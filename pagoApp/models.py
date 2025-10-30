from django.db import models
from ingresarApp.models import Producto

class Venta(models.Model):
    METODOS_ENTREGA = [
        ('retiro', 'Retiro en tienda'),
        ('envio', 'Envío a domicilio'),
        ('sucursal', 'Entrega en sucursal'),
    ]
    
    ESTADOS_PAGO = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('cancelado', 'Cancelado'),
        ('en_proceso', 'En proceso'),
    ]

    metodo_entrega = models.CharField(max_length=20, choices=METODOS_ENTREGA)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=50, blank=True, null=True)
    rut = models.CharField(max_length=20, blank=True, null=True)
    origen = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    empresa_envio = models.CharField(max_length=100, blank=True, null=True)

    total = models.PositiveIntegerField(default=0)
    pagado = models.BooleanField(default=False)
    estado = models.CharField(max_length=20, choices=ESTADOS_PAGO, default="pendiente")
    fecha = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    metodo_pago = models.CharField(max_length=50, blank=True, null=True)
    fecha_pago = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Venta #{self.id} - {self.nombre} {self.apellido}"

    @property
    def estado_display(self):
        """Devuelve el estado con iconos"""
        estados_iconos = {
            'aprobado': '✅ Aprobado',
            'rechazado': '❌ Rechazado', 
            'pendiente': '⏳ Pendiente',
            'cancelado': '🚫 Cancelado',
            'en_proceso': '🔄 En proceso'
        }
        return estados_iconos.get(self.estado, self.estado)

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def get_empresa_envio_display(self):
        """Muestra los nombres correctos de las empresas de envío"""
        if not self.empresa_envio:
            return "No especificada"
            
        nombres_corregidos = {
            'starken': 'Starken',
            'cacem': 'Cacem Express',  # Corregido aquí
            'aboraico': 'Transportes Aboraico',
            'local': 'Envío Local Valdivia'
        }
        return nombres_corregidos.get(self.empresa_envio, self.empresa_envio)

class VentaItem(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    talla = models.CharField(max_length=50, blank=True, null=True)
    cantidad = models.PositiveIntegerField(default=1)
    precio = models.PositiveIntegerField(default=0)

    @property
    def producto_nombre(self):
        return self.producto.nombre

    @property
    def precio_unitario(self):
        return self.precio

    @property
    def subtotal(self):
        return self.precio * self.cantidad