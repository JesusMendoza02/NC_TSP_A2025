from django import forms
from django.forms import ClearableFileInput
from django.utils import timezone
from datetime import timedelta
from .models import Resena, LugarTuristico

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


class LugarTuristicoChoiceField(forms.ModelChoiceField):
    """Campo personalizado para mostrar nombre y dirección del lugar"""
    def label_from_instance(self, obj):
        return f"{obj.nombre} - {obj.ubicacion}"


class FormResena(forms.ModelForm):
    # Campo personalizado para lugar turístico
    lugar_turistico = LugarTuristicoChoiceField(
        queryset=LugarTuristico.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'font-size: 0.95rem;'
        }),
        label='Lugar turístico',
        empty_label="Selecciona un lugar..."
    )
    
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
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
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
        label='Fecha y hora de visita',
        help_text='Debe ser dentro del último mes y no puede ser una fecha futura'
    )

    class Meta:
        model = Resena
        fields = ['lugar_turistico', 'descripcion', 'calificacion']

        widgets = {
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
            'descripcion': 'Descripción de la visita',
            'calificacion': 'Calificación (1-10)',
        }

    def clean_calificacion(self):
        calificacion = self.cleaned_data.get('calificacion')
        if calificacion and (calificacion < 1 or calificacion > 10):
            raise forms.ValidationError("La calificación debe estar entre 1 y 10.")
        return calificacion
    
    def clean_fecha_visita_manual(self):
        """Validar que la fecha esté dentro del último mes y no sea futura"""
        fecha_manual = self.cleaned_data.get('fecha_visita_manual')
        
        if fecha_manual:
            # Obtener la fecha actual
            ahora = timezone.now()
            
            # Convertir fecha_manual a aware si es naive
            if timezone.is_naive(fecha_manual):
                fecha_manual = timezone.make_aware(fecha_manual)
            
            # Validar que no sea fecha futura
            if fecha_manual > ahora:
                raise forms.ValidationError(
                    "No puedes seleccionar una fecha futura. "
                    "La fecha debe ser de hoy o anterior."
                )
            
            # Calcular fecha límite (1 mes atrás)
            hace_un_mes = ahora - timedelta(days=30)
            
            # Validar que esté dentro del último mes
            if fecha_manual < hace_un_mes:
                raise forms.ValidationError(
                    "La fecha de visita debe ser dentro del último mes. "
                    f"No puede ser anterior al {hace_un_mes.strftime('%d/%m/%Y %H:%M')}."
                )
        
        return fecha_manual
    
    def clean(self):
        cleaned_data = super().clean()
        actualmente = cleaned_data.get('actualmente_en_lugar')
        fecha_manual = cleaned_data.get('fecha_visita_manual')
        
        # Validar que si NO está actualmente, debe proporcionar fecha
        if actualmente == 'no' and not fecha_manual:
            self.add_error('fecha_visita_manual', 
                          'Debes proporcionar la fecha y hora de tu visita.')
        
        return cleaned_data