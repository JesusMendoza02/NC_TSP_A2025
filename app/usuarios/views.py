from django.shortcuts import render, redirect, get_object_or_404
from .forms import FormUser, FormTurista, FormEdicionUser, FormEdicionTurista, FormCambiarContrasena
from feed.models import Publicacion, Like
from .models import Turista, Seguidor
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib.auth import update_session_auth_hash

def registrar_usuario(request):
    if request.method == 'POST':
        user_form = FormUser(request.POST)
        turista_form = FormTurista(request.POST)

        if user_form.is_valid() and turista_form.is_valid():
            user = user_form.save()

            turista = turista_form.save(commit=False)
            turista.usuario = user
            turista.save()

            login(request, user)
            messages.success(request, f'¡Bienvenido, {user.username}!')
            return redirect('login')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')

    else:
        user_form = FormUser()
        turista_form = FormTurista()

    return render(request, 'registro.html', {
        'user_form': user_form,
        'turista_form': turista_form
    })

def inicio_sesion(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Autenticación del usuario
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('feed:inicio') 
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')

    # Si es GET o hay error, renderiza la página de login
    return render(request, 'login.html')

def cerrar_sesion(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('login')

@login_required
def perfil_usuario(request, username):
    """
    Muestra el perfil de cualquier usuario por su username.
    """
    # Obtener el turista correspondiente al username
    turista = get_object_or_404(Turista, usuario__username=username)

    # Publicaciones con paginación
    publicaciones_qs = (
        Publicacion.objects
        .filter(turista=turista)
        .select_related('resena__lugar_turistico')
        .prefetch_related('resena__fotografias')
        .order_by('-fecha_publicacion')
    )
    paginator = Paginator(publicaciones_qs, 5)
    page_number = request.GET.get('page')
    publicaciones = paginator.get_page(page_number)

    # Seguidores y siguiendo
    seguidores = Seguidor.objects.filter(turista_seguido=turista)
    siguiendo = Seguidor.objects.filter(turista_seguidor=turista)

    # Ver si el usuario actual sigue a este perfil
    siguiendo_a_usuario = Seguidor.objects.filter(
        turista_seguidor=request.user.datos,
        turista_seguido=turista
    ).exists()

    # IDs de publicaciones que el usuario ha likeado
    likes_usuario = Like.objects.filter(turista=request.user.datos).values_list('publicacion_id', flat=True)

    context = {
        'turista': turista,
        'username': request.user.username,
        'publicaciones': publicaciones,
        'seguidores': seguidores,
        'siguiendo': siguiendo,
        'siguiendo_a_usuario': siguiendo_a_usuario,
        'likes_usuario': likes_usuario,  
    }

    return render(request, 'perfil_usuario.html', context)



@login_required
def seguidores(request, username=None):
    if username:
        turista = get_object_or_404(Turista, usuario__username=username)
    else:
        turista = request.user.datos

    # Personas que este usuario sigue
    lista_siguiendo = (
        Seguidor.objects.filter(turista_seguidor=turista)
        .select_related('turista_seguido__usuario')
    )

    # Personas que siguen a este usuario
    lista_seguidores = (
        Seguidor.objects.filter(turista_seguido=turista)
        .select_related('turista_seguidor__usuario')
    )

    # Lista de IDs de usuarios que el usuario logueado sigue
    siguiendo_ids = set(
        Seguidor.objects.filter(turista_seguidor=request.user.datos)
        .values_list('turista_seguido__id', flat=True)
    )

    context = {
        'turista': turista,
        'seguidores': lista_seguidores,
        'siguiendo': lista_siguiendo,
        'siguiendo_ids': siguiendo_ids,
        'username': request.user.username,
    }

    return render(request, 'seguidores.html', context)



@login_required
def toggle_seguir(request, turista_id):
    turista_a_seguir = get_object_or_404(Turista, id=turista_id)
    turista_actual = request.user.datos

    if turista_actual == turista_a_seguir:
        return redirect('perfil_usuario',turista_a_seguir.usuario.username)  

    relacion, creado = Seguidor.objects.get_or_create(
        turista_seguidor=turista_actual,
        turista_seguido=turista_a_seguir
    )

    if not creado:  
        relacion.delete()

    return redirect('perfil_usuario', turista_a_seguir.usuario.username)


@login_required
@transaction.atomic
def editar_perfil(request):
    turista_actual = request.user.datos 
    
    if request.method == 'POST':
        if 'fecha_nac' in request.POST and not request.POST['fecha_nac']:
            post_data = request.POST.copy()
            
            if turista_actual.fecha_nac:
                post_data['fecha_nac'] = turista_actual.fecha_nac.isoformat()
            else:
                 pass
            
            user_form = FormEdicionUser(post_data, instance=request.user)
            turista_form = FormEdicionTurista(post_data, request.FILES, instance=turista_actual)
            contrasena_form = FormCambiarContrasena(post_data)
        else:
            user_form = FormEdicionUser(request.POST, instance=request.user)
            turista_form = FormEdicionTurista(request.POST, request.FILES, instance=turista_actual)
            contrasena_form = FormCambiarContrasena(request.POST)


        perfil_actualizado = False
        contrasena_cambiada = False
        
        #Manejar Edición de Perfil (User/Turista)
        if user_form.is_valid() and turista_form.is_valid():
            user = user_form.save()
            turista_form.save()
            perfil_actualizado = True
        
        #Manejar Cambio de Contraseña 
        new_password_input = contrasena_form.data.get('new_password')
        
        if new_password_input and new_password_input.strip(): 
            if contrasena_form.is_valid():
                user.set_password(contrasena_form.cleaned_data['new_password'])
                user.save()
                update_session_auth_hash(request, user)
                contrasena_cambiada = True
            else:
                return render(request, 'editar_perfil.html', {
                    'user_form': user_form,
                    'turista_form': turista_form,
                    'contrasena_form': contrasena_form, 
                    'turista': turista_actual
                })

        #Mensajes finales basados en el resultado
        if perfil_actualizado and contrasena_cambiada:
            messages.success(request, '¡Perfil y Contraseña actualizados con éxito! 🎉')
        elif perfil_actualizado:
            messages.success(request, '¡Tu perfil ha sido actualizado con éxito! 🎉')
        elif contrasena_cambiada:
            messages.success(request, '¡Contraseña actualizada con éxito! (El perfil no fue modificado) 🎉')
        
        #Redirección final
        if perfil_actualizado or contrasena_cambiada:
            return redirect('perfil_usuario', username=request.user.username)
        
    else:
        user_form = FormEdicionUser(instance=request.user)
        turista_form = FormEdicionTurista(instance=turista_actual)
        contrasena_form = FormCambiarContrasena()

    context = {
        'user_form': user_form,
        'turista_form': turista_form,
        'contrasena_form': contrasena_form,
        'turista': turista_actual
    }
    
    return render(request, 'editar_perfil.html', context)