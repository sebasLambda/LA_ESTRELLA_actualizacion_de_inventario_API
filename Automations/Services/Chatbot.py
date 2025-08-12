import requests
import json
import phonenumbers
from requests.auth import HTTPBasicAuth
from datetime import datetime
from dotenv import load_dotenv
import os
from .Softin import ConsultarInmueblesPorId
from twilio.rest import Client

load_dotenv()

def es_numero_valido(numero):
    try:
        parsed = phonenumbers.parse(numero, None)
        return phonenumbers.is_valid_number(parsed)
    except phonenumbers.NumberParseException:
        return False

def formatear_numero_internacional(numero, region_default="CO"):
    try:
        if numero.startswith("+"):
            parsed = phonenumbers.parse(numero, None)
        elif numero.startswith("3") and len(numero) == 10:
            parsed = phonenumbers.parse(numero, region_default)
        else:
            return f"+{numero}"

        # Formatear al estándar internacional E.164
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

    except Exception:
        return None


def iniciar_flujo(inmueble_id):
    inmueble = ConsultarInmueblesPorId(inmueble_id)
    flow_sid = os.getenv("TWILIO_FLOW_SID")  # Reemplaza con tu Flow SID de Twilio
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")  # Reemplaza con tu Account SID de Twilio
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")  # Reemplaza con tu Auth Token de Twilio

    celular = formatear_numero_internacional(inmueble["celular"])

    try:
        url = f"https://studio.twilio.com/v2/Flows/{flow_sid}/Executions"

        parametros = json.dumps({
            "codigo": str(inmueble["codigo"]),
            "propietario": inmueble["propietario"],
            "direccion": inmueble["direccion"],
            "tipo": inmueble["tipo"],
            "valor": str("${:,.0f}".format(inmueble["VlrArriendo"]).replace(",", ".")) if inmueble["gestion"] == "Arriendo" else str("${:,.0f}".format(inmueble["VlrVenta"]).replace(",", ".")),
            "gestion": str(inmueble["gestion"]),
        })

        payload = {
            "To": f"whatsapp:{celular}",
            "From": "whatsapp:+573009089882",
            "Parameters": parametros
        }

        response = requests.post(url, data=payload, auth=HTTPBasicAuth(account_sid, auth_token), timeout=10)
        
        if response.status_code == 201:
            print(f"Flujo iniciado correctamente para el inmueble {inmueble['codigo']}")
            inmueble["fecha_ultimo_mensaje"] = datetime.now()
            return response.json()
        else:
            print(f"Error al iniciar flujo: {response.status_code} - {response.text}")
            return None

    except requests.exceptions.Timeout:
        print("Timeout: La solicitud a Twilio excedió el tiempo de espera.")
    except requests.exceptions.ConnectionError:
        print("Error: Fallo de conexión con Twilio.")
    except Exception as e:
        print(f"Error inesperado: {str(e)}")

    return None
def notificar_asesor(inmueble_id, plantilla):
    inmueble= ConsultarInmueblesPorId(inmueble_id)
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    gestion = inmueble["gestion"]
    client = Client(account_sid, auth_token)
    if plantilla == "nuevo_inmueble":
        plantilla_id = os.getenv("TWILIO_PLANTILLA_NUEVO_INMUEBLE")
        numero_asesor = os.getenv("CALL_CENTER")
    elif plantilla == "Atencion_personalizada":
        plantilla_id = os.getenv("TWILIO_PLANTILLA_ATENCION_PERSONALIZADA")
        if gestion == "Arriendo":
            numero_asesor = os.getenv("CALL_CENTER_ARRIENDO")
        else:
            numero_asesor = os.getenv("CALL_CENTER_VENTA")
    try:
        message = client.messages.create(
            from_='whatsapp:+573009089882',
            content_sid=plantilla_id,
            content_variables=f'{{"1":"{inmueble["codigo"]}","2":"{inmueble["propietario"]}","3":"{inmueble["direccion"]}","4":"{inmueble["celular"]}"}}',
            to=f"whatsapp:+{numero_asesor}"
            )
        print(f"Notificación enviada al asesor: {numero_asesor}")
    except Exception as e:
        print(f"Error al enviar notificación al asesor: {str(e)}")
        return None
    
def Despublicado(inmueble_id, plantilla):
    inmueble= ConsultarInmueblesPorId(inmueble_id)
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    gestion = inmueble["gestion"]
    client = Client(account_sid, auth_token)
    if plantilla == "nuevo_inmueble":
        plantilla_id = os.getenv("TWILIO_PLANTILLA_NUEVO_INMUEBLE")
        numero_asesor = os.getenv("CALL_CENTER")
    elif plantilla == "Atencion_personalizada":
        plantilla_id = os.getenv("TWILIO_PLANTILLA_ATENCION_PERSONALIZADA")
        if gestion == "Arriendo":
            numero_asesor = os.getenv("CALL_CENTER_ARRIENDO")
        else:
            numero_asesor = os.getenv("CALL_CENTER_VENTA")
    try:
        message = client.messages.create(
            from_='whatsapp:+573009089882',
            content_sid=plantilla_id,
            content_variables=f'{{"1":"{inmueble["codigo"]}","2":"{inmueble["propietario"]}","3":"{inmueble["direccion"]}","4":"{inmueble["celular"]}"}}',
            to=f"whatsapp:+{numero_asesor}"
            )
        print(f"Notificación enviada al asesor: {numero_asesor}")
    except Exception as e:
        print(f"Error al enviar notificación al asesor: {str(e)}")
        return None