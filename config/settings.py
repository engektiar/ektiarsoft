"""
Django settings for the Portfolio / Software-studio project.

All environment-specific values are read from environment variables
(or a local `.env` file). See `.env.example`.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# --- tiny .env loader (no extra dependency) --------------------------------
def _load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env(BASE_DIR / ".env")


def env(key, default=None):
    return os.environ.get(key, default)


def env_bool(key, default=False):
    return str(env(key, default)).lower() in {"1", "true", "yes", "on"}


def env_list(key, default=""):
    return [x.strip() for x in str(env(key, default)).split(",") if x.strip()]


# --- core ------------------------------------------------------------------
ON_VERCEL = env("VERCEL") == "1"  # Vercel sets VERCEL=1 automatically

SECRET_KEY = env("SECRET_KEY", "dev-insecure-change-me-in-production")
if ON_VERCEL and SECRET_KEY.startswith("dev-insecure"):
    raise RuntimeError("Set a SECRET_KEY environment variable in Vercel -> Settings -> Environment Variables.")
# On Vercel DEBUG is always off (a copied DEBUG=True must never expose error pages live)
DEBUG = False if ON_VERCEL else env_bool("DEBUG", True)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "")
if ON_VERCEL:
    ALLOWED_HOSTS += [".vercel.app"]
    CSRF_TRUSTED_ORIGINS += ["https://*.vercel.app"]
SITE_URL = env("SITE_URL", "http://127.0.0.1:8000").rstrip("/")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
    # local apps
    "apps.accounts",
    "apps.core",
    "apps.blog",
    "apps.dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serves static files in production
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# --- database (SQL) --------------------------------------------------------
# DB_ENGINE = sqlite | mysql | postgresql
DB_ENGINE = env("DB_ENGINE", "sqlite").lower()
if DB_ENGINE == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": env("DB_NAME", "portfolio"),
            "USER": env("DB_USER", "root"),
            "PASSWORD": env("DB_PASSWORD", ""),
            "HOST": env("DB_HOST", "127.0.0.1"),
            "PORT": env("DB_PORT", "3306"),
            "OPTIONS": {"charset": "utf8mb4", "init_command": "SET sql_mode='STRICT_TRANS_TABLES'"},
        }
    }
elif DB_ENGINE == "postgresql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME", "portfolio"),
            "USER": env("DB_USER", "postgres"),
            "PASSWORD": env("DB_PASSWORD", ""),
            "HOST": env("DB_HOST", "127.0.0.1"),
            "PORT": env("DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / f"{env('DB_NAME', 'portfolio')}.sqlite3",
        }
    }


def _db_from_url(url):
    """postgres://… (Neon), mysql://… or sqlite:///path -> Django DATABASES entry."""
    import dj_database_url

    cfg = dj_database_url.parse(url, conn_max_age=0, conn_health_checks=True)
    if cfg["ENGINE"].endswith("postgresql"):
        cfg.setdefault("OPTIONS", {}).setdefault("sslmode", "require")
    return cfg


# DATABASE_URL (e.g. from Neon) overrides DB_ENGINE — used on Vercel.
if env("DATABASE_URL"):
    DATABASES["default"] = _db_from_url(env("DATABASE_URL"))
# CLOUD_DATABASE_URL: a second connection used only by `manage.py clone_to_cloud`.
if env("CLOUD_DATABASE_URL"):
    DATABASES["cloud"] = _db_from_url(env("CLOUD_DATABASE_URL"))
if ON_VERCEL and DATABASES["default"]["ENGINE"].endswith("sqlite3"):
    raise RuntimeError("Set DATABASE_URL (your Neon connection string) in Vercel -> Environment Variables.")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- auth / RBAC -----------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    "apps.accounts.backends.RoleBackend",  # role-based permissions
]
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "core:home"
DEFAULT_USER_ROLE = env("DEFAULT_USER_ROLE", "client")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- i18n ------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = env("TIME_ZONE", "Asia/Dhaka")
USE_I18N = True
USE_TZ = True


# --- static & media --------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
# Cloudinary is used on Vercel; locally only if USE_CLOUDINARY=True (clone_to_cloud uses it directly)
USE_CLOUDINARY = bool(env("CLOUDINARY_URL")) and (ON_VERCEL or env_bool("USE_CLOUDINARY", False))
if ON_VERCEL and not USE_CLOUDINARY:
    raise RuntimeError("Set CLOUDINARY_URL in Vercel -> Environment Variables (uploads need cloud storage).")
STORAGES = {
    # uploads: Cloudinary when CLOUDINARY_URL is set, otherwise the local media/ folder
    "default": {"BACKEND": "apps.core.storage.CloudinaryStorage" if USE_CLOUDINARY
                else "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage" if (DEBUG or ON_VERCEL)
        else "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}
# On Vercel there is no collectstatic step: WhiteNoise serves files straight from the app folders.
WHITENOISE_USE_FINDERS = ON_VERCEL
WHITENOISE_AUTOREFRESH = DEBUG
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# --- email -----------------------------------------------------------------
EMAIL_BACKEND = env("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", "")
EMAIL_PORT = int(env("EMAIL_PORT", "587"))
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "noreply@example.com")


# --- production security ---------------------------------------------------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(env("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    X_FRAME_OPTIONS = "DENY"
