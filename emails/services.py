# emails/services.py
import os
import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

# Configurar logging
logger = logging.getLogger(__name__)

def enviar_email_confirmacion_compra(orden):
    """
    Envía email de confirmación de compra al cliente
    """
    try:
        print(f"📧 Intentando enviar email para orden #{orden.id} a {orden.email}")
        
        # Contexto para el template
        context = {
            'orden': orden,
            'site_name': 'Surmonter',  # Cambia por el nombre de tu tienda
            'from_email': settings.DEFAULT_FROM_EMAIL,
        }
        
        # Renderizar template HTML
        html_content = render_to_string('emails/confirmacion_compra.html', context)
        text_content = strip_tags(html_content)  # Versión texto plano
        
        # Asunto del email
        subject = f'✅ Confirmación de Pedido #{orden.id} - Surmonter'
        
        # Crear email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[orden.email],
            reply_to=[settings.DEFAULT_FROM_EMAIL],
            headers={'X-Order-ID': str(orden.id)}
        )
        
        # Adjuntar versión HTML
        email.attach_alternative(html_content, "text/html")
        
        # Enviar email
        result = email.send(fail_silently=False)
        
        print(f"✅ Email enviado exitosamente a {orden.email}. Resultado: {result}")
        logger.info(f"Email de confirmación enviado para orden #{orden.id} a {orden.email}")
        return True
        
    except Exception as e:
        error_msg = f"❌ Error enviando email para orden #{orden.id}: {str(e)}"
        print(error_msg)
        logger.error(error_msg)
        return False

def enviar_email_admin_nueva_orden(orden):
    """
    Envía email al administrador cuando hay una nueva orden
    """
    try:
        subject = f'🛒 Nueva Orden #{orden.id} - {orden.nombre} {orden.apellido}'
        
        mensaje = f"""
        Nueva orden recibida:
        
        Orden ID: #{orden.id}
        Cliente: {orden.nombre} {orden.apellido}
        Email: {orden.email}
        Teléfono: {orden.telefono}
        Total: ${orden.total}
        Fecha: {orden.fecha}
        
        Productos:
        """
        
        for item in orden.items.all():
            mensaje += f"- {item.producto_nombre} (Talla: {item.talla}) x {item.cantidad} = ${item.subtotal}\n"
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.DEFAULT_FROM_EMAIL]  # Enviar al admin
        )
        
        email.send(fail_silently=False)
        print(f"✅ Email de notificación enviado al admin para orden #{orden.id}")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando email al admin: {str(e)}")
        return False