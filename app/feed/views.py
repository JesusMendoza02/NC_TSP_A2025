from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.urls import reverse
from datetime import datetime
from .forms import FormResena
from .models import Resena, Fotografia, Publicacion
from django.http import JsonResponse
import json

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
                    # Usar la hora actual con timezone
                    resena.fecha_visita = timezone.now()
                else:
                    fecha_manual = form_resena.cleaned_data.get('fecha_visita_manual')
                    if fecha_manual:
                        # Asegurar que tenga timezone
                        if timezone.is_naive(fecha_manual):
                            resena.fecha_visita = timezone.make_aware(fecha_manual)
                        else:
                            resena.fecha_visita = fecha_manual
                    else:
                        resena.fecha_visita = timezone.now()
                
                # Debug: imprimir la fecha antes de guardar
                print(f"Fecha a guardar: {resena.fecha_visita}")
                print(f"Tipo: {type(resena.fecha_visita)}")
                
                # Guardar la reseña en la base de datos
                resena.save()
                
                # Debug: verificar qué se guardó
                resena.refresh_from_db()
                print(f"Fecha guardada en DB: {resena.fecha_visita}")
                
                # Guardar las fotografías asociadas
                for foto in fotos:
                    Fotografia.objects.create(resena=resena, fotografia=foto)
                
                # Crear la publicación asociada al turista
                Publicacion.objects.create(
                    turista=request.user.datos,  
                    resena=resena
                )
                
                # Mensaje de éxito ANTES de redirigir
                messages.success(request, "¡Reseña publicada con éxito!")
                return redirect('inicio:inicio')
                
            except Exception as e:
                messages.error(request, f"Error al publicar la reseña: {str(e)}")
                print(f"Error completo: {e}")
                import traceback
                traceback.print_exc()
    else:
        form_resena = FormResena()
    
    return render(request, 'publicacion_form.html', {'form_resena': form_resena})

def eliminar_resena(request):
    return render(request, 'login.html')

def visualizar_feed(request):
    # Obtener todas las publicaciones más recientes primero
    publicaciones = (
        Publicacion.objects
        .select_related('turista', 'resena__lugar_turistico')
        .prefetch_related('resena__fotografias')
        .order_by('-fecha_publicacion')
    )
    
    return render(request, 'feed.html', {'publicaciones': publicaciones})

def dar_like(request):
        return render(request, 'login.html')

