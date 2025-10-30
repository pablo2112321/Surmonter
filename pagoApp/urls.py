from django.urls import path
from . import views

urlpatterns = [
    # Pagos
    path('iniciar_pago/', views.iniciar_pago, name='iniciar_pago'),
    path('pago/exito/', views.pago_exitoso, name='pago_exitoso'),
    path('pago/fallido/', views.pago_fallido, name='pago_fallido'), 
    path('pago/pendiente/', views.pago_pendiente, name='pago_pendiente'),

    # Webhook (MercadoPago)
    path('webhook/mercadopago/', views.webhook_mercadopago, name='webhook_mercadopago'),

    # Testing
    path('test/webhook/', views.test_webhook, name='test_webhook'),  # ✅ AGREGAR ESTA LÍNEA

    # Panel admin
    path('admin/ventas/', views.panel_ventas, name='panel_ventas'),
    path('admin/ventas/<int:venta_id>/', views.detalle_venta, name='detalle_venta'),
    path('cambiar-estado-venta/<int:venta_id>/', views.cambiar_estado_venta, name='cambiar_estado_venta'),
]