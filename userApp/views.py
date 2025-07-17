from django.shortcuts import render

# Create your views here.
def Usuario(request):
    return render(request, 'usuario/usuario.html')