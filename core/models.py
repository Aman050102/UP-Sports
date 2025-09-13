# core/models.py
from __future__ import annotations

from django.conf import settings
from django.db import models, transaction
from django.db.models import F, CheckConstraint, Q
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone


# ------------------------------------------------------------
# Check-in / Check-out สนามกีฬา
# ------------------------------------------------------------
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
    # วันที่บันทึกตาม timezone ท้องถิ่น เพื่อสรุปรายวันได้ง่าย
    session_date = models.DateField(db_index=True, editable=False)

    class Meta:
        ordering = ("-occurred_at",)
        indexes = [
            models.Index(fields=["session_date", "facility"]),
            models.Index(fields=["facility", "occurred_at"]),
        ]

    def save(self, *args, **kwargs):
        aware_dt = (
            self.occurred_at
            if timezone.is_aware(self.occurred_at)
            else timezone.make_aware(self.occurred_at)
        )
        self.session_date = timezone.localdate(aware_dt)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.occurred_at:%Y-%m-%d %H:%M} {self.facility} {self.action}"


# ------------------------------------------------------------
# ยืม–คืนอุปกรณ์กีฬา
# ------------------------------------------------------------
class Equipment(models.Model):
    name = models.CharField(max_length=100, unique=True)
    stock = models.PositiveIntegerField(default=0)  # คงเหลือ

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class BorrowRecord(models.Model):
    ACTION_CHOICES = (("borrow", "borrow"), ("return", "return"))

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    action = models.CharField(max_length=6, choices=ACTION_CHOICES, default="borrow")
    qty = models.PositiveIntegerField(default=1)
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)
    remark = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ("-occurred_at", "-id")
        indexes = [
            models.Index(fields=["occurred_at"]),
        ]
        constraints = [
            # qty > 0
            CheckConstraint(check=Q(qty__gt=0), name="borrow_qty_gt_0"),
        ]

    def __str__(self) -> str:
        return f"{self.equipment} {self.action} x{self.qty} @ {self.occurred_at:%Y-%m-%d %H:%M}"


# ------------------------------------------------------------
# Signals: ปรับสต็อกอัตโนมัติเมื่อสร้าง/แก้ไข/ลบ BorrowRecord
# ทำให้ปลอดภัยต่อการแก้ไขรายการย้อนหลัง และป้องกัน stock ติดลบ
# ------------------------------------------------------------


def _delta_for(action: str, qty: int) -> int:
    """
    แปลง action -> ผลต่อสต็อก
    borrow  : -qty
    return  : +qty
    """
    return -qty if action == "borrow" else qty


@receiver(pre_save, sender=BorrowRecord)
def _borrowrecord_presave(sender, instance: BorrowRecord, **kwargs):
    """
    คำนวณ delta ที่ต้องปรับสต็อก แล้วเก็บไว้บน instance ก่อน save
    รองรับกรณีแก้ไข (equipment/action/qty เปลี่ยน)
    """
    # ค่าเริ่มต้น: ถือว่าเป็นเรคคอร์ดใหม่
    delta_new = _delta_for(instance.action, instance.qty)
    equip_new_id = instance.equipment_id

    delta = delta_new
    equip_id = equip_new_id

    # ถ้าเป็นการอัปเดต ให้หักล้างค่าของของเดิมด้วย
    if instance.pk:
        try:
            old = BorrowRecord.objects.get(pk=instance.pk)
            delta_old = _delta_for(old.action, old.qty)
            # ต้องย้อนกลับผลของเรคคอร์ดเดิม (จึงเป็น -delta_old)
            # แล้วบวกผลใหม่
            if old.equipment_id == equip_new_id:
                delta = (-delta_old) + delta_new
                equip_id = equip_new_id
            else:
                # อุปกรณ์เปลี่ยน → ต้องคืนของเก่า แล้วตัดสต็อกของใหม่
                instance._stock_adjust_list = [
                    (old.equipment_id, -delta_old),  # ย้อนกลับของเก่า
                    (equip_new_id, delta_new),  # ใช้ของใหม่
                ]
                return
        except BorrowRecord.DoesNotExist:
            pass

    instance._stock_adjust_list = [(equip_id, delta)]


@receiver(post_save, sender=BorrowRecord)
def _borrowrecord_postsave(sender, instance: BorrowRecord, created: bool, **kwargs):
    """
    ปรับ field stock ของ Equipment ตามรายการที่ pre_save คำนวณไว้
    ตรวจสอบไม่ให้ stock ติดลบ
    """
    adjusts = getattr(instance, "_stock_adjust_list", None)
    if not adjusts:
        return

    with transaction.atomic():
        for equip_id, delta in adjusts:
            eq = Equipment.objects.select_for_update().get(pk=equip_id)
            new_stock = eq.stock + delta
            if new_stock < 0:
                # ยกเลิกทั้งทรานแซกชัน
                raise ValueError(
                    f"สต็อก '{eq.name}' ไม่พอ (คงเหลือ {eq.stock}, ต้องการ {abs(delta)})"
                )
            # อัปเดตโดยใช้ F() เพื่อความถูกต้องใน concurrent
            Equipment.objects.filter(pk=equip_id).update(stock=F("stock") + delta)


@receiver(post_delete, sender=BorrowRecord)
def _borrowrecord_postdelete(sender, instance: BorrowRecord, **kwargs):
    """
    ลบรายการ → ย้อนกลับผลต่อสต็อก
    (ถ้าเดิมเป็น borrow ก็คืนสต็อก, ถ้าเดิมเป็น return ก็ตัดสต็อก)
    """
    delta = -_delta_for(instance.action, instance.qty)
    with transaction.atomic():
        eq = Equipment.objects.select_for_update().get(pk=instance.equipment_id)
        new_stock = eq.stock + delta
        if new_stock < 0:
            raise ValueError(
                f"ลบรายการนี้ทำให้สต็อกติดลบของ '{eq.name}' (คงเหลือ {eq.stock})"
            )
        Equipment.objects.filter(pk=instance.equipment_id).update(
            stock=F("stock") + delta
        )
