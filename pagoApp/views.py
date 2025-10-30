import json
import logging
from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import ValidationError, ImproperlyConfigured

import mercadopago

from ingresarApp.models import Producto, VarianteTalla
from .models import Venta, VentaItem

logger = logging.getLogger(__name__)

# Comprobar configuración
if not getattr(settings, "MERCADOPAGO_ACCESS_TOKEN", None):
    raise ImproperlyConfigured("MERCADOPAGO_ACCESS_TOKEN no está configurado en settings.py")

def _parse_cart(session_cart):
    """
    Convierte el carrito de session (estructura esperada) a una lista de items para crear Venta y para MP.
    Debe devolver (items_for_mp, items_for_db, total_clp_int)
    """
    if not session_cart:
        raise ValueError("Carrito vacío")

    items_mp = []
    items_db = []
    total = 0

    # Se espera session_cart como dict con claves -> {id, precio, cantidad, talla, subtotal}
    for key, it in session_cart.items():
        try:
            prod_id = int(it.get("id"))
            cantidad = int(it.get("cantidad", 1))
            # Precio en CLP (entero o string) -> asegurar entero
            precio_raw = it.get("precio")
            precio = int(round(float(precio_raw)))
        except Exception as e:
            logger.exception("Datos inválidos en carrito: %s", it)
            raise ValueError("Datos inválidos en carrito") from e

        producto = Producto.objects.filter(id=prod_id).first()
        if not producto:
            raise ValueError(f"Producto no encontrado (id={prod_id})")

        subtotal = precio * cantidad
        total += subtotal

        mp_item = {
            "title": producto.nombre[:120],
            "quantity": cantidad,
            "currency_id": "CLP",
            "unit_price": float(precio),  # MercadoPago acepta números
        }
        items_mp.append(mp_item)

        items_db.append({
            "producto": producto,
            "talla": it.get("talla", ""),
            "cantidad": cantidad,
            "precio": precio,
        })

    if total <= 0:
        raise ValueError("Total inválido")
    return items_mp, items_db, int(total)

