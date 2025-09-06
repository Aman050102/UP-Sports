from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),  # หน้าหลัก + เมนู
    path(
        "accounts/", include("django.contrib.auth.urls")
    ),  # login/logout (มีชื่อ 'logout' ให้)
]
