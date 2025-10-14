from django.db import models
from usuarios.models import Turista

class LugarTuristico(models.Model):
    nombre = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=150)
    categoria = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre
    

class Resena(models.Model):
    lugar_turistico = models.ForeignKey(
        LugarTuristico,
        on_delete=models.CASCADE,
        related_name='resenas'
    )
    descripcion = models.TextField()
    fecha_visita = models.DateTimeField()
    calificacion = models.PositiveSmallIntegerField() 

    def __str__(self):
        return f"Reseña de {self.lugar_turistico} ({self.calificacion}/5)"



class Publicacion(models.Model):
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    reaccion = models.IntegerField(default=0)  
    turista = models.ForeignKey(
        Turista,
        on_delete=models.CASCADE,
        related_name='publicaciones'
    )
    resena = models.ForeignKey(
        Resena,
        on_delete=models.CASCADE,
        related_name='publicaciones'
    )

    def __str__(self):
        return f"Publicación de {self.turista} ({self.resena.lugar_turistico})"



class Fotografia(models.Model):
    resena = models.ForeignKey(
        Resena,
        on_delete=models.CASCADE,
        related_name='fotografias'
    )
    fotografia = models.ImageField(upload_to='fotos_resenas/')

    def __str__(self):
        return f"Foto de la reseña {self.resena.id}"
