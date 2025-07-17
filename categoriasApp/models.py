from django.db import models

# Create your models here.

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    padre = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subcategorias')

    def __str__(self):
        return self.nombre
