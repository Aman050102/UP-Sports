# core/views.py
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List
import json

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import (
    HttpRequest, HttpResponse, HttpResponseBadRequest, JsonResponse,
)
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods

from .models import CheckinEvent, BorrowRecord

User = get_user_model()

# =============================================================================
# Helpers / Session flag (สระว่ายน้ำ)
# =============================================================================
POOL_LOCK_KEY = "pool_locked"

def _lock_pool(request: HttpRequest) -> None:
    request.session[POOL_LOCK_KEY] = True
    request.session.modified = True

def _unlock_pool(request: HttpRequest) -> None:
    request.session[POOL_LOCK_KEY] = False
    request.session.modified = True

def _is_pool_locked(request: HttpRequest) -> bool:
    return bool(request.session.get(POOL_LOCK_KEY, False))

def _is_staff(user: User) -> bool:
    return bool(user and (user.is_staff or user.is_superuser))


# =============================================================================
# Login / Logout / Consoles
# =============================================================================
def login_page(request: HttpRequest) -> HttpResponse:
    return render(request, "registration/login.html")

@login_required
def staff_console(request: HttpRequest) -> HttpResponse:
    """หน้าเมนูเจ้าหน้าที่"""
    if not _is_staff(request.user):
        return HttpResponse("Forbidden", status=403)
    display_name = request.user.get_full_name() or request.user.username or "เจ้าหน้าที่"
    return render(request, "staff_console.html", {"display_name": display_name})

@login_required
def user_menu(request: HttpRequest) -> HttpResponse:
    display_name = request.user.get_full_name() or request.user.username or "ผู้ใช้งาน"
    return render(
        request, "user_menu.html",
        {"display_name": display_name, "pool_locked": _is_pool_locked(request)},
    )

def mock_login(request: HttpRequest) -> HttpResponse:
    """เดโม่ลอกอิน: /auth/?role=staff หรือ /auth/?role=user"""
    role = (request.GET.get("role") or "staff").strip()
    email = "b6500001@up.ac.th"
    user, _ = User.objects.get_or_create(
        username=email,
        defaults={"email": email, "first_name": "Student", "last_name": "One"},
    )
    # ให้สิทธิ์ staff เมื่อ role=staff (เดโม่)
    user.is_staff = (role == "staff")
    user.save(update_fields=["is_staff"])
    login(request, user)
    _unlock_pool(request)
    return redirect("staff_console" if role == "staff" else "user_menu")

def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("login")


# =============================================================================
# หน้าเลือกสนาม/เช็คอิน (ผู้ใช้)
# =============================================================================
@login_required
def choose(request: HttpRequest) -> HttpResponse:
    """หน้าเลือกสนาม: ถ้ายังล็อกจากสระให้บล็อกก่อน"""
    if _is_pool_locked(request):
        return render(
            request, "locked.html",
            {"reason": "คุณยังไม่ได้เช็คเอาต์ออกจากสระว่ายน้ำ กรุณาเช็คเอาต์ก่อนใช้งานสนามอื่น"},
            status=403,
        )
    return render(request, "choose.html")

def _create_event(request: HttpRequest, facility: str, action: str) -> CheckinEvent:
    return CheckinEvent.objects.create(
        user=request.user if request.user.is_authenticated else None,
        facility=facility,  # outdoor|badminton|pool|track
        action=action,      # in|out
        occurred_at=timezone.now(),
    )

def _get_post_param(request: HttpRequest, key: str) -> str:
    val = request.POST.get(key)
    if val is not None:
        return val
    try:
        body = json.loads(request.body or b"{}")
        return (body.get(key) or "").strip()
    except Exception:
        return ""

@require_POST
@login_required
def api_check_event(request: HttpRequest) -> JsonResponse | HttpResponseBadRequest:
    """
    POST: facility=<outdoor|badminton|pool|track>, action=<in|out>
    - ถ้า facility=pool จะควบคุม lock/unlock ใน session ให้โดยอัตโนมัติ
    - ป้องกันออกจากสระทั้งที่ยังไม่เช็คอิน
    """
    facility = (_get_post_param(request, "facility") or "").strip()
    action = (_get_post_param(request, "action") or "").strip()

    if facility not in {"outdoor", "badminton", "pool", "track"}:
        return HttpResponseBadRequest("invalid facility")
    if action not in {"in", "out"}:
        return HttpResponseBadRequest("invalid action")

    if facility == "pool":
        if action == "in":
            _lock_pool(request)
        else:  # out
            if not _is_pool_locked(request):
                return JsonResponse({"ok": False, "error": "not_checked_in", "locked": False})
            _unlock_pool(request)

    evt = _create_event(request, facility, action)
    session_date = timezone.localtime(evt.occurred_at).date().isoformat()
    return JsonResponse(
        {"ok": True, "id": evt.id, "facility": evt.facility, "action": evt.action,
         "ts": evt.occurred_at.isoformat(), "session_date": session_date}
    )

