from django.shortcuts import render, get_object_or_404
from django.conf import settings
from feed.models import LugarTuristico

def mapa_view(request, lugar_id):
    """Muestra el mapa con la ruta desde la ubicación actual del usuario hasta el lugar."""
    lugar = get_object_or_404(LugarTuristico, id=lugar_id)

    return render(request, 'mapa.html', {
        'lugar': lugar,
        'api_key': settings.GOOGLE_MAPS_API_KEY,
        'username': request.user.username
    })