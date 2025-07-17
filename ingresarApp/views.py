from django.shortcuts import render, redirect, get_object_or_404

from categoriasApp.forms import CategoriaForm
from .models import Producto, VarianteTalla
from pagoApp.models import Venta 
from .forms import ProductoForm, VarianteTallaFormSet

from django import forms
from .models import Categoria

def paneladmin(request):
    productos = Producto.objects.all()
    contexto = {'productos': productos}

    accion = request.GET.get('accion')
    producto_id = request.GET.get('id')

    if accion == 'agregar':
        form = ProductoForm(request.POST or None, request.FILES or None)
        formset = VarianteTallaFormSet(request.POST or None)
        if request.method == 'POST' and form.is_valid() and formset.is_valid():
            producto = form.save()
            formset.instance = producto
            formset.save()
            return redirect('panel_admin')
        contexto.update({'form': form, 'formset': formset, 'bloque': 'agregar'})

    elif accion == 'editar' and producto_id:
        producto = get_object_or_404(Producto, id=producto_id)
        form = ProductoForm(request.POST or None, request.FILES or None, instance=producto)
        formset = VarianteTallaFormSet(request.POST or None, instance=producto)
        if request.method == 'POST' and form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('panel_admin')
        contexto.update({'form': form, 'formset': formset, 'producto': producto, 'bloque': 'editar'})

    elif accion == 'eliminar' and producto_id:
        producto = get_object_or_404(Producto, id=producto_id)
        if request.method == 'POST':
            producto.delete()
            return redirect('panel_admin')
        contexto.update({'producto': producto, 'bloque': 'eliminar'})

    elif accion == 'ventas': 
        ventas = Venta.objects.prefetch_related('items').order_by('-fecha')
        contexto.update({'ventas': ventas, 'bloque': 'ventas'})



    elif accion == 'categoria':
        form = CategoriaForm(request.POST or None)
        categorias = Categoria.objects.select_related('padre').order_by('padre__nombre', 'nombre')
        if request.method == 'POST' and form.is_valid():
            form.save()
            return redirect('panel_admin')  # volver al panel después de guardar
        contexto.update({'form': form, 'categorias': categorias, 'bloque': 'categoria'})


    elif accion == 'editarcat' and producto_id:
        categoria = get_object_or_404(Categoria, id=producto_id)
        form = CategoriaForm(request.POST or None, instance=categoria)
        if request.method == 'POST' and form.is_valid():
            form.save()
            return redirect('panel_admin')
        contexto.update({'form': form, 'categoria': categoria, 'bloque': 'editarcat'})

    elif accion == 'eliminarcat' and producto_id:
        categoria = get_object_or_404(Categoria, id=producto_id)
        if request.method == 'POST':
            categoria.delete()
            return redirect('panel_admin')
        contexto.update({'categoria': categoria, 'bloque': 'eliminarcat'})
    return render(request, 'adminpanel/paneladmin.html', contexto)


