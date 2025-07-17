from django.db import models

class Venta(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, blank=True)  # opcional
    email = models.EmailField()
    telefono = models.CharField(max_length=15)
    
    direccion = models.TextField(blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    
    rut = models.CharField(max_length=20, blank=True)
    
    metodo_entrega = models.CharField(
        max_length=20,
        choices=[
            ('retiro', 'Retiro en tienda'),
            ('envio', 'Envío a domicilio')
        ]
    )
    empresa_envio = models.CharField(max_length=50, blank=True, null=True)

    total = models.PositiveIntegerField()
    pagado = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    # Campo opcional para guardar el ID del pago de MercadoPago
    payment_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Venta #{self.id} - {self.nombre} {self.apellido} - ${self.total}"


class VentaItem(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='items')
    producto_nombre = models.CharField(max_length=200)
    talla = models.CharField(max_length=20)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.PositiveIntegerField()

    def subtotal(self):
        return self.precio_unitario * self.cantidad
