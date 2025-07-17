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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        categorias = Producto._meta.get_field('categoria').related_model.objects.all().order_by('padre__nombre', 'nombre')
        opciones = []
        for cat in categorias:
            if not cat.padre:
                opciones.append((cat.id, cat.nombre))
                subcats = categorias.filter(padre=cat)
                for sub in subcats:
                    opciones.append((sub.id, f'— {sub.nombre}'))
        self.fields['categoria'].choices = opciones


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
