import requests
from dotenv import load_dotenv
import os
import requests
import pandas as pd
from datetime import datetime
from Inmuebles.models import Inmueble
load_dotenv()
def ConsultarTercero(nroid):
    url = f"https://zonaclientes.softinm.com/api/terceros/GetTercero/{os.getenv('SOFTIN_EXTENSION')}"
    token = os.getenv('SOFTIN_TOKEN')

    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}",
    })

    payload = {"nroid": nroid}
    response = session.post(url, json=payload)

    if response.status_code == 200:
        data = response.json()
        
        return {
            "nombre": data.get("nombre", ""),
            "celular": data.get("celular", "")
        }
    else:
        print("Error al consultar tercero:", response.status_code, response.text)
        return {"nombre": "", "celular": ""}


def ConsultarInmueblesPorId(idInmueble):
    url = f"https://zonaclientes.softinm.com/api/inmuebles/consultar_inmuebles/{os.getenv('SOFTIN_EXTENSION')}"
    token = os.getenv('SOFTIN_TOKEN')
    
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}",
    })

    payload = {
        "codigo": idInmueble
    }

    response = session.post(url, json=payload)

    if response.status_code == 200:
        inmuebles = response.json()
        if not inmuebles:
            print(f"No se encontró ningún inmueble con ese código. Código: {idInmueble}")
            return None

        inmueble_raw = inmuebles[0]
        tipo_servicio = inmueble_raw.get("tipo_servicio", "Arriendo")

        propietario = ConsultarTercero(inmueble_raw.get("nro_id", ""))
        inmueble = {
            "codigo": str(inmueble_raw.get("consecutivo", "")),
            "propietario": propietario.get("nombre", ""),
            "direccion": inmueble_raw.get("direccion", ""),
            "tipo": inmueble_raw.get("clase", ""),
            "VlrArriendo": inmueble_raw.get("precio", 0),
            "VlrVenta": inmueble_raw.get("precio_venta", 0),
            "celular": propietario.get("celular", ""),
            "gestion": tipo_servicio,
            "matricula": inmueble_raw.get("matriculainmobiliaria", ""),
            "fecha_creacion": inmueble_raw.get("fechamodificado", ""),
        }

        print(f"Inmueble consultado: {inmueble}")
        return inmueble

    else:
        print("Error al consultar inmuebles:", response.status_code, response.text)
        return None
def ConsultarInmuebles():
    url = f"https://zonaclientes.softinm.com/api/inmuebles/consultar_inmuebles/{os.getenv('SOFTIN_EXTENSION')}"
    token = os.getenv("SOFTIN_TOKEN")

    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}",
    })

    payload = {
        "cantidadporpagina": 10000,
        "pagina": 0
    }

    response = session.post(url, json=payload)

    if response.status_code == 200:
        inmuebles = response.json()

        for inmueble in inmuebles:
            print(inmueble)

            try:
                consecutivo = str(inmueble["consecutivo"])
                inmueble_data = ConsultarInmueblesPorId(consecutivo)  # Asegúrate de que esta función esté implementada y devuelva dict

                Inmueble.objects.update_or_create(
                    codigo=consecutivo,
                    defaults={
                        "fecha_creacion": datetime.strptime(inmueble_data.get("fechamodificado", ""), "%Y-%m-%dT%H:%M:%S"),
                        "gestion": inmueble_data.get("gestion", ""),
                        "fecha_disponibilidad": None,
                        "fecha_ultimo_mensaje": None,
                        "intentos_de_contacto": 0,
                        "estado": True,
                    }
                )

            except Exception as e:
                print(f"Error procesando inmueble {inmueble}: {e}")

    else:
        print("Error al consultar inmuebles:", response.status_code, response.text)

