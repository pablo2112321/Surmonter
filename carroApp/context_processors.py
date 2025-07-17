def carrito_total(request):
    carrito = request.session.get('carrito', {})
    total_productos = sum(item.get('cantidad', 0) for item in carrito.values())
    return {'carrito_total_items': total_productos}
