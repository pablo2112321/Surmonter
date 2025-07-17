from django.db import models

# Create your models here.
class Usuario(models.Model):
    nombre = models.CharField(max_length=50, null=False, blank=False)
    apellido = models.CharField(max_length=50, null=False, blank=False)
    email = models.EmailField(null=False, blank=False)
    telefono = models.IntegerField(null=False, blank=False)
    