
from django.urls import path
from . import views

app_name = 'feed'

urlpatterns = [
    path('', views.visualizar_feed, name='inicio'),
    path('publicar/', views.publicar_resena, name='publicar'),
    path('feed/', views.visualizar_feed, name='feed'),
    path('like/', views.dar_like, name='dar_like'),
    path('eliminar/<int:publicacion_id>/', views.eliminar_publicacion, name='eliminar_publicacion'),
]