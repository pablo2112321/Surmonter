from django.urls import path
from categoriasApp.views import mostrar_categoria
from categoriasApp.views import crear_categoria

app_name = 'categoriasApp'

urlpatterns = [
    path('lista/', views.lista_categorias, name='lista_categorias'),
    path('crear/', views.crear_categoria, name='crear_categoria'),
    path('editar/<int:categoria_id>/', views.editar_categoria, name='editar_categoria'),
    path('eliminar/<int:categoria_id>/', views.eliminar_categoria, name='eliminar_categoria'),
]