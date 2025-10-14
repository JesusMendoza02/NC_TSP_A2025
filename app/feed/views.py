from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .forms import FormResena
from .models import Resena, Fotografia, Publicacion

@login_required
def publicar_resena(request):
    if request.method == 'POST':
        form_resena = FormResena(request.POST, request.FILES)
        
        # Obtener las fotos del request
        fotos = request.FILES.getlist('fotografias')
        
        # Validar máximo 3 fotos
        if len(fotos) > 3:
            messages.error(request, "Solo puedes subir un máximo de 3 fotografías.")
        elif form_resena.is_valid():
            try:
                # Crear la reseña sin guardar aún
                resena = form_resena.save(commit=False)
                
                # Determinar la fecha de visita
                actualmente = form_resena.cleaned_data.get('actualmente_en_lugar')
                
                if actualmente == 'si':
                    resena.fecha_visita = timezone.now()  # Con hora actual
                else:
                    fecha_manual = form_resena.cleaned_data.get('fecha_visita_manual')
                    resena.fecha_visita = fecha_manual if fecha_manual else timezone.now()
                
                # Guardar la reseña en la base de datos
                resena.save()
                
                # Guardar las fotografías asociadas
                for foto in fotos:
                    Fotografia.objects.create(resena=resena, fotografia=foto)
                
                # Crear la publicación asociada al turista
                Publicacion.objects.create(
                    turista=request.user.datos,  # Usar 'datos' según tu modelo
                    resena=resena
                )
                
                messages.success(request, "¡Reseña publicada con éxito!")
                return redirect('inicio')
                
            except Exception as e:
                messages.error(request, f"Error al publicar la reseña: {str(e)}")
    else:
        form_resena = FormResena()
    
    return render(request, 'publicacion_form.html', {'form_resena': form_resena})

def eliminar_resena(request):
    return render(request, 'login.html')

def visualizar_feed(request):
    return render(request, 'feed.html')

def dar_like(request):
    return render(request, 'login.html')

