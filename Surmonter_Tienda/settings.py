from pathlib import Path
import os
from django.contrib.messages import constants as messages
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

DEBUG = False  # En producción siempre False

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'surmontertienda.cl',
    'www.surmontertienda.cl',
    '3.144.5.198',
]


CSRF_TRUSTED_ORIGINS = [
    'https://surmontertienda.cl',
    'https://www.surmontertienda.cl',
    'http://3.144.5.198',
]

MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

MERCADOPAGO_TOKEN_SANDBOX = os.environ.get('MP_TOKEN_SANDBOX')
MERCADOPAGO_TOKEN_PRODUCCION = os.environ.get('MP_TOKEN_PRODUCCION')
MERCADOPAGO_USAR_PRODUCCION = os.environ.get('MP_USAR_PRODUCCION', 'True') == 'True'


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
    #'whitenoise.middleware.WhiteNoiseMiddleware',  # Para servir static en producción
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
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
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
STATICFILES_DIRS = [BASE_DIR / 'static']  # Para tus propios archivos en desarrollo
STATIC_ROOT = BASE_DIR / 'staticfiles'    # Donde se recopilan en producción

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
