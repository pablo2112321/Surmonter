# En categoriasApp/urls.py
from django.urls import path
from . import views

app_name = 'categoriasApp'

urlpatterns = [
    path('lista/', views.lista_categorias, name='lista_categorias'),
    path('crear/', views.crear_categoria, name='crear_categoria'),
    path('editar/<int:categoria_id>/', views.editar_categoria, name='editar_categoria'),
    path('eliminar/<int:categoria_id>/', views.eliminar_categoria, name='eliminar_categoria'),
    path('ordenar/', views.ordenar_categorias, name='ordenar_categorias'),
    path('actualizar-posicion/', views.actualizar_posicion_categoria, name='actualizar_posicion_categoria'),
    path('invalidate-cache/', views.invalidate_menu_cache, name='invalidate_menu_cache'),
    path('<str:nombre_categoria>/', views.mostrar_categoria, name='mostrar_categoria'),
]