import requests
from django.conf import settings

def buscar_lugares_zacatecas(query):
    """
    Busca lugares en Zacatecas usando Google Places API
    """
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    
    params = {
        'query': f"{query} Zacatecas, México",
        'key': settings.GOOGLE_MAPS_API_KEY,
        'language': 'es',
        'region': 'mx'
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get('status') == 'OK':
            resultados = []
            for place in data.get('results', [])[:10]:
                resultados.append({
                    'place_id': place.get('place_id'),
                    'nombre': place.get('name'),
                    'ubicacion': place.get('formatted_address'),
                    'latitud': place.get('geometry', {}).get('location', {}).get('lat'),
                    'longitud': place.get('geometry', {}).get('location', {}).get('lng'),
                    'tipos': place.get('types', [])
                })
            return resultados
        else:
            print(f"Error en API: {data.get('status')}")
            return []
    except Exception as e:
        print(f"Error al buscar lugares: {e}")
        return []


def categorizar_lugar(tipos):
    """
    Determina la categoría basándose en los tipos de Google Places
    """
    mapeo_categorias = {
        'restaurant': 'restaurante',
        'food': 'restaurante',
        'bar': 'bar',
        'night_club': 'bar',
        'cafe': 'cafe',
        'museum': 'museo',
        'art_gallery': 'museo',
        'park': 'parque',
        'tourist_attraction': 'monumento',
        'point_of_interest': 'monumento',
        'lodging': 'hotel',
        'church': 'iglesia',  # ← AGREGADO
        'place_of_worship': 'iglesia',  # ← AGREGADO
        'shopping_mall': 'centro_comercial',
        'store': 'tienda',
        'movie_theater': 'entretenimiento',
        'amusement_park': 'entretenimiento',
    }
    
    for tipo in tipos:
        if tipo in mapeo_categorias:
            return mapeo_categorias[tipo]
    
    return 'otro'