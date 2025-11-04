from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.urls import reverse
from .forms import FormResena
from .models import Fotografia, Publicacion, Like, Comentario, LugarTuristico
from usuarios.models import Seguidor
from django.views.decorators.http import require_POST
from django.http import JsonResponse



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

    return render(request, 'publicacion_form.html', {'form_resena': form_resena , 'username': request.user.username})

@login_required
def eliminar_publicacion(request, publicacion_id):
    publicacion = get_object_or_404(Publicacion, id=publicacion_id)

    if publicacion.turista.usuario != request.user:
        messages.error(request, "No tienes permiso para eliminar esta publicación.")
        return redirect('perfil_usuario',request.user.username)

    if request.method == 'POST':
        publicacion.delete()
        messages.success(request, "Publicación eliminada con éxito.")
        return redirect('perfil_usuario',request.user.username) 

    return redirect('perfil_usuario',request.user.username)

@login_required
def visualizar_feed(request):
    categoria = request.GET.get('categoria', '')

    # Publicaciones ordenadas por fecha descendente
    publicaciones = (
        Publicacion.objects
        .select_related('turista', 'resena__lugar_turistico')
        .prefetch_related('resena__fotografias', 'comentarios')
    )

    username = request.user.username

    # Obtener los IDs de los usuarios que el actual sigue
    siguiendo_ids = Seguidor.objects.filter(
        turista_seguidor=request.user.datos
    ).values_list('turista_seguido_id', flat=True)

    # --- FILTRO POR CATEGORÍA ---
    if categoria:
        publicaciones = publicaciones.filter(resena__lugar_turistico__categoria=categoria)

    # --- ORDEN PERSONALIZADO ---
    # Primero las publicaciones de seguidos, luego las demás
    publicaciones = sorted(
        publicaciones,
        key=lambda pub: (
            0 if pub.turista_id in siguiendo_ids else 1,  # Prioridad: seguidos primero
            -pub.fecha_publicacion.timestamp()             # Dentro del grupo, más recientes primero
        )
    )

    # Categorías únicas para el filtro
    categorias = LugarTuristico.objects.values_list('categoria', flat=True).distinct()

    # Likes del usuario actual
    likes_usuario = set()
    if request.user.is_authenticated and hasattr(request.user, 'datos'):
        likes_usuario = set(
            Like.objects.filter(turista=request.user.datos)
            .values_list('publicacion_id', flat=True)
        )

    context = {
        'publicaciones': publicaciones,
        'likes_usuario': likes_usuario,
        'categorias': categorias,
        'categoria_actual': categoria,
        'username': username,
    }

    return render(request, 'feed.html', context)

@login_required
@require_POST
def dar_like(request, publicacion_id):
    publicacion = get_object_or_404(Publicacion, id=publicacion_id)
    turista = request.user.datos
    
    if publicacion.turista == turista:
        return JsonResponse({'error': 'No puedes dar like a tu propia publicación.'}, status=400)

    like, creado = Like.objects.get_or_create(publicacion=publicacion, turista=turista)

    if not creado:
        like.delete()
        liked = False
    else:
        liked = True

    publicacion.reaccion = publicacion.likes.count()
    publicacion.save(update_fields=['reaccion'])

    return JsonResponse({
        'liked': liked,
        'total_likes': publicacion.reaccion
    })



@login_required
def escribir_comentario(request, publicacion_id=None):
    if not publicacion_id:
        return redirect('inicio:inicio')  # Redirige al feed si no hay ID

    publicacion = get_object_or_404(Publicacion, id=publicacion_id)
    texto = request.POST.get('texto', '').strip()

    if not texto:
        return redirect('inicio:detalle_publicacion', publicacion_id=publicacion.id)

    if len(texto) > 150:
        return redirect('inicio:detalle_publicacion', publicacion_id=publicacion.id)

    Comentario.objects.create(
        publicacion=publicacion,
        turista=request.user.datos,
        texto=texto
    )
    return redirect('inicio:detalle_publicacion', publicacion_id=publicacion.id)


@login_required
def eliminar_comentario(request, comentario_id=None):
    if not comentario_id:
        return redirect('inicio:inicio')  # Redirige al feed si no hay ID

    comentario = get_object_or_404(Comentario, id=comentario_id)

    # Verificar que el usuario actual sea el autor del comentario
    if comentario.turista.usuario != request.user:
        return redirect('inicio:detalle_publicacion', publicacion_id=comentario.publicacion.id)

    if request.method == 'POST':
        publicacion_id = comentario.publicacion.id  # Guardamos ID antes de borrar
        comentario.delete()
        return redirect('inicio:detalle_publicacion', publicacion_id=publicacion_id)

    # Opcional: si deseas mostrar una confirmación antes de eliminar
    return render(request, 'confirmar_eliminar_comentario.html', {'comentario': comentario})


@login_required
def detalle_publicacion(request, publicacion_id):
    publicacion = get_object_or_404(
        Publicacion.objects
        .select_related('turista', 'resena__lugar_turistico')
        .prefetch_related('resena__fotografias', 'comentarios__turista__usuario'),
        id=publicacion_id
    )

    likes_usuario = set()
    if hasattr(request.user, 'datos'):
        likes_usuario = set(Like.objects.filter(turista=request.user.datos)
                            .values_list('publicacion_id', flat=True))

    context = {
        'publicacion': publicacion,
        'usuario': request.user,
        'username': request.user.username,
        'likes_usuario': likes_usuario
    }
    return render(request, 'detalle_publicacion.html', context)