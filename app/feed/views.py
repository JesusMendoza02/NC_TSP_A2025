from django.shortcuts import render

def publicar_resena(request):
    return render(request, 'login.html')

def eliminar_resena(request):
    return render(request, 'login.html')

def visualizar_feed(request):
    return render(request, 'feed.html')

def dar_like(request):
    return render(request, 'login.html')

