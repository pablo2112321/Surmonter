from django.urls import path
from .views import paneladmin

urlpatterns = [
    path('paneladmin/', paneladmin, name='panel_admin'),  # Sin slash final
    path('paneladmin/<str:accion>/', paneladmin),  # Para acciones con parámetros
]