from django.http import HttpResponse
from django.shortcuts import render, redirect
from ingresarApp.models import VarianteTalla, Producto
from .models import Venta, VentaItem
from django.conf import settings
import mercadopago
import random
import json

# Configuración del SDK de MercadoPago
sdk = mercadopago.SDK(
    settings.MERCADOPAGO_TOKEN_PRODUCCION if settings.MERCADOPAGO_USAR_PRODUCCION
    else settings.MERCADOPAGO_TOKEN_SANDBOX
)


# 🧾 Vista para preparar el pago y generar preferencia
from django.shortcuts import redirect

def preparar_pago(request):
    carrito = request.session.get('carrito', {})
    if not carrito:
        return render(request, 'pago/error.html', {'mensaje': 'Tu carrito está vacío.'})

    items = []
    total = 0

    for item in carrito.values():
        producto_id = item.get('id')
        if not producto_id:
            continue

        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            continue

        cantidad = item.get('cantidad', 1)
        precio_unitario = float(producto.precio)
        items.append({
            "title": producto.nombre,
            "quantity": cantidad,
            "unit_price": precio_unitario,
            "currency_id": "CLP"
        })
        total += precio_unitario * cantidad

    base_url = "https://surmontertienda.cl"

    back_urls = {
        "success": f"{base_url}/pago/exito/",
        "failure": f"{base_url}/pago/fallo/",
        "pending": f"{base_url}/pago/pendiente/"
    }

    preference_data = {
        "items": items,
        "back_urls": back_urls,
        "auto_return": "approved",
        "payer": {
            "email": "test_user_263913646@testuser.com"
        }
    }

    preference = sdk.preference().create(preference_data)

    print("🔗 back_urls:", back_urls)
    print("✅ LINK PARA PAGAR:", preference["response"]["init_point"])

    if preference.get("status") == 201:
        url_checkout = (
        preference["response"]["init_point"]
        if settings.MERCADOPAGO_USAR_PRODUCCION
        else preference["response"]["sandbox_init_point"]
    )
        return redirect(url_checkout)


    else:
        mensaje_error = preference.get("response", {}).get("message", "Error inesperado al conectar con MercadoPago.")
        return render(request, "pago/error.html", {
            "mensaje": f"No se pudo generar la preferencia de pago: {mensaje_error}"
        })
    

# 💳 Vista que se ejecuta al retornar de MercadoPago
def pago_exito(request):
    payment_id = request.GET.get("payment_id")
    if not payment_id:
        return render(request, "pago/error.html", {"mensaje": "No se recibió el ID del pago."})

    try:
        respuesta = sdk.payment().get(payment_id)
        print("📦 Respuesta completa de MercadoPago:", respuesta)

        payment_info = respuesta.get("response", {})
        status = payment_info.get("status")

        if status != "approved":
            return render(request, "pago/error.html", {"mensaje": f"Pago no aprobado. Estado: {status}"})

        carrito = request.session.get("carrito", {})
        if not carrito:
            return render(request, "pago/error.html", {"mensaje": "Carrito vacío después del pago."})

        metodo = request.session.get("metodo_entrega", "retiro")
        total = sum(item['precio'] * item['cantidad'] for item in carrito.values())

        # Crear la venta con todos los campos posibles desde la sesión
        venta = Venta.objects.create(
            nombre=request.session.get("nombre_cliente", ""),
            apellido=request.session.get("apellido", ""),  # debes agregar esto también al procesar_compra si lo quieres mostrar
            email=payment_info.get("payer", {}).get("email") or request.session.get("email", ""),
            telefono=request.session.get("telefono", ""),
            direccion=request.session.get("direccion", ""),
            ciudad=request.session.get("ciudad", ""),
            region=request.session.get("region", ""),
            rut=request.session.get("rut", ""),
            empresa_envio=request.session.get("empresa_envio", ""),
            metodo_entrega=metodo,
            total=total,
            pagado=True,
            payment_id=payment_info.get("id")
        )

        for item in carrito.values():
            VentaItem.objects.create(
                venta=venta,
                producto_nombre=item.get('nombre'),
                talla=item.get('talla'),
                cantidad=item.get('cantidad'),
                precio_unitario=item.get('precio')
            )

            # Actualiza el stock
            producto_id = item.get('id')
            if producto_id:
                try:
                    variante = VarianteTalla.objects.get(producto_id=producto_id, talla=item.get('talla'))
                    variante.stock = max(variante.stock - item.get('cantidad', 1), 0)
                    variante.save()
                except VarianteTalla.DoesNotExist:
                    print(f"No se encontró variante para {item.get('nombre')}")

        # Limpiar la sesión
        request.session['carrito'] = {}
        request.session['direccion'] = ''
        request.session['ciudad'] = ''
        request.session['region'] = ''
        request.session['nombre_cliente'] = ''
        request.session['apellido'] = ''
        request.session['telefono'] = ''
        request.session['email'] = ''
        request.session['empresa_envio'] = ''
        request.session['rut'] = ''
        request.session['metodo_entrega'] = ''

        return render(request, 'pago/confirmacion.html', {'venta': venta})

    except Exception as e:
        print("❌ Error al procesar el pago:", str(e))
        return render(request, "pago/error.html", {"mensaje": f"Error al obtener los datos del pago: {str(e)}"})

# 🛑 Si el pago falla
def pago_fallo(request):
    return render(request, "pago/error.html", {"mensaje": "El pago fue rechazado o cancelado."})

# 🕗 Si el pago está en revisión
def pago_pendiente(request):
    return render(request, "pago/error.html", {"mensaje": "El pago está en revisión por MercadoPago."})

# 📋 Panel administrativo de ventas
def panel_admin(request):
    accion = request.GET.get('accion')
    bloque = accion if accion else None

    if accion == 'ventas':
        ventas = Venta.objects.prefetch_related('items').order_by('-fecha')
        return render(request, 'adminpanel/paneladmin.html', {
            'bloque': 'ventas',
            'ventas': ventas
        })

# 🧾 Procesar compra antes del pago
def procesar_compra(request):
    if request.method == 'POST':
        request.session['metodo_entrega'] = request.POST.get('metodo_entrega')
        request.session['direccion'] = request.POST.get('direccion', '')
        request.session['ciudad'] = request.POST.get('ciudad', '')
        request.session['region'] = request.POST.get('region', '')
        request.session['nombre_cliente'] = request.POST.get('nombre', '') or request.POST.get('nombre_retiro', '')
        request.session['email'] = request.POST.get('email', '') or request.POST.get('email_retiro', '')
        request.session['telefono'] = request.POST.get('telefono', '') or request.POST.get('telefono_retiro', '')
        request.session['rut'] = request.POST.get('rut', '')
        request.session['empresa_envio'] = request.POST.get('empresa_envio', '')
        request.session['apellido'] = request.POST.get('apellido', '') or request.POST.get('apellido_retiro', '')
        return redirect('preparar_pago')
    return HttpResponse("Método no permitido", status=405)
