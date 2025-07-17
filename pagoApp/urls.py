from django.urls import path
from . import views

urlpatterns = [
    path('procesar/', views.procesar_compra, name='procesar_compra'),
    path('preparar/', views.preparar_pago, name='preparar_pago'),
    path('exito/', views.pago_exito, name='pago_exito'),
    path('fallo/', views.pago_fallo, name='pago_fallo'),
    path('pendiente/', views.pago_pendiente, name='pago_pendiente'),
]
