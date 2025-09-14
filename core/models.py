# core/models.py
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class Equipment(models.Model):
    name = models.CharField(max_length=255, unique=True)
    total = models.PositiveIntegerField(default=0)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return self.name


class BorrowRecord(models.Model):
    ACTIONS = (
        ("borrow", "Borrow"),
        ("return", "Return"),
    )
    equipment = models.ForeignKey(
        Equipment, null=True, blank=True, on_delete=models.SET_NULL, related_name="records"
    )
    qty = models.PositiveIntegerField(default=1)
    action = models.CharField(max_length=10, choices=ACTIONS)
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)

    def __str__(self) -> str:
        eq = self.equipment.name if self.equipment else "N/A"
        return f"{self.action} {eq} x{self.qty} @ {self.occurred_at:%Y-%m-%d %H:%M}"


class CheckinEvent(models.Model):
    FACILITIES = (
        ("outdoor", "Outdoor"),
        ("badminton", "Badminton"),
        ("pool", "Pool"),
        ("track", "Track"),
    )
    ACTIONS = (
        ("in", "In"),
        ("out", "Out"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    facility = models.CharField(max_length=20, choices=FACILITIES)
    action = models.CharField(max_length=5, choices=ACTIONS)
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)

    def __str__(self) -> str:
        u = self.user.get_username() if self.user else "anon"
        return f"{u} {self.facility} {self.action} @ {self.occurred_at:%Y-%m-%d %H:%M}"