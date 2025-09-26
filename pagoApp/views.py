# views.py
import json
import logging
import mercadopago
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError, ImproperlyConfigured
from ingresarApp.models import Producto, VarianteTalla
from .models import Venta, VentaItem

logger = logging.getLogger(__name__)

# Validaciones de configuración
if not getattr(settings, "MERCADOPAGO_ACCESS_TOKEN", None):
    raise ImproperlyConfigured("MERCADOPAGO_ACCESS_TOKEN no está configurado en settings.py")

# Inicializar SDK con el token seleccionado en settings
sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

def _mask_token(token):
    if not token:
        return "MISSING"
    if len(token) <= 12:
        return token
    return token[:6] + "..." + token[-6:]

@require_http_methods(["POST"])
def iniciar_pago(request):
    carrito = request.session.get('carrito', {})
    if not carrito:
        return JsonResponse({'error': 'El carrito está vacío'}, status=400)

    metodo_entrega = request.POST.get('metodo_entrega')
    errors = {}
    data = {}

    # Validaciones de formulario
    if metodo_entrega == 'envio':
        required_fields = {
            'nombre': "Nombre completo",
            'email': "Correo electrónico",
            'telefono': "Teléfono de contacto",
            'metodo_entrega': "Método de entrega"
        }
        for field, name in required_fields.items():
            value = request.POST.get(field)
            if not value:
                errors[field] = f"{name} es obligatorio"
            data[field] = value

        # campos extra
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
        for field, name in required_fields.items():
            value = request.POST.get(field)
            if not value:
                errors[field] = f"{name} es obligatorio"
            data[field] = value
    else:
        errors['metodo_entrega'] = "Método de entrega inválido o no seleccionado"

    # Validación emails simples
    if 'email' in data and data['email'] and '@' not in data['email']:
        errors['email'] = "Ingrese un email válido"
    if 'email_retiro' in data and data['email_retiro'] and '@' not in data['email_retiro']:
        errors['email_retiro'] = "Ingrese un email válido"

    if errors:
        return JsonResponse({'error': 'Datos incompletos', 'details': errors}, status=400)

    # Calcular total (asegurar float)
    try:
        total = sum(
            float(item['precio']) * int(item['cantidad'])
            for item in carrito.values()
            if item.get('precio') and item.get('cantidad')
        )
        if total <= 0:
            raise ValueError("Total inválido")
    except (ValueError, KeyError) as e:
        logger.exception("Error calculando total del carrito")
        return JsonResponse({'error': 'Error en los datos del carrito'}, status=400)

    # Persistir venta y items
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
            else:
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
    except Exception:
        logger.exception("Error creando venta")
        return JsonResponse({'error': 'Error al procesar la venta'}, status=500)

    # Preparar preferencia y crear en MP
    try:
        payer_info = {}
        if metodo_entrega == 'envio':
            payer_info = {
                "name": data['nombre'],
                "surname": request.POST.get('apellido', ''),
                "email": data['email'],
                "phone": {"number": data['telefono']},
                "address": {
                    "street_name": request.POST.get('direccion', ''),
                    "city": request.POST.get('ciudad', ''),
                    "federal_unit": request.POST.get('region', '')
                }
            }
        else:
            payer_info = {
                "name": data['nombre_retiro'],
                "surname": request.POST.get('apellido_retiro', ''),
                "email": data['email_retiro'],
                "phone": {"number": data['telefono_retiro']},
                "address": {}
            }

        # Para CLP: pasar entero
        unit_price = int(round(total))

        preference_data = {
            "items": [{
                "title": f"Compra en {settings.SITE_NAME}",
                "quantity": 1,
                "currency_id": "CLP",
                "unit_price": unit_price
            }],
            "payer": payer_info,
            "external_reference": str(venta.id),
            "back_urls": {
    "success": f"{settings.SITE_URL}{reverse('pago_exitoso')}",
    "failure": f"{settings.SITE_URL}{reverse('pago_fallido')}",
    "pending": f"{settings.SITE_URL}{reverse('pago_pendiente')}",
},
"auto_return": "approved",
"notification_url": f"{settings.SITE_URL}{reverse('webhook_mercadopago')}",

            "statement_descriptor": settings.SITE_NAME[:22]
        }

        # binary_mode solo en producción si así lo quieres
        if getattr(settings, "MERCADOPAGO_USAR_PRODUCCION", False):
            preference_data["binary_mode"] = True

        # Log token enmascarado y environment
        logger.info("Creando preferencia MercadoPago - token=%s - usar_produccion=%s",
                    _mask_token(getattr(settings, "MERCADOPAGO_ACCESS_TOKEN", None)),
                    getattr(settings, "MERCADOPAGO_USAR_PRODUCCION", None))

        preference_response = sdk.preference().create(preference_data)
        logger.debug("preference.create response: %s", json.dumps(preference_response, indent=2, default=str))

        if not isinstance(preference_response, dict):
            raise Exception("Respuesta inválida de MercadoPago")

        pref = preference_response.get("response")
        if not pref:
            raise Exception(f"MercadoPago no devolvió 'response' -> {preference_response}")

        init_point = pref.get("init_point") or pref.get("sandbox_init_point")
        if not init_point:
            raise Exception(f"No se encontró init_point en la preferencia: {pref}")

        # Redirigir al init_point (MP decide si es sandbox según token)
        return redirect(init_point)

    except Exception as e:
        logger.exception("Error creando preferencia MercadoPago")
        try:
            venta.delete()
        except Exception:
            logger.exception("No se pudo eliminar la venta tras fallo preferencia")
        return JsonResponse({"error": "Error al procesar el pago", "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_mercadopago(request):
    logger.info("📩 Webhook recibido desde MercadoPago")
    try:
        payload = json.loads(request.body.decode("utf-8"))
        logger.debug("Webhook payload: %s", json.dumps(payload, indent=2))
    except json.JSONDecodeError:
        logger.warning("JSON inválido recibido en webhook")
        return JsonResponse({"error": "JSON inválido"}, status=400)

    # Aceptar notifications tipo payment
    # Nota: MercadoPago puede enviar diferentes shapes; aquí tomamos 'type' y 'data'
    if payload.get("type") not in ("payment", "payment.updated", "payment.created"):
        logger.info("Evento webhooks ignorado: %s", payload.get("type"))
        return JsonResponse({"message": "Evento ignorado"}, status=200)

    payment_id = None
    # Dependiendo del webhook el id puede venir en data['id'] o data['object']['id']
    data_field = payload.get("data", {})
    if isinstance(data_field, dict):
        payment_id = data_field.get("id") or (data_field.get("object") or {}).get("id")

    if not payment_id:
        logger.warning("ID de pago faltante en webhook")
        return JsonResponse({"error": "ID de pago faltante"}, status=400)

    try:
        # Obtener información del pago desde MP para verificar estado real
        payment_response = sdk.payment().get(payment_id)
        logger.debug("payment.get response: %s", json.dumps(payment_response, indent=2, default=str))
        payment = payment_response.get("response")
        if not payment:
            logger.error("Respuesta inválida de payment.get")
            return JsonResponse({"error": "Respuesta inválida de MercadoPago"}, status=400)

        status = payment.get("status")
        external_reference = payment.get("external_reference")
        logger.info("Webhook payment_id=%s status=%s external_reference=%s", payment_id, status, external_reference)

        if status == "approved" and external_reference:
            try:
                with transaction.atomic():
                    venta = Venta.objects.select_for_update().get(id=external_reference)
                    if venta.pagado:
                        logger.info("Venta %s ya marcada como pagada", venta.id)
                        return JsonResponse({"message": "Venta ya estaba pagada"}, status=200)

                    venta.pagado = True
                    venta.payment_id = str(payment_id)
                    venta.metodo_pago = payment.get("payment_type_id", "")
                    venta.fecha_pago = payment.get("date_approved")
                    venta.save()

                    # Actualizar stock si corresponde
                    for item in venta.items.all():
                        if item.talla:
                            try:
                                variante = VarianteTalla.objects.select_for_update().get(
                                    producto=item.producto,
                                    talla=item.talla
                                )
                                variante.stock = max(variante.stock - item.cantidad, 0)
                                variante.save()
                            except VarianteTalla.DoesNotExist:
                                logger.warning("No se encontró variante: %s talla=%s", item.producto, item.talla)

                logger.info("Venta %s marcada como pagada correctamente", venta.id)
                return JsonResponse({"message": "Venta marcada como pagada"}, status=200)
            except Venta.DoesNotExist:
                logger.error("Venta no encontrada: %s", external_reference)
                return JsonResponse({"error": "Venta no encontrada"}, status=404)

        # Si no está approved simplemente respondemos 200
        return JsonResponse({"message": "Pago no aprobado o sin referencia externa"}, status=200)

    except Exception:
        logger.exception("Error procesando webhook")
        return JsonResponse({"error": "Error interno del servidor"}, status=500)


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
            logger.warning("No se encontró venta para external_reference=%s payment_id=%s", external_reference, payment_id)
            return render(request, 'pago/error.html', {
                'mensaje': 'No se encontró información del pago.',
                'contacto': settings.EMAIL_CONTACTO
            })

        request.session.pop('carrito', None)
        request.session.pop('datos_cliente', None)

        context = {'venta': venta, 'items': venta.items.all(), 'status': 'approved'}
        return render(request, 'pago/confirmacion.html', context)

    except Exception:
        logger.exception("Error en pago_exitoso")
        return render(request, 'pago/error.html', {
            'mensaje': 'Ocurrió un error al procesar tu pago exitoso',
            'contacto': settings.EMAIL_CONTACTO
        })


@require_http_methods(["GET"])
def pago_fallido(request):
    payment_id = request.GET.get('payment_id')
    context = {'contacto': settings.EMAIL_CONTACTO}
    if payment_id:
        try:
            venta = Venta.objects.get(payment_id=payment_id)
            context['venta'] = venta
        except Venta.DoesNotExist:
            logger.warning("Venta no encontrada para payment_id: %s", payment_id)
    return render(request, 'pago/fallido.html', context)


@require_http_methods(["GET"])
def pago_pendiente(request):
    payment_id = request.GET.get('payment_id')
    context = {'status': 'pending', 'contacto': settings.EMAIL_CONTACTO}
    if payment_id:
        try:
            venta = Venta.objects.get(payment_id=payment_id)
            context['venta'] = venta
        except Venta.DoesNotExist:
            logger.warning("Venta no encontrada para payment_id: %s", payment_id)
    return render(request, 'pago/pendiente.html', context)


@require_http_methods(["GET"])
def panel_ventas(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponseForbidden("No autorizado")
    ventas = Venta.objects.prefetch_related('items').order_by('-fecha_creacion')
    return render(request, 'admin/ventas.html', {
        'ventas': ventas,
        'total_ventas': sum(v.total for v in ventas if v.pagado)
    })


@require_http_methods(["GET"])
def detalle_venta(request, venta_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponseForbidden("No autorizado")
    venta = get_object_or_404(Venta.objects.prefetch_related('items'), id=venta_id)
    return render(request, 'admin/detalle_venta.html', {
        'venta': venta,
        'items': venta.items.all()
    })
