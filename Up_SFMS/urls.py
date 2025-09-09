# Up_SFMS/urls.py
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("core.urls")),   # ใช้ core เป็น root
    path("admin/", admin.site.urls),  # ถ้าไม่ใช้ ลบได้
]