@require_http_methods(["POST"])
@csrf_protect
def iniciar_pago(request):
    # ✅ DEBUG TEMPORAL
    print("=== DEBUG INICIAR_PAGO ===")
    print("MERCADOPAGO_ACCESS_TOKEN existe:", bool(settings.MERCADOPAGO_ACCESS_TOKEN))
    print("=== VISTA INICIAR_PAGO EJECUTADA ===")
    print("Método:", request.method)
    print("Content-Type:", request.content_type)

    
    # ✅ Inicializar SDK aquí
    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
    
    try:
        # Obtener carrito desde session
        carrito = request.session.get("carrito", {})
        print("Carrito session:", carrito)
        items_mp, items_db, total_clp = _parse_cart(carrito)
        print("Items MP:", items_mp)

    except Exception as e:
        # ✅ ASEGURAR QUE LOS ERRORES TAMBIÉN DEVUELVAN JSON
        logger.exception("Error en iniciar_pago")
        return JsonResponse({
            "error": "Error interno del servidor",
            "message": str(e)
        }, status=500)

    # ✅ INICIALIZAR payer_info Y venta FUERA DE LOS BLOQUES
    payer_info = None
    venta = None
    
    # leer método de entrega y campos requeridos
    metodo_entrega = request.POST.get("metodo_entrega")
    print("Método de entrega recibido:", metodo_entrega)
    
    if metodo_entrega not in ("envio", "retiro", "sucursal"):
        return JsonResponse({"error": "Método de entrega inválido"}, status=400)

    # Recolectar datos mínimos del payer (email obligatorio para MP)
    try:
        if metodo_entrega == "envio":
            print("Procesando envío a domicilio...")
            nombre = request.POST["nombre"].strip()
            apellido = request.POST["apellido"].strip()
            email = request.POST["email"].strip()
            telefono = request.POST.get("telefono", "").strip()
            direccion = request.POST.get("direccion", "").strip()
            ciudad = request.POST.get("ciudad", "").strip()
            region = request.POST.get("region", "").strip()
            empresa_envio = request.POST.get("empresa_envio", "").strip()
            rut_envio = request.POST.get("rut_envio", "").strip()
            
            print(f"Datos envío - Nombre: {nombre}, Email: {email}, Tel: {telefono}")
            
            payer_info = {
                "name": nombre,
                "surname": apellido,
                "email": email,
                "phone": {"number": telefono} if telefono else {},
                "address": {
                    "street_name": direccion,
                    "city": ciudad,
                    "federal_unit": region
                } if direccion and ciudad and region else {}
            }
            
        elif metodo_entrega == "retiro":
            print("Procesando retiro en tienda...")
            nombre = request.POST["nombre_retiro"].strip()
            apellido = request.POST["apellido_retiro"].strip()
            email = request.POST["email_retiro"].strip()
            telefono = request.POST.get("telefono_retiro", "").strip()
            rut = request.POST.get("rut", "").strip()
            
            print(f"Datos retiro - Nombre: {nombre}, Email: {email}, Tel: {telefono}")
            
            payer_info = {
                "name": nombre,
                "surname": apellido,
                "email": email,
                "phone": {"number": telefono} if telefono else {}
            }
            
        else:  # sucursal
            print("Procesando envío a sucursal...")
            nombre = request.POST["nombre_sucursal"].strip()
            apellido = request.POST["apellido_sucursal"].strip()
            email = request.POST["email_sucursal"].strip()
            telefono = request.POST.get("telefono_sucursal", "").strip()
            direccion_suc = request.POST.get("direccion_sucursal", "").strip()
            ciudad_suc = request.POST.get("ciudad_sucursal", "").strip()
            region_suc = request.POST.get("region_sucursal", "").strip()
            empresa_envio_sucursal = request.POST.get("empresa_envio_sucursal", "").strip()
            rut_sucursal = request.POST.get("rut_sucursal", "").strip()
            
            print(f"Datos sucursal - Nombre: {nombre}, Email: {email}, Tel: {telefono}")
            
            payer_info = {
                "name": nombre,
                "surname": apellido,
                "email": email,
                "phone": {"number": telefono} if telefono else {},
                "address": {
                    "street_name": direccion_suc,
                    "city": ciudad_suc,
                    "federal_unit": region_suc
                } if direccion_suc and ciudad_suc and region_suc else {}
            }
            
        print("Payer info construido:", payer_info)
            
    except KeyError as e:
        logger.warning("Campo requerido faltante: %s", e)
        return JsonResponse({"error": "Falta campo requerido", "field": str(e)}, status=400)

    # ✅ VERIFICAR QUE payer_info SE CONSTRUYÓ CORRECTAMENTE
    if not payer_info:
        logger.error("payer_info no se construyó correctamente")
        return JsonResponse({"error": "Error procesando datos del comprador"}, status=400)

    # Crear venta y items en DB
    try:
        with transaction.atomic():
            # ✅ USAR LAS VARIABLES CORRECTAS SEGÚN EL MÉTODO
            if metodo_entrega == "envio":
                venta = Venta.objects.create(
                    nombre=nombre,
                    apellido=apellido,
                    email=email,
                    telefono=telefono or "",
                    direccion=direccion,
                    ciudad=ciudad,
                    region=region,
                    rut=rut_envio,
                    metodo_entrega=metodo_entrega,
                    empresa_envio=empresa_envio,
                    total=total_clp,
                    pagado=False,
                    origen="web"
                )
            elif metodo_entrega == "retiro":
                venta = Venta.objects.create(
                    nombre=nombre,
                    apellido=apellido,
                    email=email,
                    telefono=telefono or "",
                    direccion="",
                    ciudad="",
                    region="",
                    rut=rut,
                    metodo_entrega=metodo_entrega,
                    empresa_envio="",
                    total=total_clp,
                    pagado=False,
                    origen="web"
                )
            else:  # sucursal
                venta = Venta.objects.create(
                    nombre=nombre,
                    apellido=apellido,
                    email=email,
                    telefono=telefono or "",
                    direccion=direccion_suc,
                    ciudad=ciudad_suc,
                    region=region_suc,
                    rut=rut_sucursal,
                    metodo_entrega=metodo_entrega,
                    empresa_envio=empresa_envio_sucursal,
                    total=total_clp,
                    pagado=False,
                    origen="web"
                )

            print(f"Venta creada en DB - ID: {venta.id}")

            # Crear items de venta y validar stock
            for it in items_db:
                # validar stock si corresponde
                talla = it["talla"]
                producto = it["producto"]
                cantidad = it["cantidad"]

                if talla:
                    variante = VarianteTalla.objects.filter(producto=producto, talla=talla).first()
                    if variante and cantidad > variante.stock:
                        raise ValidationError(f"Stock insuficiente para {producto.nombre} talla {talla}")

                VentaItem.objects.create(
                    venta=venta,
                    producto=producto,
                    talla=talla,
                    cantidad=cantidad,
                    precio=it["precio"]
                )

    except Exception as e:
        logger.exception("Error creando la venta en DB")
        return JsonResponse({"error": "Error creando venta", "message": str(e)}, status=500)

    # Crear preferencia MercadoPago
    try:
        # ✅ CONFIGURACIÓN FLEXIBLE - FÁCIL DE CAMBIAR CON NGROK
        # CAMBIA ESTA VARIABLE CUANDO CAMBIES NGROK
        SITE_URL = settings.SITE_URL  # Esta variable está en settings.py
        
        preference_data = {
            "items": items_mp,
            "payer": payer_info,
            "external_reference": str(venta.id),
            "back_urls": {
                "success": f"{settings.SITE_URL}{reverse('pago_exitoso')}",
                "failure": f"{settings.SITE_URL}{reverse('pago_fallido')}",
                "pending": f"{settings.SITE_URL}{reverse('pago_pendiente')}",
            },
            "auto_return": "approved",
            "statement_descriptor": settings.SITE_NAME[:22],
            "notification_url": f"{settings.SITE_URL}{reverse('webhook_mercadopago')}"
        }

        print("Preference data enviado a MP:", preference_data)

        pref_resp = sdk.preference().create(preference_data)
        print("Respuesta completa de MP:", pref_resp)

        if pref_resp["status"] in [200, 201]:
            pref_obj = pref_resp.get("response", {})
            print("Preferencia creada exitosamente:", pref_obj.get("id"))
            
            # Vaciar carrito de session
            request.session["carrito"] = {}
            request.session.modified = True

            return JsonResponse({
                "init_point": pref_obj.get("init_point"), 
                "preference": pref_obj
            }, status=200)
        else:
            logger.error(f"Error MP API: {pref_resp}")
            error_msg = pref_resp.get('response', {}).get('message', 'Error desconocido de MercadoPago')
            raise Exception(f"Error de API: {error_msg}")
            
    except Exception as e:
        logger.exception("Error creando preferencia MercadoPago")
        # Intentar cleanup de la venta creada
        try:
            if venta:
                venta.delete()
                print("Venta eliminada por fallo en preferencia")
        except Exception:
            logger.exception("No se pudo eliminar venta tras fallo de preferencia")
        return JsonResponse({"error": "Error creando preferencia", "message": str(e)}, status=500)

