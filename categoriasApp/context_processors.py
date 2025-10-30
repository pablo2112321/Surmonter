# categoriasApp/context_processors.py
from .models import Categoria

def menu_categorias(request):
    categorias_principales = Categoria.objects.filter(
        padre__isnull=True, 
        activa=True
    ).order_by('posicion', 'nombre')
    
    # Para cada categoría principal, obtener sus subcategorías ordenadas
    categorias_con_sub = []
    for categoria in categorias_principales:
        categoria.subcategorias_ordenadas = categoria.subcategorias.filter(
            activa=True
        ).order_by('posicion', 'nombre')
        categorias_con_sub.append(categoria)
    
    return {
        'menu_categorias': categorias_con_sub
    }