# management/commands/test_email_final.py
import os
import sys

# Añade el directorio raíz al path para que Django encuentre los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Surmonter_Tienda.settings')
django.setup()

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Prueba final del sistema de emails'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Probando sistema de emails de Surmonter...")
        
        print(f"📧 Email desde: {settings.EMAIL_HOST_USER}")
        print(f"🔑 Password configurado: {'SÍ' if settings.EMAIL_HOST_PASSWORD else 'NO'}")
        print(f"🌐 SITE_URL: {settings.SITE_URL}")
        
        try:
            send_mail(
                '🎉 ¡Sistema de Emails Funcionando! - Surmonter',
                f'''¡Excelente! El sistema de emails está configurado correctamente.

📧 Email emisor: {settings.EMAIL_HOST_USER}
🌐 Sitio web: {settings.SITE_URL}
📞 Teléfono: +56 9 5665 2265

Los clientes ahora recibirán confirmaciones automáticas de sus compras.''',
                settings.DEFAULT_FROM_EMAIL,
                ['surmonterestampados@gmail.com'],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS('✅ ¡ÉXITO! Email de prueba enviado correctamente'))
            self.stdout.write('📨 Revisa la bandeja de entrada de surmonterestampados@gmail.com')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))