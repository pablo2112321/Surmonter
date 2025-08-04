from django.urls import path
from . import views

urlpatterns = [
    path('pago/exitoso/', views.pago_exitoso, name='pago_exitoso'),
    path('pago/fallido/', views.pago_fallido, name='pago_fallido'),
    path('pago/pendiente/', views.pago_pendiente, name='pago_pendiente'),
    path('webhook/', views.webhook_mercadopago, name='webhook_mercadopago'),
    path('admin/ventas/', views.panel_ventas, name='panel_ventas'),
    path('admin/ventas/<int:venta_id>/', views.detalle_venta, name='detalle_venta'),
    path('procesar-compra/', views.iniciar_pago, name='procesar_compra'),
]

