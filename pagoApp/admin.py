from django.contrib import admin
from .models import Venta, VentaItem

class VentaItemInline(admin.TabularInline):
    model = VentaItem
    extra = 0
    readonly_fields = ('producto_nombre', 'talla', 'cantidad', 'precio_unitario')

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'apellido', 'metodo_entrega', 'pagado', 'total', 'fecha')
    list_filter = ('pagado', 'metodo_entrega', 'fecha')
    search_fields = ('nombre', 'apellido', 'email', 'rut')
    inlines = [VentaItemInline]
