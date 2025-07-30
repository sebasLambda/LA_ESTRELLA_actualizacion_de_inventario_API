from django.urls import path
from .views import *

urlpatterns = [
    path("actualizar-valor/", ActualizarValorInmuebleView.as_view(), name="actualizar_valor_inmueble"),
    path("actualizar-estatus/", ActualizarEstatusInmuebleView.as_view(), name="actualizar_estatus_inmueble"),
    path("comparar-valores/", CompararValoresView.as_view(), name="comparar_valores_inmueble"),
    path("contactar-propietario/" , ContactarPropietarioView.as_view(), name="contactar_propietario"),
    path("optener-inmueble/", optenerInmueblesView.as_view(), name="optener_inmuebles"),
]