# Webhook: recibir notificaciones de MercadoPago
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@require_http_methods(["POST", "GET"])
def webhook_mercadopago(request):
    """
    Webhook mejorado que maneja TODOS los formatos de MercadoPago:
    1. Parámetros GET (?id=XXX&topic=payment) ← FUNCIONANDO
    2. Parámetros GET con data.id (?data.id=XXX&type=payment) ← NUEVO
    3. JSON en el body ← NUEVO
    """
    logger.info("🎯 === WEBHOOK MERCADOPAGO MEJORADO ===")
    
    # ✅ LOG COMPLETO PARA DEBUGGING
    logger.info(f"📧 Método: {request.method}")
    logger.info(f"🔗 GET params: {dict(request.GET)}")
    logger.info(f"📦 POST data: {dict(request.POST)}")
    
    # Inicializar SDK
    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
    
    # ✅ EXTRACCIÓN MEJORADA DE PARÁMETROS - MANEJA TODOS LOS FORMATOS
    topic = None
    resource_id = None
    
    # FORMATO 1: Parámetros GET estándar (?id=XXX&topic=payment)
    if request.GET.get('id') and request.GET.get('topic'):
        resource_id = request.GET.get('id')
        topic = request.GET.get('topic')
        logger.info(f"🔍 Formato 1 detectado - Topic: {topic}, ID: {resource_id}")
    
    # FORMATO 2: Parámetros GET con data.id (?data.id=XXX&type=payment)  
    elif request.GET.get('data.id') and request.GET.get('type'):
        resource_id = request.GET.get('data.id')
        topic = request.GET.get('type')
        logger.info(f"🔍 Formato 2 detectado - Type: {topic}, data.id: {resource_id}")
    
    # FORMATO 3: JSON en el body (nuevos webhooks)
    elif request.body:
        try:
            body_data = json.loads(request.body.decode('utf-8'))
            logger.info(f"📦 Body JSON recibido: {body_data}")
            
            # Extraer del formato JSON
            topic = body_data.get('type')
            resource_id = body_data.get('data', {}).get('id') or body_data.get('id')
            
            logger.info(f"🔍 Formato 3 detectado - Type: {topic}, ID: {resource_id}")
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ JSON inválido en body: {e}")
    
    # ✅ SI NO SE ENCONTRÓ EN NINGÚN FORMATO, BUSCAR EN POST DATA
    if not topic and request.POST:
        topic = request.POST.get('type')
        resource_id = request.POST.get('data.id') or request.POST.get('id')
        if topic and resource_id:
            logger.info(f"🔍 Formato POST detectado - Type: {topic}, ID: {resource_id}")
    
    logger.info(f"🎯 Parámetros finales - Topic: {topic}, Resource ID: {resource_id}")
    
    if not topic or not resource_id:
        logger.warning("❌ No se pudieron extraer topic/type o resource_id")
        logger.warning(f"📋 GET: {dict(request.GET)}")
        logger.warning(f"📦 POST: {dict(request.POST)}")
        if request.body:
            logger.warning(f"📄 Body: {request.body.decode('utf-8')}")
        
        return JsonResponse({
            "error": "No se pudieron extraer los parámetros necesarios",
            "help": "Se espera: ?id=XXX&topic=payment O ?data.id=XXX&type=payment O JSON en body",
            "received_get": dict(request.GET),
            "received_post": dict(request.POST)
        }, status=400)
    
    # ✅ NORMALIZAR TOPIC (algunos vienen como 'payment', otros como 'payment.updated')
    if 'payment' in topic:
        normalized_topic = 'payment'
    elif 'merchant_order' in topic:
        normalized_topic = 'merchant_order'
    else:
        normalized_topic = topic
    
    logger.info(f"🔄 Topic normalizado: {topic} → {normalized_topic}")
    
    try:
        if normalized_topic == 'payment':
            # ✅ PROCESAR PAGO
            logger.info(f"💳 Procesando payment: {resource_id}")
            
            # Consultar el pago en MercadoPago
            mp_resp = sdk.payment().get(resource_id)
            logger.info(f"📊 Status code MP: {mp_resp.get('status')}")
            
            if mp_resp["status"] not in [200, 201]:
                logger.error(f"❌ Error al obtener pago {resource_id}: {mp_resp}")
                
                # ✅ SI ES MODO SANDBOX, PODRÍA SER UN PAGO DE PRUEBA
                if not settings.MERCADOPAGO_USAR_PRODUCCION:
                    logger.info(f"🔧 Modo Sandbox - Podría ser pago de prueba")
                    # Intentar procesar igual con datos simulados para testing
                    return _procesar_pago_sandbox(resource_id, topic, request)
                
                return JsonResponse({"error": "Error al consultar pago en MercadoPago"}, status=400)
                
            payment = mp_resp.get("response", {})
            status = payment.get("status")
            external_reference = payment.get("external_reference")
            
            logger.info(f"📄 Payment {resource_id} - Status: {status}, External Ref: {external_reference}")
            
            if not external_reference:
                logger.warning(f"⚠️ Payment {resource_id} sin external_reference")
                return JsonResponse({"message": "Pago sin referencia externa"}, status=200)
            
            # Buscar y actualizar venta
            with transaction.atomic():
                try:
                    venta = Venta.objects.select_for_update().get(id=external_reference)
                    logger.info(f"✅ Venta encontrada: #{venta.id}, Estado actual: {venta.estado}")
                except Venta.DoesNotExist:
                    logger.error(f"❌ Venta no encontrada: {external_reference}")
                    return JsonResponse({"error": "Venta no encontrada"}, status=404)
                
                # ✅ ACTUALIZAR ESTADO SEGÚN MERCADOPAGO
                estado_anterior = venta.estado
                
                if status == "approved":
                    venta.estado = "aprobado"
                    venta.pagado = True
                    logger.info(f"🎉 Venta #{external_reference} APROBADA")
                elif status == "rejected":
                    venta.estado = "rechazado" 
                    venta.pagado = False
                    logger.info(f"❌ Venta #{external_reference} RECHAZADA")
                elif status == "in_process":
                    venta.estado = "en_proceso"
                    venta.pagado = False
                    logger.info(f"⏳ Venta #{external_reference} EN PROCESO")
                elif status == "cancelled":
                    venta.estado = "cancelado"
                    venta.pagado = False
                    logger.info(f"🚫 Venta #{external_reference} CANCELADA")
                else:
                    logger.info(f"🔍 Venta #{external_reference} - Estado no manejado: {status}")
                
                # Guardar información del pago
                venta.payment_id = str(resource_id)
                venta.metodo_pago = payment.get("payment_type_id", "")
                
                # Convertir fecha de pago si existe
                fecha_aprobado = payment.get("date_approved")
                if fecha_aprobado:
                    from django.utils.dateparse import parse_datetime
                    fecha_parseada = parse_datetime(fecha_aprobado)
                    if fecha_parseada:
                        venta.fecha_pago = fecha_parseada
                
                venta.save()
                logger.info(f"💾 Venta #{venta.id} guardada - Estado: {estado_anterior} → {venta.estado}")
                
                # ✅ REDUCIR STOCK SOLO SI FUE APROBADO
                if status == "approved":
                    _reducir_stock_venta(venta)
            
            return JsonResponse({
                "message": "Venta actualizada correctamente", 
                "venta_id": external_reference,
                "estado": status,
                "estado_anterior": estado_anterior,
                "estado_nuevo": venta.estado,
                "formato": "payment_processed"
            }, status=200)
            
        elif normalized_topic == 'merchant_order':
            # ✅ PROCESAR MERCHANT ORDER (código existente que SÍ funciona)
            logger.info(f"📦 Procesando merchant_order: {resource_id}")
            
            # Consultar la merchant order
            mp_resp = sdk.merchant_order().get(resource_id)
            if mp_resp["status"] not in [200, 201]:
                logger.error(f"❌ Error al obtener merchant order {resource_id}: {mp_resp}")
                return JsonResponse({"error": "Error al consultar merchant order"}, status=400)
                
            order = mp_resp.get("response", {})
            external_reference = order.get("external_reference")
            
            logger.info(f"📄 Merchant Order {resource_id} - External Ref: {external_reference}")
            
            if not external_reference:
                logger.warning(f"⚠️ Merchant Order {resource_id} sin external_reference")
                return JsonResponse({"message": "Merchant order sin referencia externa"}, status=200)
            
            # Buscar venta y actualizar (código existente)
            with transaction.atomic():
                try:
                    venta = Venta.objects.select_for_update().get(id=external_reference)
                    logger.info(f"✅ Venta encontrada via merchant order: #{venta.id}")
                except Venta.DoesNotExist:
                    logger.error(f"❌ Venta no encontrada para merchant order: {external_reference}")
                    return JsonResponse({"error": "Venta no encontrada"}, status=404)
                
                # Procesar payments dentro de la merchant order
                payments = order.get("payments", [])
                logger.info(f"💳 Payments en merchant order: {len(payments)}")
                
                if payments:
                    # Tomar el último payment
                    latest_payment = payments[-1]
                    payment_status = latest_payment.get("status")
                    payment_id = latest_payment.get("id")
                    
                    logger.info(f"🔍 Payment en merchant order: {payment_id} - Status: {payment_status}")
                    
                    # Sincronizar estado con el payment
                    estado_anterior = venta.estado
                    
                    if payment_status == "approved":
                        venta.estado = "aprobado"
                        venta.pagado = True
                    elif payment_status == "rejected":
                        venta.estado = "rechazado"
                        venta.pagado = False
                    elif payment_status == "in_process":
                        venta.estado = "en_proceso"
                        venta.pagado = False
                    elif payment_status == "cancelled":
                        venta.estado = "cancelado"
                        venta.pagado = False
                    
                    # Guardar payment_id
                    if payment_id:
                        venta.payment_id = str(payment_id)
                    
                    logger.info(f"🔄 Venta #{venta.id} actualizada via merchant order: {estado_anterior} → {venta.estado}")
                
                venta.save()
            
            return JsonResponse({
                "message": "Merchant order procesada correctamente",
                "venta_id": external_reference,
                "payments_count": len(payments),
                "formato": "merchant_order_processed"
            }, status=200)
            
        else:
            logger.warning(f"⚠️ Topic no manejado: {topic} (normalizado: {normalized_topic})")
            return JsonResponse({"error": f"Topic no soportado: {topic}"}, status=400)
            
    except Exception as e:
        logger.exception(f"💥 ERROR procesando webhook - Topic: {topic}, ID: {resource_id}")
        return JsonResponse({
            "error": "Error interno del servidor",
            "details": str(e),
            "topic": topic,
            "resource_id": resource_id
        }, status=500)

