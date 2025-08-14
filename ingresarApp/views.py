from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseRedirect
from django.urls import reverse

from categoriasApp.forms import CategoriaForm
from .models import Producto, VarianteTalla, Categoria
from pagoApp.models import Venta
from .forms import ProductoForm, VarianteTallaFormSet

def es_admin(user):
    return user.is_authenticated and user.is_staff

def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('panel_admin')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect('panel_admin')
        else:
            messages.error(request, 'Credenciales inválidas o sin permisos de administrador.')

    return render(request, 'adminpanel/admin_login.html')

def admin_logout(request):
    logout(request)
    messages.success(request, "Sesión cerrada con éxito.")
    return redirect('Inicio')  # Cambia 'Inicio' si tu URL principal tiene otro nombre

@user_passes_test(es_admin, login_url='/admin-login/')
def paneladmin(request):
    productos = Producto.objects.all()
    categorias_qs = Categoria.objects.select_related('padre').order_by('padre__nombre', 'nombre')
    categorias = list(categorias_qs)
    ventas = Venta.objects.prefetch_related('items').order_by('-fecha')

    # Session para orden
    orden_principal = request.session.get('orden_categorias', [c.id for c in categorias if c.padre is None])
    orden_sub = request.session.get('orden_subcategorias', {})

    accion = request.GET.get('accion')
    producto_id = request.GET.get('id')

    # Manejo mover categorías/subcategorías
    if accion == 'mover':
        mover_id = request.GET.get('mover_id')
        direccion = request.GET.get('direccion')  # 'up' o 'down'

        if mover_id and direccion in ['up', 'down']:
            mover_id = int(mover_id)
            mover_cat = next((c for c in categorias if c.id == mover_id), None)
            if mover_cat:
                if mover_cat.padre is None:
                    # Categoria principal
                    if mover_id in orden_principal:
                        idx = orden_principal.index(mover_id)
                        if direccion == 'up' and idx > 0:
                            orden_principal[idx], orden_principal[idx-1] = orden_principal[idx-1], orden_principal[idx]
                        elif direccion == 'down' and idx < len(orden_principal)-1:
                            orden_principal[idx], orden_principal[idx+1] = orden_principal[idx+1], orden_principal[idx]
                        request.session['orden_categorias'] = orden_principal
                else:
                    # Subcategoria
                    padre_id = mover_cat.padre.id
                    if str(padre_id) not in orden_sub:
                        orden_sub[str(padre_id)] = [c.id for c in categorias if c.padre and c.padre.id == padre_id]
                    sub_orden = orden_sub[str(padre_id)]
                    if mover_id in sub_orden:
                        idx = sub_orden.index(mover_id)
                        if direccion == 'up' and idx > 0:
                            sub_orden[idx], sub_orden[idx-1] = sub_orden[idx-1], sub_orden[idx]
                        elif direccion == 'down' and idx < len(sub_orden)-1:
                            sub_orden[idx], sub_orden[idx+1] = sub_orden[idx+1], sub_orden[idx]
                        orden_sub[str(padre_id)] = sub_orden
                        request.session['orden_subcategorias'] = orden_sub

            return HttpResponseRedirect(reverse('panel_admin') + '?accion=categoria')

    # Ordenar categorias para mostrar
    categorias_principales = [c for id_c in orden_principal for c in categorias if c.id == id_c]

    for cat in categorias_principales:
        subs = [c for c in categorias if c.padre and c.padre.id == cat.id]
        sub_orden = orden_sub.get(str(cat.id), [s.id for s in subs])
        cat.subcategorias_ordenadas = [s for id_s in sub_orden for s in subs if s.id == id_s]

    contexto = {'productos': productos, 'ventas': ventas, 'bloque': accion or ''}

    # Manejo de bloques
    if accion == 'agregar':
        form = ProductoForm(request.POST or None, request.FILES or None)
        formset = VarianteTallaFormSet(request.POST or None)
        if request.method == 'POST' and form.is_valid() and formset.is_valid():
            producto = form.save()
            formset.instance = producto
            formset.save()
            return redirect('panel_admin')
        contexto.update({'form': form, 'formset': formset, 'bloque': 'agregar'})

    elif accion == 'editar' and producto_id:
        producto = get_object_or_404(Producto, id=producto_id)
        form = ProductoForm(request.POST or None, request.FILES or None, instance=producto)
        formset = VarianteTallaFormSet(request.POST or None, instance=producto)
        if request.method == 'POST' and form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('panel_admin')
        contexto.update({'form': form, 'formset': formset, 'producto': producto, 'bloque': 'editar'})

    elif accion == 'eliminar' and producto_id:
        producto = get_object_or_404(Producto, id=producto_id)
        if request.method == 'POST':
            producto.delete()
            return redirect('panel_admin')
        contexto.update({'producto': producto, 'bloque': 'eliminar'})

    elif accion == 'ventas':
        contexto.update({'ventas': ventas, 'bloque': 'ventas'})

    elif accion == 'categoria':
        form = CategoriaForm(request.POST or None)
        if request.method == 'POST' and form.is_valid():
            form.save()
            return redirect('panel_admin')
        contexto.update({'form': form, 'categorias': categorias_principales, 'bloque': 'categoria'})

    elif accion == 'editarcat' and producto_id:
        categoria = get_object_or_404(Categoria, id=producto_id)
        form = CategoriaForm(request.POST or None, instance=categoria)
        if request.method == 'POST' and form.is_valid():
            form.save()
            return redirect('panel_admin')
        contexto.update({'form': form, 'categoria': categoria, 'bloque': 'editarcat'})

    elif accion == 'eliminarcat' and producto_id:
        categoria = get_object_or_404(Categoria, id=producto_id)
        if request.method == 'POST':
            categoria.delete()
            return redirect('panel_admin')
        contexto.update({'categoria': categoria, 'bloque': 'eliminarcat'})

    return render(request, 'adminpanel/paneladmin.html', contexto)
