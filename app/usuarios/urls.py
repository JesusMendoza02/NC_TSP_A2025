from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio_sesion, name='login'),  # página principal
    path('registrarse/', views.registrar_usuario, name='registrar'),
    path('cerrar/', views.cerrar_sesion, name='cerrar_sesion'),
]
