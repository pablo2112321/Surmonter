from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from django.urls import reverse
from ingresarApp.models import Producto
from django.shortcuts import render, get_object_or_404

def buscar_productos(request):
    query = request.GET.get('q', '').strip()
    if query:
        productos = Producto.objects.filter(nombre__icontains=query)[:10]
        data = [{
            'nombre': p.nombre,
            'imagen': p.imagen.url,
            'url': reverse('mostrar_producto', args=[p.id])  # 🧠 usa el nombre de la vista
        } for p in productos]
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)


def mostrar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    return render(request, 'producto.html', {'producto': producto})

