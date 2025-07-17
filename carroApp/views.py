from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from ingresarApp.models import Producto

def Carro(request):
    carrito_sesion = request.session.get('carrito', {})
    carrito = []
    total = 0

    for key, item in carrito_sesion.items():
        try:
            producto_id = key.split('-')[0]  # Extraemos solo el ID
            producto = Producto.objects.get(pk=int(producto_id))
        except Producto.DoesNotExist:
            continue

        cantidad = item.get('cantidad', 1)
        talla = item.get('talla', 'Sin talla')
        precio_unitario = item.get('precio', 0)
        subtotal = precio_unitario * cantidad
        total += subtotal

        carrito.append({
    'id': producto.id, 
    'key': key,
    'producto': producto,
    'cantidad': cantidad,
    'talla': talla,
    'subtotal': subtotal,
})


    context = {
        'carrito': carrito,
        'total': total,
    }
    return render(request, 'pago/Carro.html', context)


def eliminar_item(request, key):
    carrito = request.session.get('carrito', {})
    if key in carrito:
        del carrito[key]
        request.session['carrito'] = carrito
    return redirect('ver_carrito')

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from ingresarApp.models import Producto

def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    carrito = request.session.get('carrito', {})
    talla = request.POST.get('talla', '')
    key = f"{producto.id}-{talla}"

    if key in carrito:
        carrito[key]['cantidad'] += 1
    else:
        carrito[key] = {
            'id': producto.id,
            'nombre': producto.nombre,
            'precio': int(producto.precio),
            'cantidad': 1,
            'talla': talla,
        }

    request.session['carrito'] = carrito

    total_items = sum(item['cantidad'] for item in carrito.values())

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'nombre': producto.nombre,
            'talla': talla,
            'carrito_total_items': total_items
        })

    messages.success(request, f"{producto.nombre} agregado al carrito.")
    return redirect('ver_carrito')

# views.py
from django.http import JsonResponse

def contador_carrito(request):
    carrito = request.session.get('carrito', {})
    total_items = sum(item['cantidad'] for item in carrito.values())
    return JsonResponse({'total': total_items})
