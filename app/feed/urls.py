from django.urls import path
from . import views

app_name = 'feed'

urlpatterns = [
    path('', views.visualizar_feed, name='inicio'), 
    path('publicar/', views.publicar_resena, name='publicar'), # página principal del feed
]
