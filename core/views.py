# core/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib.auth.decorators import login_required

User = get_user_model()


# ============ เมนูหลัก ============
@login_required
def staff_console(request):
    display_name = request.user.get_full_name() or request.user.username or "เจ้าหน้าที่"
    return render(request, "staff_console.html", {"display_name": display_name})


@login_required
def user_menu(request):
    display_name = request.user.get_full_name() or request.user.username or "ผู้ใช้งาน"
    return render(request, "user_menu.html", {"display_name": display_name})


# ============ Mock Login / Logout ============
def mock_login(request):
    """
    ?role=staff หรือ ?role=person
    จำลองล็อกอินด้วยอีเมล @up.ac.th แล้วเด้งไปหน้าตามบทบาท
    """
    role = request.GET.get("role", "staff")
    email = "b6500001@up.ac.th"
    user, _ = User.objects.get_or_create(
        username=email,
        defaults={"email": email, "first_name": "Student", "last_name": "One"},
    )
    login(request, user)
    return redirect("home" if role == "staff" else "user_menu")


def logout_view(request):
    logout(request)
    return redirect("auth_redirect")  # หรือ 'login' ถ้าคุณมีหน้า login แยก


# ============ Health ============
def health(request):
    return HttpResponse("OK")


# ============ Placeholders สำหรับลิงก์ใน staff_console.html ============
@login_required
def staff_equipment(request):
    return HttpResponse("หน้ายืม-คืนอุปกรณ์ (กำลังพัฒนา)")


@login_required
def staff_badminton_booking(request):
    return HttpResponse("หน้าจองสนามแบดมินตัน (กำลังพัฒนา)")


@login_required
def staff_report(request):
    return HttpResponse("หน้ารายงานการเข้าใช้สนาม (กำลังพัฒนา)")


@login_required
def staff_borrow_stats(request):
    return HttpResponse("หน้าสถิติการยืม-คืน (กำลังพัฒนา)")

@login_required
def choose(request):
    """
    หน้าเลือกประเภทสนาม เพื่อเช็คอิน
    """
    return render(request, "choose.html")



@require_POST
@login_required
def pool_checkout(request):
    # บันทึกเวลา check out ของผู้ใช้ในฐานข้อมูลผ่าน session (DB-backed)
    checked_out_at = timezone.now().isoformat()
    request.session["pool_last_checkout_at"] = checked_out_at
    request.session.modified = True
    return JsonResponse({"ok": True, "checked_out_at": checked_out_at})

