from django.urls import path
from . import views

urlpatterns = [
    path("", views.staff_console, name="staff_console"),

    path("staff/equipment/", views.equipment_view, name="staff_equipment"),
    path("staff/badminton-booking/", views.badminton_booking_view, name="staff_badminton_booking"),
    path("staff/report/", views.report_view, name="staff_report"),
    path("staff/borrow-stats/", views.borrow_stats_view, name="staff_borrow_stats"),
]