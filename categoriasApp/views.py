from django.shortcuts import get_object_or_404, redirect, render
from categoriasApp.models import Categoria
from ingresarApp.models import Producto
from django.contrib import messages
from .models import Categoria
from .forms import CategoriaForm  # lo definimos ahora

# Create your views here.


def mostrar_categoria(request, nombre_categoria):
    categoria = get_object_or_404(Categoria, nombre=nombre_categoria)
    productos = Producto.objects.filter(categoria=categoria)
    return render(request, 'categorias/generica.html', {
        'categoria': categoria,
        'productos': productos,
        'subcategorias': categoria.subcategorias.all()
    })

def lista_categorias(request):
    categorias = Categoria.objects.all().order_by('nombre')
    return render(request, 'categorias/lista_categorias.html', {'categorias': categorias})

def crear_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Categoría creada exitosamente!')
            return redirect('categoriasApp:lista_categorias')
        else:
            messages.error(request, '¡Error al crear la categoría! Revise los datos.')
    else:
        form = CategoriaForm()
    
    return render(request, 'categorias/crear_categoria.html', {'form': form})

def editar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Categoría actualizada exitosamente!')
            return redirect('categoriasApp:lista_categorias')
        else:
            messages.error(request, '¡Error al actualizar! Revise los datos.')
    else:
        form = CategoriaForm(instance=categoria)
    
    return render(request, 'categorias/editar_categoria.html', {
        'form': form,
        'categoria': categoria
    })

def eliminar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    
    if request.method == 'POST':
        categoria.delete()
        messages.success(request, '¡Categoría eliminada exitosamente!')
        return redirect('categoriasApp:lista_categorias')
    
    return render(request, 'categorias/eliminar_categoria.html', {'categoria': categoria})