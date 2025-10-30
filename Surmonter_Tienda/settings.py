from pathlib import Path
import os
from django.contrib.messages import constants as messages
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# ✅ CONFIGURACIÓN PRODUCCIÓN
DEBUG = False
DJANGO_ENV = 'production'

# Configuración del sitio
SITE_NAME = "Surmonter Tienda"
EMAIL_CONTACTO = "surmonterestampados@gmail.com"
TELEFONO_CONTACTO = "+56 9 5665 2265"

# ✅ CONFIGURACIÓN DOMINIO PRODUCCIÓN
SITE_URL = 'https://surmontertienda.cl'
ALLOWED_HOSTS = [
    'surmontertienda.cl',
    'www.surmontertienda.cl',
    '3.144.5.198',
]

CSRF_TRUSTED_ORIGINS = [
    'https://surmontertienda.cl',
    'https://www.surmontertienda.cl',
]

# ✅ SEGURIDAD PRODUCCIÓN
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# ✅ LOGS DE CONFIGURACIÓN
print("=" * 50)
print(f"🚀 ENTORNO: PRODUCCIÓN")
print(f"🔧 DEBUG: {DEBUG}")
print(f"🌐 SITE_URL: {SITE_URL}")
print("=" * 50)

MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

# ======================
# CONFIGURACIÓN DE EMAIL PRODUCCIÓN
# ======================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'surmonterestampados@gmail.com'
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')
DEFAULT_FROM_EMAIL = 'surmonterestampados@gmail.com'
SERVER_EMAIL = 'surmonterestampados@gmail.com'
print("📧 MODO PRODUCCIÓN: Emails se envían por SMTP")

# ✅ CONFIGURACIÓN MERCADOPAGO PRODUCCIÓN
MERCADOPAGO_TOKEN_SANDBOX = os.environ.get("MP_TOKEN_SANDBOX")
MERCADOPAGO_TOKEN_PRODUCCION = os.environ.get("MP_TOKEN_PRODUCCION")
MERCADOPAGO_PUBLIC_KEY_SANDBOX = os.environ.get("MP_PUBLIC_KEY_SANDBOX")
MERCADOPAGO_PUBLIC_KEY_PRODUCCION = os.environ.get("MP_PUBLIC_KEY_PRODUCCION")

# FORZAR PRODUCCIÓN
MERCADOPAGO_USAR_PRODUCCION = True
print("💰 MercadoPago: MODO PRODUCCIÓN (Ventas Reales)")

if MERCADOPAGO_USAR_PRODUCCION:
    if not MERCADOPAGO_TOKEN_PRODUCCION:
        print("❌ ERROR CRÍTICO: MP_TOKEN_PRODUCCION no configurado")
        raise Exception("Token de MercadoPago producción no configurado")
    else:
        MERCADOPAGO_ACCESS_TOKEN = MERCADOPAGO_TOKEN_PRODUCCION
        MERCADOPAGO_PUBLIC_KEY = MERCADOPAGO_PUBLIC_KEY_PRODUCCION
        print(f"🔑 MercadoPago Token Producción: {MERCADOPAGO_ACCESS_TOKEN[:20]}...")

# APLICACIONES
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'carroApp',
    'categoriasApp',
    'inicioApp',
    'pagoApp',
    'adminpanelApp',
    'ingresarApp',
    'mostrarApp',
    'userApp',
    'django.contrib.humanize',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Surmonter_Tienda.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'builtins': [
                'django.contrib.humanize.templatetags.humanize',
            ],
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'categoriasApp.context_processors.menu_categorias',
                'carroApp.context_processors.carrito_total',
                'ingresarApp.context_processors.get_carrito_total_items',
                'Surmonter_Tienda.context_processors.mercadopago_config',
            ],
        },
    },
]

WSGI_APPLICATION = 'Surmonter_Tienda.wsgi.application'

# BASE DE DATOS PRODUCCIÓN
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'surmonterdb'),
        'USER': os.environ.get('DB_USER', 'surmonteruser'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'S@urmonter2024!'),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '3306'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# Static & Media settings
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CACHE PRODUCCIÓN
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_cache_surmonter',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}