# core/views.py
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List

from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    JsonResponse,
)
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import CheckinEvent, BorrowRecord  # ใช้โมเดลจริง

User = get_user_model()

# =============================================================================
# Session flag สำหรับกฎสระว่ายน้ำ (ห้ามใช้สนามอื่นถ้ายังไม่ checkout)
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


# =============================================================================
# หน้า Login (เป็นหน้าแรกเสมอ)
# =============================================================================
def login_page(request: HttpRequest) -> HttpResponse:
    # เทมเพลต: PROJECT_ROOT/templates/registration/login.html
    return render(request, "registration/login.html")


# =============================================================================
# เมนูหลัก (ต้องล็อกอินเสมอ)
# =============================================================================
@login_required
def staff_console(request: HttpRequest) -> HttpResponse:
    display_name = request.user.get_full_name() or request.user.username or "เจ้าหน้าที่"
    return render(request, "staff_console.html", {"display_name": display_name})

# ส่ง pool_locked ไป template เพื่อให้ฝั่ง JS รู้สถานะ (data-pool-locked)
@login_required
def user_menu(request: HttpRequest) -> HttpResponse:
    display_name = request.user.get_full_name() or request.user.username or "ผู้ใช้งาน"
    return render(
        request,
        "user_menu.html",
        {
            "display_name": display_name,
            "pool_locked": _is_pool_locked(request),
        },
    )


@login_required
def choose(request: HttpRequest) -> HttpResponse:
    """หน้าเลือกสนาม: ถ้ายังล็อกจากสระให้บล็อกก่อน"""
    if _is_pool_locked(request):
        return render(
            request,
            "locked.html",
            {
                "reason": "คุณยังไม่ได้เช็คเอาต์ออกจากสระว่ายน้ำ กรุณาเช็คเอาต์ก่อนใช้งานสนามอื่น",
            },
            status=403,
        )
    return render(request, "choose.html")


# =============================================================================
# Mock Login / Logout
# =============================================================================
def mock_login(request: HttpRequest) -> HttpResponse:
    role = request.GET.get("role", "staff")
    email = "b6500001@up.ac.th"

    user, _ = User.objects.get_or_create(
        username=email,
        defaults={"email": email, "first_name": "Student", "last_name": "One"},
    )
    login(request, user)
    _unlock_pool(request)  # เคลียร์สถานะล็อกสระเมื่อเริ่มเซสชันใหม่

    return redirect("staff_console" if role == "staff" else "user_menu")


def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("login")


# =============================================================================
# เดโมสระว่ายน้ำ (เฉพาะสระ)
# =============================================================================
@login_required
@csrf_exempt  # ถ้าจะเปิดใช้ CSRF จริง ให้ถอดบรรทัดนี้ แล้วส่ง csrftoken จาก JS
def pool_checkin(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Invalid method"}, status=405
        )
    _lock_pool(request)
    return JsonResponse({"status": "ok", "locked": True})


@login_required
@csrf_exempt
def pool_checkout(request: HttpRequest) -> JsonResponse:
    """
    POST เท่านั้น:
    - ถ้ายังไม่ได้เช็คอินสระ => no-op (status="noop")
    - ถ้าเช็คอินอยู่ => ปลดล็อกและตอบ ok
    """
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Invalid method"}, status=405
        )

    if not _is_pool_locked(request):
        return JsonResponse(
            {"status": "noop", "locked": False, "message": "Not checked in"}
        )

    _unlock_pool(request)
    request.session["pool_last_checkout_at"] = timezone.now().isoformat()
    request.session.modified = True
    return JsonResponse({"status": "ok", "locked": False, "message": "Checked out"})


# =============================================================================
# เช็คอิน/เช็คเอาต์ทุกสนาม
# =============================================================================
def _create_event(request: HttpRequest, facility: str, action: str) -> CheckinEvent:
    """บันทึกเหตุการณ์เข้า/ออกลงฐานข้อมูล"""
    return CheckinEvent.objects.create(
        user=request.user if request.user.is_authenticated else None,
        facility=facility,  # "outdoor" | "badminton" | "pool" | "track"
        action=action,  # "in" | "out"
        occurred_at=timezone.now(),
    )


def _get_post_param(request: HttpRequest, key: str) -> str:
    """อ่านค่าจาก POST (รองรับ form & JSON แบบง่าย)"""
    val = request.POST.get(key)
    if val is not None:
        return val
    try:
        import json
        body = json.loads(request.body or b"{}")
        return (body.get(key) or "").strip()
    except Exception:
        return ""


