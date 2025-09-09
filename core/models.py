from django.conf import settings
from django.db import models
from django.utils import timezone

FACILITY_CHOICES = [
    ("outdoor", "สนามกลางแจ้ง"),
    ("badminton", "สนามแบดมินตัน"),
    ("pool", "สระว่ายน้ำ"),
    ("track", "ลู่และลาน"),
]

ACTION_CHOICES = [("in", "Check-in"), ("out", "Check-out")]


class CheckinEvent(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="checkin_events",
    )
    facility = models.CharField(max_length=20, choices=FACILITY_CHOICES)
    action = models.CharField(max_length=3, choices=ACTION_CHOICES)
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)
    # วันที่ของ session (ให้รายงานกรองรายวันได้สะดวก)
    session_date = models.DateField(db_index=True, editable=False)

    class Meta:
        ordering = ("-occurred_at",)

    def save(self, *args, **kwargs):
        # ให้ session_date อิง timezone ปัจจุบันเสมอ
        aware_dt = (
            self.occurred_at
            if timezone.is_aware(self.occurred_at)
            else timezone.make_aware(self.occurred_at)
        )
        self.session_date = timezone.localdate(aware_dt)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.occurred_at:%Y-%m-%d %H:%M} {self.facility} {self.action}"
