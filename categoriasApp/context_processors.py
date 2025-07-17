from .models import Categoria

def menu_categorias(request):
    categorias = Categoria.objects.filter(padre__isnull=True)
    return {'menu_categorias': categorias}
