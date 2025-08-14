from django.urls import path
from .views import paneladmin, admin_login, admin_logout

urlpatterns = [
    path('admin-login/', admin_login, name='admin_login'),
    path('paneladmin/', paneladmin, name='panel_admin'),  # Sin slash final
    path('paneladmin/<str:accion>/', paneladmin),  # Para acciones con parámetros
    path('admin-logout/', admin_logout, name='admin_logout'),
]