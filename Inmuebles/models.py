from django.db import models

# Create your models here.

class Inmueble(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    fecha_creacion = models.DateTimeField()
    gestion = models.CharField(max_length=20, null=True, blank=True)
    fecha_disponibilidad = models.DateTimeField(null=True, blank=True)
    fecha_ultimo_mensaje = models.DateTimeField(null=True, blank=True)
    intentos_de_contacto = models.IntegerField(default=0)
    estado = models.BooleanField(default=True)
    fecha_desactivacion = models.DateTimeField(null=True, blank=True)
    estado_finca= models.BooleanField(default=True)
    estado_Ciencuadras = models.BooleanField(default=True)