# Quick pool API (เดโม่)
@login_required
@csrf_exempt
def pool_checkin(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)
    _lock_pool(request)
    return JsonResponse({"status": "ok", "locked": True})

@login_required
@csrf_exempt
def pool_checkout(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)
    if not _is_pool_locked(request):
        return JsonResponse({"status": "noop", "locked": False, "message": "Not checked in"})
    _unlock_pool(request)
    request.session["pool_last_checkout_at"] = timezone.now().isoformat()
    request.session.modified = True
    return JsonResponse({"status": "ok", "locked": False, "message": "Checked out"})


# =============================================================================
# รายงานเช็คอิน (แสดงผล + API)
# =============================================================================
@login_required
def checkin_report(request: HttpRequest) -> HttpResponse:
    return render(request, "checkin_report.html")

@login_required
def api_checkins(request: HttpRequest) -> JsonResponse:
    """
    GET: from=YYYY-MM-DD, to=YYYY-MM-DD, facility=outdoor|badminton|pool|track (ว่าง = ทั้งหมด)
    """
    date_from_str = (request.GET.get("from") or "").strip()
    date_to_str = (request.GET.get("to") or "").strip()
    facility = (request.GET.get("facility") or "").strip()

    today = timezone.localdate()
    try:
        date_from = (
            timezone.datetime.fromisoformat(date_from_str).date()
            if date_from_str else today
        )
    except Exception:
        date_from = today
    try:
        date_to = (
            timezone.datetime.fromisoformat(date_to_str).date()
            if date_to_str else today
        )
    except Exception:
        date_to = today

    qs = CheckinEvent.objects.all()
    if facility in {"outdoor", "badminton", "pool", "track"}:
        qs = qs.filter(facility=facility)

    start_dt = timezone.make_aware(
        timezone.datetime.combine(date_from, timezone.datetime.min.time())
    )
    end_dt = timezone.make_aware(
        timezone.datetime.combine(date_to, timezone.datetime.max.time())
    )
    qs = qs.filter(occurred_at__range=(start_dt, end_dt)).order_by("occurred_at")

    rows: List[Dict[str, Any]] = []
    for evt in qs:
        local_dt = timezone.localtime(evt.occurred_at)
        rows.append(
            {
                "ts": evt.occurred_at.isoformat(),
                "session_date": local_dt.date().isoformat(),
                "facility": evt.facility,
                "action": evt.action,
            }
        )
    return JsonResponse(rows, safe=False)


# =============================================================================
# ยืม–คืนอุปกรณ์ (หน้า + API + สถิติ)
# =============================================================================
@login_required
def user_equipment(request: HttpRequest) -> HttpResponse:
    return render(request, "user_equipment.html")

@login_required
def staff_equipment(request: HttpRequest) -> HttpResponse:
    if not _is_staff(request.user):
        return HttpResponse("Forbidden", status=403)
    return render(request, "staff_equipment.html")

@login_required
@require_http_methods(["POST"])
def api_borrow_return(request: HttpRequest) -> JsonResponse:
    """POST JSON: { "action": "borrow"|"return", "equipment": "<ชื่อ>", "qty": <int> }"""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)

    action = (payload.get("action") or "").strip()
    name = (payload.get("equipment") or "").strip()
    try:
        qty = int(payload.get("qty") or 1)
    except Exception:
        qty = 1

    if action not in {"borrow", "return"}:
        return JsonResponse({"ok": False, "error": "invalid_action"}, status=400)
    if not name:
        return JsonResponse({"ok": False, "error": "equipment_required"}, status=400)
    if qty < 1:
        return JsonResponse({"ok": False, "error": "qty_invalid"}, status=400)

    eq_obj = None
    try:
        from .models import Equipment
        eq_obj, _ = Equipment.objects.get_or_create(name=name)
    except Exception:
        pass

    rec = BorrowRecord.objects.create(
        equipment=eq_obj, qty=qty, action=action, occurred_at=timezone.now(),
    )
    return JsonResponse({"ok": True, "id": rec.id, "action": action, "equipment": name, "qty": qty})

