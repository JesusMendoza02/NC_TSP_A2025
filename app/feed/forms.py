from django import forms
from django.forms import ClearableFileInput
from .models import Resena

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class FormResena(forms.ModelForm):
    # Campo extra para las fotografías
    fotografias = MultipleFileField(
        required=False,
        label='Fotografías (máximo 3)',
        widget=MultipleFileInput(attrs={
            'accept': 'image/*',
            'class': 'form-control'
        })
    )
    
    # Campo extra para saber si está actualmente en el lugar
    actualmente_en_lugar = forms.ChoiceField(
        choices=[('si', 'Sí'), ('no', 'No')],
        widget=forms.RadioSelect,
        initial='si',
        label='¿Actualmente en el lugar?'
    )
    
    # Campo condicional para fecha/hora manual
    fecha_visita_manual = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        }),
        label='Fecha y hora de visita'
    )

    class Meta:
        model = Resena
        fields = ['lugar_turistico', 'descripcion', 'calificacion']

        widgets = {
            'lugar_turistico': forms.Select(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Escribe tu experiencia...'
            }),
            'calificacion': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 1, 
                'max': 10, 
                'placeholder': '1 a 10'
            }),
        }

        labels = {
            'lugar_turistico': 'Lugar turístico',
            'descripcion': 'Descripción de la visita',
            'calificacion': 'Calificación (1-10)',
        }

    def clean_calificacion(self):
        calificacion = self.cleaned_data.get('calificacion')
        if calificacion and (calificacion < 1 or calificacion > 10):
            raise forms.ValidationError("La calificación debe estar entre 1 y 10.")
        return calificacion
    
    def clean(self):
        cleaned_data = super().clean()
        actualmente = cleaned_data.get('actualmente_en_lugar')
        fecha_manual = cleaned_data.get('fecha_visita_manual')
        
        # Validar que si NO está actualmente, debe proporcionar fecha
        if actualmente == 'no' and not fecha_manual:
            self.add_error('fecha_visita_manual', 
                          'Debes proporcionar la fecha y hora de tu visita.')
        
        return cleaned_data