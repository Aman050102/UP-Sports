# core/admin.py
from django.contrib import admin
from .models import CheckinEvent
@admin.register(CheckinEvent)
class CheckinEventAdmin(admin.ModelAdmin):
    list_display = ("occurred_at", "facility", "action", "user", "session_date")
    list_filter = ("facility", "action", "session_date")
    search_fields = ("user__username",)