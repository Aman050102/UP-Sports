# core/views.py
from __future__ import annotations

from typing import Any, Dict, List

from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
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

from .models import CheckinEvent

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
# หน้า Login (เป็นหน้าแรกเสมอ) — เทมเพลตอยู่นอกแอป core
# =============================================================================
def login_page(request: HttpRequest) -> HttpResponse:
    # เทมเพลต: PROJECT_ROOT/templates/registration/login.html
    return render(request, "registration/login.html")


# =============================================================================
# เมนูหลัก (ต้องล็อกอินเสมอ)
# =============================================================================
@login_required
def staff_console(request: HttpRequest) -> HttpResponse:
    display_name = (
        request.user.get_full_name() or request.user.username or "เจ้าหน้าที่"
    )
    return render(request, "staff_console.html", {"display_name": display_name})


@login_required
def user_menu(request: HttpRequest) -> HttpResponse:
    display_name = request.user.get_full_name() or request.user.username or "ผู้ใช้งาน"
    return render(request, "user_menu.html", {"display_name": display_name})


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
#   /auth/?role=staff  -> เมนูสตาฟ
#   /auth/?role=user   -> เมนูผู้ใช้
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
# เดโมสระว่ายน้ำ (เฉพาะสระ) — ไว้ทดสอบ UI
# =============================================================================
@login_required
@csrf_exempt  # ถ้าจะเปิดใช้ CSRF จริง ถอดบรรทัดนี้ และส่ง csrftoken จากฝั่ง JS
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
    _unlock_pool(request)
    request.session["pool_last_checkout_at"] = timezone.now().isoformat()
    request.session.modified = True
    return JsonResponse({"status": "ok", "locked": False, "message": "Checked out"})


# =============================================================================
# บันทึกเหตุการณ์เข้า/ออก (ทุกสนาม) — ใช้จาก choose.html
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
    Endpoint กลางสำหรับบันทึกเช็คอิน/เช็คเอาต์
    POST: facility=<outdoor|badminton|pool|track>, action=<in|out>
    - ถ้า facility=pool จะควบคุมสถานะ lock/unlock ใน session ให้โดยอัตโนมัติ
    """
    facility = (_get_post_param(request, "facility") or "").strip()
    action = (_get_post_param(request, "action") or "").strip()

    if facility not in {"outdoor", "badminton", "pool", "track"}:
        return HttpResponseBadRequest("invalid facility")
    if action not in {"in", "out"}:
        return HttpResponseBadRequest("invalid action")

    if facility == "pool":
        _lock_pool(request) if action == "in" else _unlock_pool(request)

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
# หน้ารีพอร์ต + API ข้อมูลสำหรับกราฟ/ตาราง
# =============================================================================
@login_required
def checkin_report(request: HttpRequest) -> HttpResponse:
    return render(request, "checkin_report.html")


@login_required
def staff_report(request: HttpRequest) -> HttpResponse:
    # เผื่อมีลิงก์เก่าเรียกชื่อเดิม — redirect มาหน้าใหม่
    return redirect("checkin_report")


@login_required
def api_checkins(request: HttpRequest) -> JsonResponse:
    """
    ดึงเหตุการณ์จากฐานข้อมูลตามช่วงวันที่และ (ถ้ามี) ประเภทสนาม
    Query:
      - from=YYYY-MM-DD
      - to=YYYY-MM-DD
      - facility=outdoor|badminton|pool|track (ว่าง = ทั้งหมด)
    Response (list of rows): { ts, session_date, facility, action }
    """
    date_from_str = (request.GET.get("from") or "").strip()
    date_to_str = (request.GET.get("to") or "").strip()
    facility = (request.GET.get("facility") or "").strip()

    today = timezone.localdate()
    try:
        date_from = (
            timezone.datetime.fromisoformat(date_from_str).date() if date_from_str else today
        )
    except Exception:
        date_from = today
    try:
        date_to = (
            timezone.datetime.fromisoformat(date_to_str).date() if date_to_str else today
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
# Placeholder อื่น ๆ
# =============================================================================
@login_required
def staff_equipment(request: HttpRequest) -> HttpResponse:
    return HttpResponse("หน้ายืม-คืนอุปกรณ์ (กำลังพัฒนา)")


@login_required
def staff_badminton_booking(request: HttpRequest) -> HttpResponse:
    return HttpResponse("หน้าจองสนามแบดมินตัน (กำลังพัฒนา)")


@login_required
def staff_borrow_stats(request: HttpRequest) -> HttpResponse:
    return HttpResponse("หน้าสถิติการยืม-คืน (กำลังพัฒนา)")


def health(request: HttpRequest) -> HttpResponse:
    return HttpResponse("OK")