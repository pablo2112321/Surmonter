from django import forms
from .models import Producto, VarianteTalla
from django.forms.models import inlineformset_factory

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio': forms.NumberInput(attrs={'class': 'form-control'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'talla': forms.TextInput(attrs={'class': 'form-control'}), 
        }


VarianteTallaFormSet = inlineformset_factory(
    Producto,
    VarianteTalla,
    fields=('talla', 'stock'),
    widgets={
        'talla': forms.TextInput(attrs={'class': 'form-control'}),
        'stock': forms.NumberInput(attrs={'class': 'form-control'}),
    },
    extra=1,
    can_delete=True
)
