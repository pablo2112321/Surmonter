from django.contrib import admin
from .models import Producto, VarianteTalla

class VarianteTallaInline(admin.TabularInline):
    model = VarianteTalla
    extra = 1
    min_num = 1
    verbose_name = "Talla disponible"
    verbose_name_plural = "Tallas disponibles"

class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio')
    inlines = [VarianteTallaInline]  # Esta línea es clave

admin.site.register(Producto, ProductoAdmin)