# ✅ FUNCIÓN AUXILIAR PARA REDUCIR STOCK
def _reducir_stock_venta(venta):
    """Reduce el stock para todos los items de una venta aprobada - VERSIÓN MEJORADA"""
    stock_reducido = []
    errores = []
    
    for item in venta.items.all():
        try:
            if item.talla:
                # Buscar variante de talla
                variante = VarianteTalla.objects.select_for_update().get(
                    producto=item.producto, 
                    talla=item.talla
                )
                if variante.stock >= item.cantidad:
                    variante.stock -= item.cantidad
                    variante.save()
                    stock_reducido.append(f"{item.producto.nombre} (talla {item.talla}): -{item.cantidad}")
                    logger.info(f"📦 Stock reducido: {item.producto.nombre} talla {item.talla} - {item.cantidad} unidades")
                else:
                    error_msg = f"Stock insuficiente: {item.producto.nombre} talla {item.talla} (stock: {variante.stock}, necesario: {item.cantidad})"
                    errores.append(error_msg)
                    logger.warning(f"⚠️ {error_msg}")
                    
            else:
                # Si no tiene talla, reducir stock del producto principal
                if item.producto.stock >= item.cantidad:
                    item.producto.stock -= item.cantidad
                    item.producto.save()
                    stock_reducido.append(f"{item.producto.nombre}: -{item.cantidad}")
                    logger.info(f"📦 Stock reducido (sin talla): {item.producto.nombre} - {item.cantidad} unidades")
                else:
                    error_msg = f"Stock insuficiente (sin talla): {item.producto.nombre} (stock: {item.producto.stock}, necesario: {item.cantidad})"
                    errores.append(error_msg)
                    logger.warning(f"⚠️ {error_msg}")
                    
        except VarianteTalla.DoesNotExist:
            error_msg = f"Variante no encontrada: {item.producto.nombre} talla {item.talla}"
            errores.append(error_msg)
            logger.warning(f"⚠️ {error_msg}")
        except Exception as e:
            error_msg = f"Error procesando {item.producto.nombre}: {str(e)}"
            errores.append(error_msg)
            logger.error(f"❌ {error_msg}")
    
    # Construir resultado
    result = ""
    if stock_reducido:
        result += f"Stock reducido: {', '.join(stock_reducido)}"
    if errores:
        if result:
            result += " | "
        result += f"Errores: {', '.join(errores)}"
    
    logger.info(f"📊 Resultado stock para venta #{venta.id}: {result}")
    return result
