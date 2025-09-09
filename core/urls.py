# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # หน้าแรก & หน้า login → แสดงหน้า login เสมอ
    path("", views.login_page, name="login"),
    path("login/", views.login_page, name="login"),
    path("login", views.login_page, name="login"),

    # mock login / logout
    path("auth/", views.mock_login, name="auth_redirect"),
    path("logout/", views.logout_view, name="logout"),

    # เมนูที่ต้องล็อกอิน
    path("staff/", views.staff_console, name="staff_console"),
    path("user/", views.user_menu, name="user_menu"),
    path("choose/", views.choose, name="choose"),

    # รายงาน + API
    path("staff/report/", views.checkin_report, name="checkin_report"),
    path("api/checkins", views.api_checkins, name="api_checkins"),
    path("api/check-event/", views.api_check_event, name="api_check_event"),

    # สระ
    path("pool/checkin/", views.pool_checkin, name="pool_checkin_api"),
    path("pool/checkout/", views.pool_checkout, name="pool_checkout_api"),

    # อื่น ๆ
    path("staff/equipment/", views.staff_equipment, name="staff_equipment"),
    path("staff/badminton-booking/", views.staff_badminton_booking, name="staff_badminton_booking"),
    path("staff/borrow-stats/", views.staff_borrow_stats, name="staff_borrow_stats"),

    path("health/", views.health, name="health"),
]