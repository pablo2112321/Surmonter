from django.conf import settings

def mercadopago_config(request):
    return {
        'MERCADOPAGO_PUBLIC_KEY': getattr(settings, 'MERCADOPAGO_PUBLIC_KEY', ''),
        'MERCADOPAGO_USAR_PRODUCCION': getattr(settings, 'MERCADOPAGO_USAR_PRODUCCION', False),
        'SITE_URL': getattr(settings, 'SITE_URL', 'http://localhost:8000'),  # ✅ AGREGADO
    }