# -------------------

@csrf_exempt
def test_webhook(request):
    """
    Vista temporal para probar el webhook manualmente
    """
    if request.method == 'GET':
        # Mostrar formulario de prueba
        return render(request, 'pago/test_webhook.html')
    
    # Procesar prueba
    payment_id = request.POST.get('payment_id')
    external_ref = request.POST.get('external_reference')
    scenario = request.POST.get('scenario', 'approved')
    
    if not payment_id or not external_ref:
        return JsonResponse({"error": "Faltan parámetros payment_id y external_reference"}, status=400)
    
    logger.info(f"🧪 TEST WEBHOOK - Payment ID: {payment_id}, External Ref: {external_ref}, Scenario: {scenario}")
    
    try:
        with transaction.atomic():
            # Verificar si la venta existe
            try:
                venta = Venta.objects.select_for_update().get(id=external_ref)
                logger.info(f"✅ Venta encontrada: #{venta.id} - Estado actual: {venta.estado}")
            except Venta.DoesNotExist:
                logger.error(f"❌ Venta no encontrada: {external_ref}")
                return JsonResponse({"error": f"Venta #{external_ref} no encontrada"}, status=404)
            
            # Guardar estado anterior
            estado_anterior = venta.estado
            
            # Simular diferentes escenarios
            if scenario == 'approved':
                venta.estado = 'aprobado'
                venta.pagado = True
                venta.payment_id = payment_id
                message = "✅ Pago APROBADO simulado"
                
                # Reducir stock si se aprueba - CON MANEJO DE ERRORES
                try:
                    stock_result = _reducir_stock_venta(venta)
                    message += f" | Stock: {stock_result}"
                except Exception as e:
                    logger.error(f"❌ Error reduciendo stock: {e}")
                    message += f" | ❌ Error en stock: {str(e)}"
                
            elif scenario == 'rejected':
                venta.estado = 'rechazado'
                venta.pagado = False
                venta.payment_id = payment_id
                message = "❌ Pago RECHAZADO simulado"
                
            elif scenario == 'pending':
                venta.estado = 'en_proceso'
                venta.pagado = False
                venta.payment_id = payment_id
                message = "⏳ Pago EN PROCESO simulado"
                
            elif scenario == 'cancelled':
                venta.estado = 'cancelado'
                venta.pagado = False
                venta.payment_id = payment_id
                message = "🚫 Pago CANCELADO simulado"
                
            else:
                return JsonResponse({"error": "Escenario no válido"}, status=400)
            
            venta.save()
            logger.info(f"🔄 Venta #{venta.id} actualizada: {estado_anterior} → {venta.estado}")
            
            return JsonResponse({
                "message": message,
                "venta_id": external_ref,
                "payment_id": payment_id,
                "estado_anterior": estado_anterior,
                "estado_nuevo": venta.estado,
                "pagado": venta.pagado,
                "scenario": scenario
            })
            
    except Exception as e:
        logger.exception(f"💥 ERROR en test_webhook: {e}")
        return JsonResponse({
            "error": "Error interno del servidor",
            "details": str(e)
        }, status=500)

