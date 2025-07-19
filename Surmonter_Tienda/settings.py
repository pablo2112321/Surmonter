from pathlib import Path
import os
from django.contrib.messages import constants as messages
# Si no usarás dotenv, puedes comentar o borrar esta línea
#from dotenv import load_dotenv
#load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-vhcwovj7s$2!%+o3w#u3xfd=z6zd%c(mf&5tdcs=sdv((e&hmo'

DEBUG = False  # En producción siempre False

ALLOWED_HOSTS = [
    'surmontertienda.cl',
    'www.surmontertienda.cl',
    '3.144.5.198',      # Tu IP pública del servidor
    'localhost',
]

CSRF_TRUSTED_ORIGINS = [
    'https://surmontertienda.cl',
    'https://www.surmontertienda.cl',
    'http://3.144.5.198',
]

MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

MERCADOPAGO_TOKEN_SANDBOX = "TEST-7920081371925564-031811-21c0365417ecf513ce563a59b54e11f7-1934968664"
MERCADOPAGO_TOKEN_PRODUCCION = "APP_USR-7920081371925564-031811-5574349ce597ae69e1e71e53a4a069be-1934968664"
MERCADOPAGO_USAR_PRODUCCION = True

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
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Para servir static en producción
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
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'categoriasApp.context_processors.menu_categorias',
                'carroApp.context_processors.carrito_total',
                'ingresarApp.context_processors.get_carrito_total_items',
            ],
        },
    },
]

WSGI_APPLICATION = 'Surmonter_Tienda.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'surmonterdb',
        'USER': 'surmonteruser',
        'PASSWORD': 'S@urmonter2024!',
        'HOST': '127.0.0.1',
        'PORT': '3306',
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
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Carpeta donde collectstatic juntará todos los estáticos

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
