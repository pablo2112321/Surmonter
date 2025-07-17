from django.urls import path
from .views import buscar_productos, mostrar_producto

urlpatterns = [
    path('buscar/', buscar_productos, name='buscar_productos'),
    path('producto/<int:id>/', mostrar_producto, name='mostrar_producto'),
    
]
