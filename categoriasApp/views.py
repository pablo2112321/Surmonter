from django.shortcuts import get_object_or_404, redirect, render
from categoriasApp.models import Categoria
from ingresarApp.models import Producto
from django.contrib import messages
from .models import Categoria
from .forms import CategoriaForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.db import transaction
import time
from django.db.models import Q  

# Función helper para obtener categorías con cache
def obtener_menu_categorias():
    """Obtiene el menú de categorías desde cache o BD"""
    cache_key = 'menu_categorias'
    menu_categorias = cache.get(cache_key)
    
    if not menu_categorias:
        # Cache miss - cargar desde BD
        menu_categorias = Categoria.objects.filter(
            padre__isnull=True,
            activa=True  # ✅ Solo categorías activas
        ).prefetch_related('subcategorias').order_by('posicion')
        
        # Guardar en cache por 10 minutos
        cache.set(cache_key, menu_categorias, 60 * 10)
        print("🔄 Categorías cargadas desde BD y guardadas en cache")
    
    return menu_categorias

@csrf_exempt
def invalidate_menu_cache(request):
    """Invalidar cache del menú cuando se actualizan categorías"""
    if request.method == 'POST':
        try:
            # Invalidar cache del menú
            cache.delete('menu_categorias')
            cache.delete('header_categorias')
            
            return JsonResponse({'status': 'success', 'message': 'Cache invalidado'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error'}, status=405)

@cache_page(60 * 5)
def mostrar_categoria(request, nombre_categoria):
    """Vista para mostrar productos de una categoría específica Y sus subcategorías"""
    # ✅ Filtro corregido con activa=True
    categoria = get_object_or_404(Categoria, nombre=nombre_categoria, activa=True)
    
    # ✅ Obtener IDs de todas las subcategorías activas
    subcategorias_ids = categoria.subcategorias.filter(activa=True).values_list('id', flat=True)
    
    # ✅ Obtener productos de la categoría principal Y de sus subcategorías
    productos = Producto.objects.filter(
        activo=True
    ).filter(
        Q(categoria=categoria) |  # Productos de la categoría principal
        Q(categoria_id__in=subcategorias_ids)  # Productos de las subcategorías
    ).distinct()  # Evitar duplicados
    
    # Obtener menú de categorías para el header
    menu_categorias = obtener_menu_categorias()
    
    return render(request, 'categorias/generica.html', {
        'categoria': categoria,
        'productos': productos,
        'subcategorias': categoria.subcategorias.filter(activa=True),
        'menu_categorias': menu_categorias
    })

def lista_categorias(request):
    """Vista para listar todas las categorías (admin)"""
    categorias = Categoria.objects.all().order_by('nombre')
    return render(request, 'categorias/lista_categorias.html', {'categorias': categorias})

def crear_categoria(request):
    """Crear nueva categoría"""
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            
            # Limpiar cache después de crear
            cache.delete('menu_categorias')
            cache.delete('header_categorias')
            
            messages.success(request, '¡Categoría creada exitosamente!')
            return redirect('categoriasApp:lista_categorias')
        else:
            messages.error(request, '¡Error al crear la categoría! Revise los datos.')
    else:
        form = CategoriaForm()
    
    return render(request, 'categorias/crear_categoria.html', {'form': form})

def editar_categoria(request, categoria_id):
    """Editar categoría existente"""
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            
            # Limpiar cache después de editar
            cache.delete('menu_categorias')
            cache.delete('header_categorias')
            
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
    """Eliminar categoría"""
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    
    if request.method == 'POST':
        categoria.delete()
        
        # Limpiar cache después de eliminar
        cache.delete('menu_categorias')
        cache.delete('header_categorias')
        
        messages.success(request, '¡Categoría eliminada exitosamente!')
        return redirect('categoriasApp:lista_categorias')
    
    return render(request, 'categorias/eliminar_categoria.html', {'categoria': categoria})

def ordenar_categorias(request):
    """Vista para ordenar categorías con drag & drop"""
    # ✅ Filtro corregido con activa=True
    categorias_principales = Categoria.objects.filter(
        padre__isnull=True,
        activa=True
    ).order_by('posicion').prefetch_related('subcategorias')
    
    # Calcular total de subcategorías
    total_subcategorias = 0
    for categoria in categorias_principales:
        total_subcategorias += categoria.subcategorias.filter(activa=True).count()
    
    return render(request, 'categorias/ordenar_categorias.html', {
        'categorias_principales': categorias_principales,
        'total_subcategorias': total_subcategorias,
    })

@csrf_exempt
@transaction.atomic
def actualizar_posicion_categoria(request):
    """API para actualizar posición de categorías (AJAX) - OPTIMIZADA PARA PRODUCCIÓN"""
    if request.method == 'POST':
        try:
            categoria_id = request.POST.get('categoria_id')
            nueva_posicion = request.POST.get('nueva_posicion')
            padre_id = request.POST.get('padre_id')
            
            print(f"🔄 Actualizando categoría {categoria_id} a posición {nueva_posicion}, padre: {padre_id}")
            
            categoria = Categoria.objects.get(id=categoria_id)
            categoria.posicion = nueva_posicion
            
            if padre_id and padre_id != 'null':
                categoria.padre_id = padre_id
            elif padre_id == 'null':
                categoria.padre = None
            
            categoria.save()
            
            # 🔥 LIMPIAR CACHE DESPUÉS DE GUARDAR CAMBIOS - PRODUCCIÓN
            start_time = time.time()
            cache_keys_to_delete = [
                'menu_categorias',
                'header_categorias', 
                'categorias_principales',
            ]
            
            for key in cache_keys_to_delete:
                cache.delete(key)
            
            end_time = time.time()
            print(f"✅ Cache limpiado en {end_time - start_time:.2f} segundos")
            
            return JsonResponse({
                'success': True, 
                'message': 'Posición actualizada correctamente',
                'cache_cleared': True
            })
            
        except Categoria.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'error': 'Categoría no encontrada'
            })
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False, 
        'error': 'Método no permitido'
    })