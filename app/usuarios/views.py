from django.shortcuts import render, redirect
from .forms import FormUser, FormTurista
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

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

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from feed.models import Publicacion # 👈 IMPORTANTE: Añade esta importación

# ... (otras vistas)

@login_required
def mostrar_perfil_usuario(request):
    """Muestra el perfil del usuario logueado y sus publicaciones."""
    
    # 1. Obtener el objeto Turista del usuario logueado
    # El modelo User tiene un related_name='datos' al Turista (request.user.datos)
    turista = request.user.datos

    # 2. Obtener las publicaciones del usuario, optimizando las consultas.
    publicaciones = (
        Publicacion.objects
        .filter(turista=turista) # 👈 Filtrar solo las publicaciones del Turista actual
        .select_related('resena__lugar_turistico')
        .prefetch_related('resena__fotografias')
        .order_by('-fecha_publicacion')
    )

    context = {
        'turista': turista,
        'usuario': request.user,
        'publicaciones': publicaciones,
    }
    
    return render(request, 'perfil_usuario.html', context)
