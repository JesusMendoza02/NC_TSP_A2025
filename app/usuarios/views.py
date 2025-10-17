from django.shortcuts import render, redirect
from .forms import FormUser, FormTurista
from feed.models import Publicacion 
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required

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
def mostrar_perfil_usuario(request):
    """Muestra el perfil del usuario logueado con paginación (5 publicaciones por página)."""
    
    # 1. Obtener el objeto Turista del usuario logueado (User → datos)
    turista = request.user.datos

    # 2. Obtener las publicaciones del usuario, optimizando las consultas
    publicaciones_qs = (
        Publicacion.objects
        .filter(turista=turista)
        .select_related('resena__lugar_turistico')
        .prefetch_related('resena__fotografias')
        .order_by('-fecha_publicacion')
    )

    # 3. Paginación 
    paginator = Paginator(publicaciones_qs, 5)
    page_number = request.GET.get('page')
    publicaciones = paginator.get_page(page_number) 

    # 4. Contexto
    context = {
        'turista': turista,
        'usuario': request.user,
        'publicaciones': publicaciones,
    }
    
    return render(request, 'perfil_usuario.html', context)
