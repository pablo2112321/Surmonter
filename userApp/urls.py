from django.urls import path
from . import views

urlpatterns = [
    path('usuario/', views.Usuario, name='usuario' )
]