@require_POST
@login_required
def api_check_event(request: HttpRequest) -> JsonResponse | HttpResponseBadRequest:
    """
    POST: facility=<outdoor|badminton|pool|track>, action=<in|out>
    - ถ้า facility=pool จะควบคุมสถานะ lock/unlock ใน session ให้โดยอัตโนมัติ
    - กันกรณีออกจากสระทั้งที่ยังไม่เช็คอิน
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
        else:  # action == "out"
            if not _is_pool_locked(request):
                return JsonResponse({"ok": False, "error": "not_checked_in", "locked": False})
            _unlock_pool(request)

    evt = _create_event(request, facility, action)
    session_date = timezone.localtime(evt.occurred_at).date().isoformat()

    return JsonResponse(
        {
            "ok": True,
            "id": evt.id,
            "facility": evt.facility,
            "action": evt.action,
            "ts": evt.occurred_at.isoformat(),
            "session_date": session_date,
        }
    )


# =============================================================================
# รีพอร์ตเช็คอิน
# =============================================================================
@login_required
def checkin_report(request: HttpRequest) -> HttpResponse:
    return render(request, "checkin_report.html")


@login_required
def staff_report(request: HttpRequest) -> HttpResponse:
    return redirect("checkin_report")


@login_required
def api_checkins(request: HttpRequest) -> JsonResponse:
    """
    GET:
      - from=YYYY-MM-DD
      - to=YYYY-MM-DD
      - facility=outdoor|badminton|pool|track (ว่าง = ทั้งหมด)
    """
    date_from_str = (request.GET.get("from") or "").strip()
    date_to_str = (request.GET.get("to") or "").strip()
    facility = (request.GET.get("facility") or "").strip()

    today = timezone.localdate()
    try:
        date_from = (
            timezone.datetime.fromisoformat(date_from_str).date()
            if date_from_str
            else today
        )
    except Exception:
        date_from = today
    try:
        date_to = (
            timezone.datetime.fromisoformat(date_to_str).date()
            if date_to_str
            else today
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
# สถิติการยืม–คืนอุปกรณ์กีฬา (หน้า + API + Export)
# =============================================================================
def _parse_date(s: str | None) -> date:
    if not s:
        return timezone.localdate()
    try:
        return date.fromisoformat(s)
    except Exception:
        return timezone.localdate()


@login_required
def staff_borrow_stats(request: HttpRequest) -> HttpResponse:
    """หน้า UI สถิติการยืม-คืน (กราฟ+ตาราง+ปุ่มดาวน์โหลด)"""
    today = timezone.localdate().isoformat()
    return render(request, "staff_borrow_stats.html", {"today": today})


@login_required
def api_borrow_stats(request: HttpRequest) -> JsonResponse:
    """
    GET /api/borrow-stats?from=YYYY-MM-DD&to=YYYY-MM-DD&action=borrow|return
    Response:
      {
        "from": "...", "to": "...",
        "action": "borrow",
        "rows": [{"equipment": "แบดมินตัน","qty": 355}, ...],
        "total": 510
      }
    """
    dfrom = _parse_date(request.GET.get("from"))
    dto = _parse_date(request.GET.get("to"))
    action = (request.GET.get("action") or "borrow").strip()

    qs = BorrowRecord.objects.all()

    # กรองช่วงวันที่ (อิง occurred_at)
    qs = qs.filter(occurred_at__date__range=(dfrom, dto))

    # กรอง action ถ้ามีค่า valid
    if action in {"borrow", "return"}:
        qs = qs.filter(action=action)

    rows_qs = qs.values("equipment__name").annotate(qty=Sum("qty")).order_by("-qty")
    rows: List[Dict[str, Any]] = [
        {"equipment": r["equipment__name"] or "ไม่ระบุ", "qty": r["qty"] or 0}
        for r in rows_qs
    ]

    total = sum(r["qty"] for r in rows)
    return JsonResponse(
        {
            "from": dfrom.isoformat(),
            "to": dto.isoformat(),
            "action": action,
            "rows": rows,
            "total": total,
        }
    )


@login_required
def export_borrow_stats_csv(request: HttpRequest) -> HttpResponse:
    """ดาวน์โหลดผลสถิติเป็น CSV (เปิดได้ด้วย Excel)"""
    # reuse ข้อมูลจาก api_borrow_stats แบบเรียกภายใน
    api_resp: JsonResponse = api_borrow_stats(request)

    import json, csv

    data = json.loads(api_resp.content.decode("utf-8"))

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
# Placeholder อื่น ๆ (กัน error จาก urls ที่อ้างถึง)
# =============================================================================
@login_required
def staff_equipment(request: HttpRequest) -> HttpResponse:
    return HttpResponse("หน้ายืม-คืนอุปกรณ์ (กำลังพัฒนา)")


@login_required
def staff_badminton_booking(request: HttpRequest) -> HttpResponse:
    return HttpResponse("หน้าจองสนามแบดมินตัน (กำลังพัฒนา)")


def health(request: HttpRequest) -> HttpResponse:
    return HttpResponse("OK")