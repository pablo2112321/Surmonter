# test_email_simple.py
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Surmonter_Tienda.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("🚀 Probando sistema de emails de Surmonter...")
print(f"📧 Email desde: {settings.EMAIL_HOST_USER}")
print(f"🔑 Password configurado: {'SÍ' if settings.EMAIL_HOST_PASSWORD else 'NO'}")

try:
    send_mail(
        '🎉 ¡Sistema de Emails Funcionando! - Surmonter',
        '¡Excelente! El sistema de emails está configurado correctamente.\n\nLos clientes recibirán confirmaciones automáticas.',
        settings.DEFAULT_FROM_EMAIL,
        ['surmonterestampados@gmail.com'],
        fail_silently=False,
    )
    print("✅ ¡ÉXITO! Email de prueba enviado correctamente")
    print("📨 Revisa la bandeja de entrada de surmonterestampados@gmail.com")
except Exception as e:
    print(f"❌ Error: {e}")