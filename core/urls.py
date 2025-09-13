# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ----- Auth -----
    path("", views.login_page, name="login"),                 # หน้าแรก = login (หลัก)
    path("login/", views.login_page, name="login_alias"),     # alias กัน 404 จากบุ๊คมาร์กเก่า

    path("auth/", views.mock_login, name="auth_redirect"),
    path("logout/", views.logout_view, name="logout"),

    # ----- Consoles -----
    path("staff/", views.staff_console, name="staff_console"),
    path("user/", views.user_menu, name="user_menu"),
    path("choose/", views.choose, name="choose"),

    # ----- Reports (Check-in) -----
    path("staff/report/", views.checkin_report, name="checkin_report"),
    path("api/checkins/", views.api_checkins, name="api_checkins"),         # มี / ปิดท้าย
    path("api/check-event/", views.api_check_event, name="api_check_event"),# มี / ปิดท้าย

    # ----- Pool -----
    path("pool/checkin/", views.pool_checkin, name="pool_checkin_api"),
    path("pool/checkout/", views.pool_checkout, name="pool_checkout_api"),

    # ----- Equipment & Badminton -----
    path("staff/equipment/", views.staff_equipment, name="staff_equipment"),
    path("staff/badminton-booking/", views.staff_badminton_booking, name="staff_badminton_booking"),

    # ----- Borrow stats (staff) -----
    path("staff/borrow-stats/", views.staff_borrow_stats, name="staff_borrow_stats"),
    path("api/borrow-stats/", views.api_borrow_stats, name="api_borrow_stats"),   # มี / ปิดท้าย
    path("export/borrow-stats.csv", views.export_borrow_stats_csv, name="export_borrow_stats_csv"),

    # ----- Health -----
    path("health/", views.health, name="health"),

    # ----- Aliases for user menu -----
    path("borrow-stats/", views.staff_borrow_stats, name="borrow_stats"),
    path("badminton-booking/", views.staff_badminton_booking, name="badminton_booking"),
]