# Vistas públicas de resultado - MEJORADAS
@require_http_methods(["GET"])
def pago_exitoso(request):
    """Página de éxito - Maneja tanto redirección automática como manual"""
    external_reference = request.GET.get('external_reference')
    payment_id = request.GET.get('payment_id')
    collection_id = request.GET.get('collection_id')  # ✅ Alternativo
    preference_id = request.GET.get('preference_id')  # ✅ Alternativo
    
    print(f"=== PAGO EXITOSO ===")
    print(f"external_reference: {external_reference}")
    print(f"payment_id: {payment_id}")
    print(f"collection_id: {collection_id}")
    print(f"preference_id: {preference_id}")
    print(f"Todos los parámetros: {dict(request.GET)}")
    
    # ✅ BUSCAR VENTA POR MÚLTIPLES MÉTODOS
    venta = None
    
    if external_reference:
        venta = Venta.objects.filter(id=external_reference).first()
        print(f"Buscando por external_reference {external_reference}: {venta}")
    
    if not venta and payment_id:
        venta = Venta.objects.filter(payment_id=payment_id).first()
        print(f"Buscando por payment_id {payment_id}: {venta}")
        
    if not venta and collection_id:
        venta = Venta.objects.filter(payment_id=collection_id).first()
        print(f"Buscando por collection_id {collection_id}: {venta}")
    
    # ✅ SI NO ENCUENTRA VENTA, MOSTRAR PÁGINA GENÉRICA
    if not venta:
        print("No se encontró información de la venta")
        return render(request, 'pago/confirmacion.html', {
            'mensaje': '¡Pago exitoso! Hemos recibido tu pago correctamente.',
            'contacto': getattr(settings, 'EMAIL_CONTACTO', 'soporte@tutienda.com')  # ✅ CONFIGURABLE
        })
    
    print(f"Venta encontrada: #{venta.id} - Estado: {venta.estado} - Pagado: {venta.pagado}")
    
    # ✅ LIMPIAR CARRITO Y MOSTRAR CONFIRMACIÓN
    request.session.pop('carrito', None)
    
    return render(request, 'pago/confirmacion.html', {
        'venta': venta, 
        'items': venta.items.all(), 
        'status': 'approved'
    })