# แบบฟอร์มเดโม่ (optional)
@login_required
def borrow_form(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        equipment_name = (request.POST.get("equipment") or "").strip()
        user_name = (request.POST.get("user_name") or "").strip()
        try:
            qty = int(request.POST.get("qty") or "1")
        except ValueError:
            qty = 1

        if not equipment_name:
            messages.error(request, "กรุณาระบุชื่ออุปกรณ์")
            return render(request, "borrow_form.html")
        if qty < 1:
            messages.error(request, "จำนวนต้องมากกว่า 0")
            return render(request, "borrow_form.html")

        eq_obj = None
        try:
            from .models import Equipment
            eq_obj, _ = Equipment.objects.get_or_create(name=equipment_name)
        except Exception:
            pass

        BorrowRecord.objects.create(
            equipment=eq_obj, qty=qty, action="borrow", occurred_at=timezone.now()
        )
        show_name = user_name or "guest"
        messages.success(request, f"บันทึกการยืม {equipment_name} จำนวน {qty} รายการแล้ว ({show_name})")
        return redirect("borrow_form")

    return render(request, "borrow_form.html")


# --- สถิติการยืม-คืน ---
def _parse_date(s: str | None) -> date:
    if not s:
        return timezone.localdate()
    try:
        return date.fromisoformat(s)
    except Exception:
        return timezone.localdate()

@login_required
def user_borrow_stats(request: HttpRequest) -> HttpResponse:
    today = timezone.localdate().isoformat()
    return render(
        request, "borrow_stats.html",
        {"today": today, "can_export": False,
         "display_name": request.user.get_full_name() or request.user.username or "ผู้ใช้งาน"},
    )

@login_required
def staff_borrow_stats(request: HttpRequest) -> HttpResponse:
    if not _is_staff(request.user):
        return HttpResponse("Forbidden", status=403)
    today = timezone.localdate().isoformat()
    return render(
        request, "staff_borrow_stats.html",
        {"today": today, "can_export": True,
         "display_name": request.user.get_full_name() or request.user.username or "เจ้าหน้าที่"},
    )

@login_required
def api_borrow_stats(request: HttpRequest) -> JsonResponse:
    dfrom = _parse_date(request.GET.get("from"))
    dto = _parse_date(request.GET.get("to"))
    action = (request.GET.get("action") or "borrow").strip()

    qs = BorrowRecord.objects.all().filter(occurred_at__date__range=(dfrom, dto))
    if action in {"borrow", "return"}:
        qs = qs.filter(action=action)

    rows_qs = qs.values("equipment__name").annotate(qty=Sum("qty")).order_by("-qty")
    rows: List[Dict[str, Any]] = [
        {"equipment": r["equipment__name"] or "ไม่ระบุ", "qty": r["qty"] or 0}
        for r in rows_qs
    ]
    total = sum(r["qty"] for r in rows)
    return JsonResponse(
        {"from": dfrom.isoformat(), "to": dto.isoformat(),
         "action": action, "rows": rows, "total": total}
    )

@staff_member_required
def export_borrow_stats_csv(request: HttpRequest) -> HttpResponse:
    api_resp: JsonResponse = api_borrow_stats(request)
    data = json.loads(api_resp.content.decode("utf-8"))

    import csv
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="borrow-stats.csv"'
    w = csv.writer(resp)
    w.writerow(["ช่วงวันที่", f'{data["from"]} - {data["to"]}'])
    w.writerow(["ประเภท", "ยืม" if data["action"] == "borrow" else "คืน"])
    w.writerow([])
    w.writerow(["ลำดับ", "รายการ", "จำนวนครั้ง"])
    for i, r in enumerate(data["rows"], start=1):
        w.writerow([i, r["equipment"], r["qty"]])
    w.writerow([])
    w.writerow(["รวมทั้งหมด", "", data["total"]])
    return resp


# =============================================================================
# จองสนามแบดมินตัน
# =============================================================================
@login_required
def badminton_booking(request: HttpRequest) -> HttpResponse:
    return HttpResponse("หน้าจองสนามแบดมินตัน (ผู้ใช้) – กำลังพัฒนา")

@login_required
def staff_badminton_booking(request: HttpRequest) -> HttpResponse:
    if not _is_staff(request.user):
        return HttpResponse("Forbidden", status=403)
    return HttpResponse("หน้าจองสนามแบดมินตัน (เจ้าหน้าที่) – กำลังพัฒนา")


# =============================================================================
# Health
# =============================================================================
def health(request: HttpRequest) -> HttpResponse:
    return HttpResponse("OK")