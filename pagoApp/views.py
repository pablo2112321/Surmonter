import json
import logging
import mercadopago
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from ingresarApp.models import Producto, VarianteTalla
from .models import Venta, VentaItem

# Configuración de logging
logger = logging.getLogger(__name__)

# Validación de configuración esencial
if not hasattr(settings, 'MERCADOPAGO_ACCESS_TOKEN'):
    raise ImproperlyConfigured("MERCADOPAGO_ACCESS_TOKEN no está configurado en settings.py")

# Configuración de MercadoPago
sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

@require_http_methods(["POST"])
def iniciar_pago(request):
    """
    Vista para iniciar el proceso de pago con MercadoPago
    Validaciones robustas y manejo de errores para producción
    """
    carrito = request.session.get('carrito', {})
    if not carrito:
        return JsonResponse({'error': 'El carrito está vacío'}, status=400)

    metodo_entrega = request.POST.get('metodo_entrega')

    errors = {}
    data = {}

    if metodo_entrega == 'envio':
        required_fields = {
            'nombre': "Nombre completo",
            'email': "Correo electrónico",
            'telefono': "Teléfono de contacto",
            'metodo_entrega': "Método de entrega"
        }
        # Validar campos obligatorios para envío
        for field, name in required_fields.items():
            value = request.POST.get(field)
            if not value:
                errors[field] = f"{name} es obligatorio"
            data[field] = value

        # Validar campos adicionales para envío
        direccion = request.POST.get('direccion', '').strip()
        ciudad = request.POST.get('ciudad', '').strip()
        region = request.POST.get('region', '').strip()
        empresa_envio = request.POST.get('empresa_envio')

        if not direccion:
            errors['direccion'] = "Dirección es obligatoria"
        if not ciudad:
            errors['ciudad'] = "Ciudad es obligatoria"
        if not region:
            errors['region'] = "Región es obligatoria"
        if not empresa_envio:
            errors['empresa_envio'] = "Empresa de envío es obligatoria"

    elif metodo_entrega == 'retiro':
        required_fields = {
            'nombre_retiro': "Nombre completo",
            'email_retiro': "Correo electrónico",
            'telefono_retiro': "Teléfono de contacto",
            'rut': "Rut",
            'metodo_entrega': "Método de entrega"
        }
        # Validar campos obligatorios para retiro
        for field, name in required_fields.items():
            value = request.POST.get(field)
            if not value:
                errors[field] = f"{name} es obligatorio"
            data[field] = value

    else:
        errors['metodo_entrega'] = "Método de entrega inválido o no seleccionado"

    # Validación básica adicional
    if 'email' in data and data['email'] and '@' not in data['email']:
        errors['email'] = "Ingrese un email válido"
    if 'email_retiro' in data and data['email_retiro'] and '@' not in data['email_retiro']:
        errors['email_retiro'] = "Ingrese un email válido"

    if errors:
        return JsonResponse({'error': 'Datos incompletos', 'details': errors}, status=400)

    # Calcular total
    try:
        total = sum(
            float(item['precio']) * int(item['cantidad'])
            for item in carrito.values()
            if item.get('precio') and item.get('cantidad')
        )
        if total <= 0:
            raise ValueError("Total inválido")
    except (ValueError, KeyError) as e:
        return JsonResponse({'error': 'Error en los datos del carrito'}, status=400)

    try:
        with transaction.atomic():
            if metodo_entrega == 'envio':
                venta = Venta.objects.create(
                    nombre=data['nombre'],
                    apellido=request.POST.get('apellido', ''),
                    email=data['email'],
                    telefono=data['telefono'],
                    direccion=request.POST.get('direccion', ''),
                    ciudad=request.POST.get('ciudad', ''),
                    region=request.POST.get('region', ''),
                    rut='',
                    metodo_entrega=metodo_entrega,
                    empresa_envio=request.POST.get('empresa_envio', ''),
                    total=total,
                    pagado=False,
                    origen='web'
                )
            else:  # retiro
                venta = Venta.objects.create(
                    nombre=data['nombre_retiro'],
                    apellido=request.POST.get('apellido_retiro', ''),
                    email=data['email_retiro'],
                    telefono=data['telefono_retiro'],
                    direccion='',
                    ciudad='',
                    region='',
                    rut=request.POST.get('rut', ''),
                    metodo_entrega=metodo_entrega,
                    empresa_envio='',
                    total=total,
                    pagado=False,
                    origen='web'
                )

            for item_id, item in carrito.items():
                producto = Producto.objects.get(id=item['id'])
                talla = item.get('talla', '')

                if talla:
                    variante = VarianteTalla.objects.filter(
                        producto=producto,
                        talla=talla
                    ).first()
                    if variante and item['cantidad'] > variante.stock:
                        raise ValidationError(f"Stock insuficiente para {producto.nombre} - Talla {talla}")

                VentaItem.objects.create(
                    venta=venta,
                    producto=producto,
                    producto_nombre=producto.nombre,
                    talla=talla,
                    cantidad=item['cantidad'],
                    precio_unitario=item['precio']
                )

    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Error al procesar la venta'}, status=500)

    # Preparar preferencia MercadoPago
    try:
        payer_info = {}
        if metodo_entrega == 'envio':
            payer_info = {
                "name": data['nombre'],
                "surname": request.POST.get('apellido', ''),
                "email": data['email'],
                "phone": {
                    "number": data['telefono']
                },
                "address": {
                    "street_name": request.POST.get('direccion', ''),
                    "city": request.POST.get('ciudad', ''),
                    "federal_unit": request.POST.get('region', '')
                }
            }
        else:  # retiro
            payer_info = {
                "name": data['nombre_retiro'],
                "surname": request.POST.get('apellido_retiro', ''),
                "email": data['email_retiro'],
                "phone": {
                    "number": data['telefono_retiro']
                },
                # Dirección vacía para retiro
                "address": {}
            }

        preference_data = {
            "items": [{
                "title": f"Compra en {settings.SITE_NAME}",
                "quantity": 1,
                "currency_id": "CLP",
                "unit_price": float(total)
            }],
            "payer": payer_info,
            "external_reference": str(venta.id),
            "back_urls": {
                "success": request.build_absolute_uri(reverse('pago_exitoso')),
                "failure": request.build_absolute_uri(reverse('pago_fallido')),
                "pending": request.build_absolute_uri(reverse('pago_pendiente')),
            },
            "auto_return": "approved",
            "notification_url": request.build_absolute_uri(reverse('webhook_mercadopago')),
            "statement_descriptor": settings.SITE_NAME[:22]
        }

        if settings.MERCADOPAGO_USAR_PRODUCCION:
            preference_data["binary_mode"] = True

        preference_response = sdk.preference().create(preference_data)

        if not preference_response.get("response"):
            raise Exception("Error en la respuesta de MercadoPago")

        preference = preference_response["response"]
        init_point = preference["sandbox_init_point"] if settings.DEBUG else preference["init_point"]

        return redirect(init_point)

    except Exception as e:
        venta.delete()  # revertir venta si falla creación preferencia
        return JsonResponse({
            "error": "Error al procesar el pago",
            "message": str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_mercadopago(request):
    """
    Webhook para recibir notificaciones de MercadoPago
    Implementa validaciones de seguridad para producción
    """
    # Verificación básica de origen (deberías implementar una más robusta)
    logger.info("📩 Webhook recibido desde MercadoPago")

    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        logger.warning("JSON inválido recibido en webhook")
        return JsonResponse({"error": "JSON inválido"}, status=400)

    # Solo procesar notificaciones de tipo payment
    if data.get("type") != "payment":
        return JsonResponse({"message": "Evento ignorado"}, status=200)

    payment_id = data.get("data", {}).get("id")
    if not payment_id:
        logger.warning("ID de pago faltante en webhook")
        return JsonResponse({"error": "ID de pago faltante"}, status=400)

    try:
        # Obtener información del pago desde MercadoPago
        payment_response = sdk.payment().get(payment_id)
        payment = payment_response.get("response")
        
        if not payment:
            logger.error(f"Respuesta inesperada de MercadoPago: {payment_response}")
            return JsonResponse({"error": "Respuesta inválida de MercadoPago"}, status=400)

        if payment.get("status") == "approved":
            external_reference = payment.get("external_reference")
            if not external_reference:
                logger.error("Referencia externa faltante en pago aprobado")
                return JsonResponse({"error": "Referencia externa faltante"}, status=400)

            try:
                with transaction.atomic():
                    venta = Venta.objects.select_for_update().get(id=external_reference)
                    
                    # Si ya estaba pagada, registrar pero no hacer nada
                    if venta.pagado:
                        logger.info(f"Venta {venta.id} ya estaba marcada como pagada")
                        return JsonResponse({"message": "Venta ya estaba pagada"}, status=200)
                    
                    # Actualizar venta
                    venta.pagado = True
                    venta.payment_id = str(payment_id)
                    venta.metodo_pago = payment.get("payment_type_id", "")
                    venta.fecha_pago = payment.get("date_approved")
                    venta.save()
                    
                    # Actualizar stock para cada item
                    for item in venta.items.all():
                        if item.talla:  # Solo si es producto con tallas
                            try:
                                variante = VarianteTalla.objects.select_for_update().get(
                                    producto=item.producto, 
                                    talla=item.talla
                                )
                                variante.stock = max(variante.stock - item.cantidad, 0)
                                variante.save()
                            except VarianteTalla.DoesNotExist:
                                logger.warning(f"No se encontró variante para {item.producto.nombre} - Talla: {item.talla}")

                    logger.info(f"Venta {venta.id} marcada como pagada correctamente")
                    return JsonResponse({"message": "Venta marcada como pagada"}, status=200)
                
            except Venta.DoesNotExist:
                logger.error(f"Venta no encontrada: {external_reference}")
                return JsonResponse({"error": "Venta no encontrada"}, status=404)
                
    except Exception as e:
        logger.error(f"Error en webhook: {e}", exc_info=True)
        return JsonResponse({"error": "Error interno del servidor"}, status=500)

    return JsonResponse({"message": "Pago no aprobado"}, status=200)

@require_http_methods(["GET"])
def pago_exitoso(request):
    try:
        external_reference = request.GET.get('external_reference')
        payment_id = request.GET.get('payment_id')

        venta = None
        if external_reference:
            venta = Venta.objects.filter(id=external_reference).first()
        elif payment_id:
            venta = Venta.objects.filter(payment_id=payment_id).first()

        if not venta:
            logger.warning(f"No se encontró venta para external_reference={external_reference} o payment_id={payment_id}")
            return render(request, 'pago/error.html', {
                'mensaje': 'No se encontró información del pago.',
                'contacto': settings.EMAIL_CONTACTO
            })

        # Limpiar carrito y datos del cliente en sesión
        request.session.pop('carrito', None)
        request.session.pop('datos_cliente', None)

        context = {
            'venta': venta,
            'items': venta.items.all(),
            'status': 'approved'
        }
        return render(request, 'pago/confirmacion.html', context)

    except Exception as e:
        logger.error(f"Error en pago_exitoso: {e}", exc_info=True)
        return render(request, 'pago/error.html', {
            'mensaje': 'Ocurrió un error al procesar tu pago exitoso',
            'contacto': settings.EMAIL_CONTACTO
        })



@require_http_methods(["GET"])
def pago_fallido(request):
    """
    Vista para cuando el pago falla
    """
    payment_id = request.GET.get('payment_id')
    context = {
        'contacto': settings.EMAIL_CONTACTO
    }
    
    if payment_id:
        try:
            venta = Venta.objects.get(payment_id=payment_id)
            context['venta'] = venta
        except Venta.DoesNotExist:
            logger.warning(f"Venta no encontrada para payment_id: {payment_id}")

    return render(request, 'pago/fallido.html', context)

@require_http_methods(["GET"])
def pago_pendiente(request):
    """
    Vista para cuando el pago está pendiente
    """
    payment_id = request.GET.get('payment_id')
    context = {
        'status': 'pending',
        'contacto': settings.EMAIL_CONTACTO
    }
    
    if payment_id:
        try:
            venta = Venta.objects.get(payment_id=payment_id)
            context['venta'] = venta
        except Venta.DoesNotExist:
            logger.warning(f"Venta no encontrada para payment_id: {payment_id}")

    return render(request, 'pago/pendiente.html', context)

@require_http_methods(["GET"])
def panel_ventas(request):
    """
    Panel administrativo para ver las ventas
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponseForbidden("No autorizado")
        
    ventas = Venta.objects.prefetch_related('items').order_by('-fecha_creacion')
    return render(request, 'admin/ventas.html', {
        'ventas': ventas,
        'total_ventas': sum(v.total for v in ventas if v.pagado)
    })

@require_http_methods(["GET"])
def detalle_venta(request, venta_id):
    """
    Detalle de una venta específica
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponseForbidden("No autorizado")
        
    venta = get_object_or_404(Venta.objects.prefetch_related('items'), id=venta_id)
    return render(request, 'admin/detalle_venta.html', {
        'venta': venta,
        'items': venta.items.all()
    })
