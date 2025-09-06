import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

INSTALLED_APPS = [
    # ...
    "django.contrib.staticfiles",
    "core",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],   # โฟลเดอร์ templates หลัก
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ]},
    },
]

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]     # สำหรับไฟล์ front-end ในโปรเจกต์
# STATIC_ROOT = BASE_DIR / "staticfiles"     # ใช้ตอน collectstatic (deploy)