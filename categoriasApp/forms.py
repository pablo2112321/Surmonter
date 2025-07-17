from django import forms
from .models import Categoria

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'padre']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar categorías que no tengan padre (= categorías raíz)
        self.fields['padre'].queryset = Categoria.objects.filter(padre__isnull=True)