class SoftinmClient:
    def __init__(self):
        # Inicializa la sesión HTTP y credenciales desde variables de entorno
        self.session = requests.Session()
        self.usuario = os.getenv("SOFTINM_USUARIO")
        self.clave = os.getenv("SOFTINM_CLAVE")
        self.id_empresa = int(os.getenv("SOFTINM_EMPRESA_ID",))
        self.token = None
        self.login()

    def login(self):
        """
        Realiza la autenticación contra la API de Softinm y actualiza los headers
        de la sesión con el token de autorización necesario para futuras peticiones.
        """
        login_url = "https://www.softinm.com/api/usuarios/login"
        payload = {
            "idEmpresa": self.id_empresa,
            "usuario": self.usuario,
            "clave": self.clave
        }

        response = self.session.post(login_url, json=payload)
        response.raise_for_status()

        data = response.json()
        self.token = data.get("token") or data.get("access_token")
        if not self.token:
            raise Exception("No se obtuvo token.")

        # Headers obligatorios para todas las llamadas posteriores
        self.session.headers.update({
            "authorization": f"Bearer {self.token}",
            "accept": "application/json, text/plain, */*",
            "accept-language": "es-419,es;q=0.9",
            "content-type": "application/json;charset=UTF-8",
            "origin": "https://www.softinm.com",
            "referer": "https://www.softinm.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."
        })

    def retirar_inmueble(self, inmueble_id: int):
        """
        Marca un inmueble como retirado en Softinm.
        - inmueble_id: ID del inmueble a retirar.
        """
        url_consulta = f"https://softinm.com/api/inmueble/conulstaInmueble/{inmueble_id}"
        resp = self.session.get(url_consulta)
        resp.raise_for_status()
        inmueble = resp.json()

        # Marca como retirado y registra la fecha de modificación
        inmueble["retirado"] = True
        inmueble["fechamodificado"] = datetime.now().isoformat()

        url_update = "https://softinm.com/api/inmueble/actualizarinmueble"
        put = self.session.put(url_update, json=inmueble)

        print(f"Inmueble {inmueble_id} retirado - PUT {put.status_code}")
        try:
            print("Json:", put.json())
        except:
            print("Texto:", put.text)

    def actualizar_valor(self, inmueble_id: int, nuevo_valor: int, tipo_servicio: str):
        """
        Actualiza el valor del inmueble, dependiendo del tipo de servicio.
        - Si es Arriendo: actualiza el canon (`precio`)
        - Si es Venta: actualiza `precio_venta`
        - VlrVenta si es para venta, VlrArriendo
        """
        url_consulta = f"https://softinm.com/api/inmueble/conulstaInmueble/{inmueble_id}"
        resp = self.session.get(url_consulta)
        resp.raise_for_status()
        inmueble = resp.json()


        # Lógica condicional según tipo de servicio
        if tipo_servicio == "Arriendo":
            inmueble["precio"] = nuevo_valor
            print(f"✔ Tipo: Arriendo – Se actualiza canon a {nuevo_valor}")
        else:
            inmueble["precio_venta"] = nuevo_valor
            print(f"✔ Tipo: {tipo_servicio} – Se actualiza precio_venta a {nuevo_valor}")

        inmueble["fechamodificado"] = datetime.now().isoformat()

        url_update = "https://softinm.com/api/inmueble/actualizarinmueble"
        put = self.session.put(url_update, json=inmueble)

        print(f"Inmueble {inmueble_id} actualizado - PUT {put.status_code}")
        try:
            print("Respuesta JSON:", put.json())
        except:
            print("Texto:", put.text)

    def actualizar_fecha_disponibilidad(self, inmueble_id: int, nueva_fecha: str):
        """
        Actualiza la fecha de disponibilidad de un inmueble.
        - nueva_fecha: debe ser un string en formato 'YYYY-MM-DD'
        """
        url_consulta = f"https://softinm.com/api/inmueble/conulstaInmueble/{inmueble_id}"
        resp = self.session.get(url_consulta)
        resp.raise_for_status()
        inmueble = resp.json()

        # Validación del formato de fecha
        try:
            datetime.strptime(nueva_fecha, "%Y-%m-%d")
        except ValueError:
            raise ValueError("La fecha debe tener el formato 'YYYY-MM-DD'")

        # Asignación y modificación
        inmueble["fechadisponible"] = nueva_fecha
        inmueble["fechamodificado"] = datetime.now().isoformat()

        url_update = "https://softinm.com/api/inmueble/actualizarinmueble"
        put = self.session.put(url_update, json=inmueble)

        print(f"Fecha de disponibilidad actualizada para {inmueble_id} - PUT {put.status_code}")
        try:
            print("Respuesta JSON:", put.json())
        except:
            print("Texto:", put.text)
