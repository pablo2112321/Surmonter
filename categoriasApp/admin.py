# categoriasApp/admin.py
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from .models import Categoria

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'padre', 'posicion', 'activa', 'tipo_categoria']
    list_editable = ['posicion', 'activa']
    list_filter = ['padre', 'activa']
    search_fields = ['nombre']
    ordering = ['padre', 'posicion']
    
    def tipo_categoria(self, obj):
        return "Principal" if obj.padre is None else f"Subcategoría de {obj.padre.nombre}"
    tipo_categoria.short_description = 'Tipo'