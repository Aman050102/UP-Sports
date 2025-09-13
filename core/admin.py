# core/admin.py
from django.contrib import admin
from .models import Equipment, BorrowRecord, CheckinEvent


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ("name", "stock")
    search_fields = ("name",)


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ("occurred_at", "equipment", "action", "qty", "user")
    list_filter = ("action", "equipment")
    search_fields = ("equipment__name", "user__username")


@admin.register(CheckinEvent)
class CheckinEventAdmin(admin.ModelAdmin):
    list_display = ("occurred_at", "facility", "action", "user", "session_date")
    list_filter = ("facility", "action", "session_date")
    search_fields = ("user__username",)