@require_http_methods(["GET"])
def pago_fallido(request):
    """Página para pagos fallidos"""
    external_reference = request.GET.get('external_reference')
    payment_id = request.GET.get('payment_id')
    
    print(f"=== PAGO FALLIDO ===")
    print(f"external_reference: {external_reference}")
    print(f"payment_id: {payment_id}")
    
    context = {
        'contacto': getattr(settings, 'EMAIL_CONTACTO', 'soporte@tutienda.com'),  # ✅ CONFIGURABLE
        'status': 'failed'
    }
    
    if external_reference:
        venta = Venta.objects.filter(id=external_reference).first()
        if venta:
            context['venta'] = venta
            print(f"Venta encontrada en fallido: #{venta.id}")
    
    return render(request, 'pago/fallido.html', context)

@require_http_methods(["GET"])
def pago_pendiente(request):
    """Página para pagos pendientes - También verifica si ya fue aprobado"""
    external_reference = request.GET.get('external_reference')
    payment_id = request.GET.get('payment_id')
    
    print(f"=== PAGO PENDIENTE ===")
    print(f"external_reference: {external_reference}")
    print(f"payment_id: {payment_id}")
    
    context = {
        'status': 'pending', 
        'contacto': getattr(settings, 'EMAIL_CONTACTO', 'soporte@tutienda.com')  # ✅ CONFIGURABLE
    }
    
    # ✅ VERIFICAR SI EL PAGO YA FUE APROBADO VÍA WEBHOOK
    if external_reference:
        venta = Venta.objects.filter(id=external_reference).first()
        if venta:
            print(f"Venta encontrada en pendiente: #{venta.id} - Estado: {venta.estado}")
            context['venta'] = venta
            
            # ✅ SI YA ESTÁ APROBADO, REDIRIGIR A ÉXITO
            if venta.estado == 'aprobado' and venta.pagado:
                print("Pago ya aprobado, redirigiendo a éxito")
                return redirect('pago_exitoso')
    
    return render(request, 'pago/pendiente.html', context)

