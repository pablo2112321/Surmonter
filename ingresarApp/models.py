from django.db import models


from categoriasApp.models import Categoria  # actualiza el nombre si cambiaste el modelo


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    imagen = models.ImageField(upload_to='productos/')
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre
    
class VarianteTalla(models.Model):
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE, related_name='variantes')
    talla = models.CharField(max_length=5)
    stock = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.producto.nombre} - Talla {self.talla}"
