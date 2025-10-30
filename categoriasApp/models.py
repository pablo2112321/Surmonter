# categoriasApp/models.py
from django.db import models

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    padre = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subcategorias')
    posicion = models.IntegerField(default=0, help_text="Posición para ordenar (menor número = primero)")
    activa = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['posicion', 'nombre']
    
    def __str__(self):
        return self.nombre
    
    @property
    def es_categoria_principal(self):
        return self.padre is None
    
    @property
    def es_subcategoria(self):
        return self.padre is not None
    
    def get_subcategorias_activas(self):
        return self.subcategorias.filter(activa=True).order_by('posicion', 'nombre')
    
    class Meta:
        ordering = ['posicion']