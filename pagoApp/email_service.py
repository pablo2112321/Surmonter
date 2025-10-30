# pagoApp/email_service.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def enviar_email_confirmacion_compra(venta):
    """
    Envía email de confirmación de compra al cliente
    """
    try:
        # Validaciones previas
        if not venta.email:
            logger.error(f"❌ No se puede enviar email: venta #{venta.id} no tiene email")
            return False

        # Preparar contexto para el email
        contexto = {
            'nombre_cliente': f"{venta.nombre} {venta.apellido}",
            'email_cliente': venta.email,
            'rut_cliente': venta.rut or "No especificado",
            'telefono_cliente': venta.telefono or "No especificado",
            'numero_pedido': venta.id,
            'fecha_pedido': venta.fecha.strftime("%d/%m/%Y %H:%M"),
            'metodo_entrega': venta.get_metodo_entrega_display(),
            'direccion_entrega': None,
            'productos': [],
            'total': venta.total,
            'empresa_envio': venta.get_empresa_envio_display() if venta.empresa_envio else "No especificada",
            'soporte_email': 'surmonterestampados@gmail.com',
            'sitio_web': settings.SITE_URL,
        }
        
        # Construir dirección de entrega si aplica
        if venta.metodo_entrega == 'envio' and venta.direccion and venta.ciudad:
            contexto['direccion_entrega'] = f"{venta.direccion}, {venta.ciudad}"
        elif venta.metodo_entrega == 'sucursal' and venta.direccion and venta.ciudad:
            contexto['direccion_entrega'] = f"{venta.direccion}, {venta.ciudad}"
        
        # Agregar productos al contexto
        for item in venta.items.all():
            contexto['productos'].append({
                'nombre': item.producto.nombre,
                'talla': item.talla or "Única",
                'cantidad': item.cantidad,
                'subtotal': item.subtotal,
                'precio_unitario': item.precio_unitario,
            })
        
        # Renderizar template HTML
        html_content = render_to_string('emails/confirmacion_compra.html', contexto)
        text_content = strip_tags(html_content)
        
        # Crear email
        email = EmailMultiAlternatives(
            subject=f'✅ Confirmación de Pedido #{venta.id} - Surmonter Tienda',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[venta.email],
            reply_to=['surmonterestampados@gmail.com'],
            bcc=['surmonterestampados@gmail.com']
        )
        
        # Adjuntar versión HTML
        email.attach_alternative(html_content, "text/html")
        
        # Enviar email
        email.send(fail_silently=False)
        
        logger.info(f"📧 Email de confirmación enviado a {venta.email} para pedido #{venta.id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error enviando email para pedido #{venta.id}: {str(e)}")
        return False