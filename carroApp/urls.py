from django.urls import path
from . import views

urlpatterns = [
    path('carrito/', views.Carro, name='ver_carrito'),
    path('carrito/eliminar/<str:key>/', views.eliminar_item, name='eliminar_item'),
    path('carrito/agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    #path('procesar/', views.procesar_compra, name='procesar_compra'),
    path('carrito/contador/', views.contador_carrito, name='contador_carrito'),

]