# -------------------
# Panel administrativo
# -------------------
from django.contrib.auth.decorators import user_passes_test

@user_passes_test(lambda u: u.is_staff)
def panel_ventas(request):
    """Panel de administración que lista todas las ventas separadas por estado."""
    ventas_aprobadas = Venta.objects.filter(estado='aprobado').order_by('-fecha')
    ventas_rechazadas = Venta.objects.filter(estado='rechazado').order_by('-fecha')
    ventas_pendientes = Venta.objects.filter(estado='pendiente').order_by('-fecha')
    ventas_en_proceso = Venta.objects.filter(estado='en_proceso').order_by('-fecha')
    ventas_canceladas = Venta.objects.filter(estado='cancelado').order_by('-fecha')
    
    # Estadísticas
    total_aprobadas = sum(v.total for v in ventas_aprobadas)
    total_pendientes = sum(v.total for v in ventas_pendientes)
    total_en_proceso = sum(v.total for v in ventas_en_proceso)
    
    context = {
        'ventas_aprobadas': ventas_aprobadas,
        'ventas_rechazadas': ventas_rechazadas,
        'ventas_pendientes': ventas_pendientes,
        'ventas_en_proceso': ventas_en_proceso,
        'ventas_canceladas': ventas_canceladas,
        'total_aprobadas': total_aprobadas,
        'total_pendientes': total_pendientes,
        'total_en_proceso': total_en_proceso,
    }
    
    return render(request, 'adminpanel/panel_ventas.html', context)

@user_passes_test(lambda u: u.is_staff)
def detalle_venta(request, venta_id):
    """Detalle completo de una venta con todos los campos."""
    venta = get_object_or_404(Venta.objects.prefetch_related('items'), id=venta_id)
    
    # Información completa según método de entrega
    info_entrega = {}
    if venta.metodo_entrega == 'envio':
        info_entrega = {
            'tipo': 'Envío a domicilio',
            'direccion': venta.direccion,
            'ciudad': venta.ciudad,
            'region': venta.region,
            'empresa_envio': venta.empresa_envio
        }
    elif venta.metodo_entrega == 'retiro':
        info_entrega = {
            'tipo': 'Retiro en tienda',
            'rut': venta.rut
        }
    elif venta.metodo_entrega == 'sucursal':
        info_entrega = {
            'tipo': 'Envío a sucursal',
            'direccion': venta.direccion,
            'ciudad': venta.ciudad,
            'region': venta.region,
            'empresa_envio': venta.empresa_envio
        }
    
    context = {
        'venta': venta,
        'items': venta.items.all(),
        'info_entrega': info_entrega,
    }
    
    return render(request, 'adminpanel/detalle_venta.html', context)

@user_passes_test(lambda u: u.is_staff)
def cambiar_estado_venta(request, venta_id):
    """Cambiar el estado de una venta"""
    if request.method == 'POST':
        venta = get_object_or_404(Venta, id=venta_id)
        nuevo_estado = request.POST.get('estado')
        
        if nuevo_estado in dict(Venta.ESTADOS_PAGO):
            venta.estado = nuevo_estado
            
            # Si se aprueba, marcar como pagado
            if nuevo_estado == 'aprobado':
                venta.pagado = True
            else:
                venta.pagado = False
                
            venta.save()
            
        return redirect('detalle_venta', venta_id=venta_id)
    
    return redirect('panel_ventas')