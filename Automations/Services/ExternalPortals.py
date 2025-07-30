import requests
from dotenv import load_dotenv
import os
load_dotenv()

def DespublicarFincaRaiz(inmueble):
    
    login_url = "https://graph.infocasas.com.uy/graphql"

    # Headers del login
    headers = {
        "x-origin": "www.fincaraiz.com.co",
    }

    # Datos de autenticación
    payload_login = [
        {
            "operationName": "Login",
            "variables": {
                "email": os.getenv("FINCA_USER"),
                "pass": os.getenv("FINCA_PASSWORD"),
                "is_terms_and_conditions_accepted": False
            },
            "query": """
            mutation Login($email: String!, $pass: String!, $is_terms_and_conditions_accepted: Boolean) {
                login(
                    input: {username: $email, password: $pass, is_terms_and_conditions_accepted: $is_terms_and_conditions_accepted}
                ) {
                    access_token
                    user_md5
                    __typename
                }
            }
            """
        }
    ]

    # Iniciar sesión y obtener el token
    session = requests.Session()
    response_login = session.post(login_url, headers=headers, json=payload_login)

    # Validar respuesta
    if response_login.status_code == 200:
        try:
            # Extraer token de la respuesta JSON
            access_token = response_login.json()[0]["data"]["login"]["access_token"]
            print("Token obtenido correctamente:")

            # Establecer el token en los headers de la sesión
            session.headers.update({"Authorization": f"Bearer {access_token}"})

        except (KeyError, IndexError):
            print("Error al extraer el token de la respuesta")
    else:
        print(f"Error en login: {response_login.status_code}")
        print(response_login.text)
    payload_inmueble = {
        "search":f"{inmueble}",
    }
    find_inmueble = session.post("https://graph.infocasas.com.uy/api/1.0/listing/virtual-office", json=payload_inmueble, headers=headers)
    try:
        inmueble = find_inmueble.json()["response"]["data"][0]["available_actions"]
        if "add_products" in inmueble:
            print("iniciando proceso de desactivacion")
            
            payload_despublicar = [
            {
                "listing_id": find_inmueble.json()["response"]["data"][0]["id"],
                "desired_status": "INACTIVE"
            }
            ]
            desactive_response = session.put("https://graph.infocasas.com.uy/api/1.0/listing/status", json=payload_despublicar, headers=headers)
            print(desactive_response.status_code)
    except:
        print("inmueble no encontrado")
####porta ciencuadras
def DespublicarCiencuadras(inmueble):
    retorno = False
    # 1. Obtener el token de autenticación
    token_url = "https://ciencuadras-prod-api-auth.auth.us-east-1.amazoncognito.com/oauth2/token"
    auth_payload = {"grant_type": "client_credentials"}
    auth_headers = {
        "Authorization": os.getenv("CIEN_CUADRAS_TOKEN"),
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.post(token_url, data=auth_payload, headers=auth_headers)

    if response.status_code == 200:
        access_token = response.json().get("access_token")
        print("Token obtenido con éxito.")
    else:
        print("Error al obtener el token:", response.text)

    # 2. Obtener publicaciones
    publications_url = "https://api-backend.ciencuadras.com/prod/publications/v1/publications?ignorePropertyTypes=false"
    publications_payload = {
        "userId": "8436",
        "transactionTypeId": None,
        "userTypeId": "1",
        "sortField": None,
        "sortOrder": None,
        "param": {
            "name": None,
            "id": None,
            "cityId": None,
            "projectPhaseId": None,
            "code": f"8436-494{inmueble}",
            "transactionTypeId": None,
            "city": None,
        },
        "actives": {
            "from": 0,
            "size": 10,
            "currentPage": 1,
            "total": 0,
            "code": "",
        },
        "inactives": {
            "from": 0,
            "size": 10,
            "currentPage": 1,
            "total": 0,
            "code": "",
        },
        "total": {
            "from": 0,
            "size": 10,
            "currentPage": 1,
            "total": 0,
            "code": "",
        },
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    response = requests.post(publications_url, json=publications_payload, headers=headers)

    if response.status_code == 200:
        publications_data = response.json()
        active_count = publications_data.get("data", {}).get("activePublicationsCount", 0)
        print(f"Número de publicaciones activas: {active_count}")

        # 3. Verificar si debe deshabilitar
        if active_count == 1:
            retorno = True
            active_publications = publications_data.get("data", {}).get("activePublications", [])
            if active_publications:
                publication_id = active_publications[0].get("id")
                print(f"Deshabilitando publicación con ID: {publication_id}")

                # 4. Deshabilitar publicación
                disable_url = "https://api-backend.ciencuadras.com/prod/publications/v1/disable"
                disable_payload = {
                    "id": publication_id,
                    "userId": 8436,
                    "userTypeId": 1,
                }

                disable_response = requests.post(disable_url, json=disable_payload, headers=headers)

                if disable_response.status_code == 200:
                    print("Publicación deshabilitada con éxito:", disable_response.json())
                else:
                    print("Error al deshabilitar publicación:", disable_response.text)
            else:
                print("No se encontró ninguna publicación activa para deshabilitar.")
        else:
            print("No hay publicaciones activas que deshabilitar.")
    else:
        print("Error al obtener publicaciones:", response.text)
    return retorno