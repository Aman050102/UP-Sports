# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # --- เมนูหลัก ---
    path("", views.staff_console, name="home"),           # เมนูเจ้าหน้าที่
    path("user/", views.user_menu, name="user_menu"),     # เมนูผู้ใช้งานทั่วไป (นิสิต/บุคลากร)
    path("choose/", views.choose, name="choose"),         # หน้าสำหรับเลือกสนาม

    # --- ระบบ mock login/logout ---
    path("auth/", views.mock_login, name="auth_redirect"),
    path("logout/", views.logout_view, name="logout"),

    # --- ลิงก์ใน staff console (ตอนนี้ยัง placeholder ได้) ---
    path("staff/equipment/", views.staff_equipment, name="staff_equipment"),
    path("staff/badminton-booking/", views.staff_badminton_booking, name="staff_badminton_booking"),
    path("staff/report/", views.staff_report, name="staff_report"),
    path("staff/borrow-stats/", views.staff_borrow_stats, name="staff_borrow_stats"),
    path("pool/checkout/", views.pool_checkout, name="pool_checkout_api"),

    # --- health check ---
    path("health/", views.health, name="health"),
]