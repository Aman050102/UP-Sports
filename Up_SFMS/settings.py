from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ==== DEV ONLY ====
SECRET_KEY = "dev-secret-key-change-me"  # เปลี่ยนตอน deploy
DEBUG = True
ALLOWED_HOSTS = []

# ==== Apps ====
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",  # แอปของคุณ
]

# ==== Middleware ====
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "Up_SFMS.urls"

# ==== Templates ====
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # โฟลเดอร์ templates หลัก
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "Up_SFMS.wsgi.application"
ASGI_APPLICATION = "Up_SFMS.asgi.application"

# ==== Database (SQLite สำหรับพัฒนา) ====
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ==== I18N / TZ ====
LANGUAGE_CODE = "th"
TIME_ZONE = "Asia/Bangkok"
USE_I18N = True
USE_TZ = True

# ==== Static files ====
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]  # ใช้ตอน dev
# STATIC_ROOT = BASE_DIR / "staticfiles"  # ใช้ตอน collectstatic (deploy)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
