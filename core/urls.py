# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ----- Auth -----
    path("", views.login_page, name="login"),
    path("login/", views.login_page, name="login_alias"),
    path("auth/", views.mock_login, name="auth_redirect"),
    path("logout/", views.logout_view, name="logout"),

    # ----- Admin / Staff -----
    path("staff/", views.staff_console, name="staff_console"),
    path("staff/equipment/", views.staff_equipment, name="staff_equipment"),
    path("staff/borrow-stats/", views.staff_borrow_stats, name="staff_borrow_stats"),
    path("staff/badminton/", views.staff_badminton_booking, name="staff_badminton_booking"),

    # ----- User -----
    path("user/", views.user_menu, name="user_menu"),
    path("choose/", views.choose, name="choose"),
    path("user/equipment/", views.user_equipment, name="user_equipment"),
    path("user/equipment/return/", views.equipment_return_page, name="user_equipment_return"),
    path("badminton/", views.badminton_booking, name="badminton_booking"),
    path("user/borrow-stats/", views.user_borrow_stats, name="user_borrow_stats"),

    # ----- Reports / APIs -----
    path("staff/report/", views.checkin_report, name="checkin_report"),
    path("api/checkins/", views.api_checkins, name="api_checkins"),
    path("api/check-event/", views.api_check_event, name="api_check_event"),
    path("pool/checkin/", views.pool_checkin, name="pool_checkin_api"),
    path("pool/checkout/", views.pool_checkout, name="pool_checkout_api"),
    path("api/borrow-return/", views.api_borrow_return, name="api_borrow_return"),
    path("api/borrow-stats/", views.api_borrow_stats, name="api_borrow_stats"),
    path("export/borrow-stats.csv", views.export_borrow_stats_csv, name="export_borrow_stats_csv"),

    # ----- Equipment API (ยืม/คืนแบบอัปเดตสต็อกทันที) -----
    path("api/equipment/borrow/", views.equip_borrow_api, name="equip_borrow_api"),
    path("api/equipment/return/", views.equip_return_api, name="equip_return_api"),

    # ----- Health -----
    path("health/", views.health, name="health"),
]