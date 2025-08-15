from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .Services.Softin import *
from datetime import datetime
import os
import pandas as pd
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
from .Services.Chatbot import notificar_asesor
from Inmuebles.models import Inmueble
import threading
class ActualizarValorInmuebleView(APIView):
    """
    POST /actualizar-valor/
    {
        "inmueble_id": 12475,
        "asesor": "juan",
        "VlrVenta": "$1.850.000",
        "VlrArriendo": "2,200,000"
    }
    """

    def post(self, request):
        try:
            def limpiar(valor):
                if not valor or str(valor).strip() == "":
                    return 0
                return int(str(valor).replace("$", "").replace(".", "").replace(",", "").strip())

            inmueble_id = int(request.data.get("inmueble_id"))
            asesor = request.data.get("asesor", "No especificado")
            
            # Determinamos el valor a actualizar según el campo recibido
            if "VlrVenta" in request.data:
                nuevo_valor = limpiar(request.data.get("VlrVenta"))
                tipo_valor = "Venta"
            elif "VlrArriendo" in request.data:
                nuevo_valor = limpiar(request.data.get("VlrArriendo"))
                tipo_valor = "Arriendo"
            else:
                return Response({"error": "Debe proporcionar 'VlrVenta' o 'VlrArriendo'"}, status=400)
            
            info_inmueble = ConsultarInmueblesPorId(inmueble_id)
            if not info_inmueble:
                return Response({"error": "No se encontró información del inmueble"}, status=404)

            valor_anterior = int(info_inmueble.get("valor_canon", 0))
            diferencia = nuevo_valor - valor_anterior
            variacion = (diferencia / valor_anterior) * 100 if valor_anterior != 0 else 0

            # Actualiza valor vía API externa
            client = SoftinmClient()

            try:
                threading.Thread(target=client.actualizar_valor, args=(inmueble_id, nuevo_valor, tipo_valor)).start()
            except Exception as e:
                return Response({"error": f"Error al actualizar el valor en la API externa: {str(e)}"}, status=500)

            # Registrar cambio en hoja separada
            try:
                threading.Thread(target=self.registrar_cambio_precio, args=(info_inmueble, valor_anterior, nuevo_valor, asesor)).start()
            except Exception as e:
                return Response({"error": f"Error al registrar el cambio en la hoja separada: {str(e)}"}, status=500)

            return Response({
                "mensaje": f"Inmueble {inmueble_id} actualizado correctamente",
                "tipo_valor": tipo_valor,
                "valor_anterior": valor_anterior,
                "nuevo_valor": nuevo_valor,
                "diferencia": diferencia,
                "variacion_porcentual": round(variacion, 2)
            })

        except ValueError as e:
            return Response({"error": "Formato de valor incorrecto. Verifique los valores de entrada."}, status=400)
        except KeyError as e:
            return Response({"error": f"Falta el campo requerido: {str(e)}"}, status=400)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def registrar_cambio_precio(self, inmueble_data, precio_anterior, precio_nuevo, asesor):
        print("Registrando cambio de valor en Excel...")

        archivo = "inmuebles_retirados.xlsx"
        hoja = "cambios_valor"

        df_nuevo = pd.DataFrame([{
            "codigo": inmueble_data.get("codigo", ""),
            "direccion": inmueble_data.get("direccion", ""),
            "propietario": inmueble_data.get("propietario", ""),
            "celular": inmueble_data.get("celular", ""),
            "tipo": inmueble_data.get("tipo", ""),
            "gestion": inmueble_data.get("gestion", ""),
            "precio_anterior": precio_anterior,
            "precio_nuevo": precio_nuevo,
            "registrado_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Responsable": asesor
        }])

        try:
            if os.path.exists(archivo):
                with pd.ExcelWriter(archivo, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
                    try:
                        df_existente = pd.read_excel(archivo, sheet_name=hoja)
                        df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
                    except ValueError:
                        df_final = df_nuevo  # la hoja aún no existe
                    column_order = [
                        "codigo", "direccion", "propietario", "celular",
                        "tipo", "gestion", "precio_anterior", "precio_nuevo", "registrado_en"
                    ]
                    df_final = df_final.reindex(columns=column_order)
                    df_final.to_excel(writer, sheet_name=hoja, index=False)
            else:
                with pd.ExcelWriter(archivo, engine='openpyxl') as writer:
                    df_nuevo.to_excel(writer, sheet_name=hoja, index=False)

            print("Cambio de valor registrado correctamente.")

        except Exception as e:
            print(f"Error al manipular Excel: {e}")
            raise


class ActualizarEstatusInmuebleView(APIView):
    """
    Actualiza el estatus de un inmueble y registra la acción en un Excel.

    POST /actualizar-estatus/
    {
        "inmueble_id": 12475,
        "mensaje": "No, disponible",
        "asesor": "Juan Perez"
    }
    """
    RESPUESTAS_VALIDAS = {
        "He decidido no arrendar.": True,
        "No, ya se arrendó.": True,
        "Sí, continúa disponible": False,
        "No, ya se vendió": True,
        "He decidido no vender": True,
        "FlujoAsesor": True,
    }

    def post(self, request):
        try:
            inmueble_id = int(request.data.get("inmueble_id"))
            mensaje = request.data.get("mensaje", "").strip()
            asesor = request.data.get("asesor", "Propietario")
            inmueble_local = Inmueble.objects.filter(codigo=inmueble_id).first()
            print(f"Mensaje recibido: {mensaje}")
            if mensaje not in self.RESPUESTAS_VALIDAS:
                return Response({
                    "error": "El mensaje recibido no está en las opciones válidas. No se realizará ninguna acción.",
                    "mensajes_validos": list(self.RESPUESTAS_VALIDAS.keys())
                }, status=status.HTTP_400_BAD_REQUEST)

            retirar = self.RESPUESTAS_VALIDAS[mensaje]
            client = SoftinmClient()
            info_inmueble = ConsultarInmueblesPorId(inmueble_id)
            if retirar:
                client.retirar_inmueble(inmueble_id)
            else:
                try:
                    fecha_disponible = datetime.now().strftime("%Y-%m-%d")
                    client.actualizar_fecha_disponibilidad(inmueble_id, fecha_disponible)
                    inmueble_local.fecha_disponibilidad = datetime.now()
                    inmueble_local.save()
                except Exception as e:
                    print(f"Error al actualizar fecha de disponibilidad: {e}")
            if not info_inmueble:
                info_inmueble = {"codigo": inmueble_id}
            threading.Thread(target=self.registrar_en_excel, args=(info_inmueble, mensaje, retirar, fecha_disponible if not retirar else None, asesor)).start()

            return Response({
                "mensaje": f"Inmueble {inmueble_id} actualizado correctamente",
                "retirado": retirar,
                "fecha_disponible": fecha_disponible,
                "observacion": mensaje
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def registrar_en_excel(self, inmueble_data, mensaje, retirado, fecha_disponible, asesor):
        print("Iniciando registro en Excel...")

        archivo = "inmuebles_retirados.xlsx"
        hoja = "retiros"

        df_nuevo = pd.DataFrame([{
            "codigo": inmueble_data.get("codigo", ""),
            "direccion": inmueble_data.get("direccion", ""),
            "propietario": inmueble_data.get("propietario", ""),
            "celular": inmueble_data.get("celular", ""),
            "tipo": inmueble_data.get("tipo", ""),
            "precio": inmueble_data.get("valor_canon", 0),
            "gestion": inmueble_data.get("gestion", ""),
            "mensaje": mensaje,
            "retirado": "Sí" if retirado else "No",
            "fecha_disponible": fecha_disponible or "",
            "registrado_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Responsable": asesor
        }])

        try:
            from openpyxl import load_workbook

            if os.path.exists(archivo):
                with pd.ExcelWriter(archivo, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
                    try:
                        # Si ya existe la hoja, cargarla y concatenar
                        df_existente = pd.read_excel(archivo, sheet_name=hoja)
                        df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
                    except ValueError:
                        # La hoja no existe, escribir directamente
                        df_final = df_nuevo

                    df_final.to_excel(writer, sheet_name=hoja, index=False)

            else:
                # Si no existe el archivo, lo creamos con esta hoja
                with pd.ExcelWriter(archivo, engine='openpyxl') as writer:
                    df_nuevo.to_excel(writer, sheet_name=hoja, index=False)

            print("Excel actualizado correctamente en hoja 'retiros'.")

        except Exception as e:
            print(f"Error al manipular Excel: {e}")
            raise

        
        
class CompararValoresView(APIView):
    """
    Compara dos valores numéricos (canon anterior vs. nuevo) y
    devuelve los montos con formato $X.XXX.XXX.

    POST /comparar-valores/
    {
        "valor_a": "$1.850.000",
        "valor_b": "2,200,000"
    }
    """

    def post(self, request):
        try:
            # ---------- helpers ----------
            def limpiar(valor):
                """Convierte texto con $ . , en entero."""
                if not valor or str(valor).strip() == "":
                    return 0
                return int(str(valor)
                           .replace("$", "")
                           .replace(".", "")
                           .replace(",", "")
                           .strip())

            def a_pesos(numero: int) -> str:
                """Formatea entero a $X.XXX.XXX (puntos como miles)."""
                return "${:,.0f}".format(numero).replace(",", ".")

            # ---------- parseo ----------
            valor_a = limpiar(request.data.get("valor_a"))
            valor_b = limpiar(request.data.get("valor_b"))
            diferencia = valor_b - valor_a
            variacion = round((diferencia / valor_a) * 100, 2) if valor_a else 0

            # ---------- respuesta ----------
            resultado = {
                "valor_a": a_pesos(valor_a),
                "valor_b": a_pesos(valor_b),
                "diferencia": a_pesos(diferencia),
                "variacion_porcentual": f"{variacion}%",
            }

            if abs(variacion) > 20:
                resultado["error"] = "La variación supera el límite permitido del 20 %"
                return Response(resultado, status=status.HTTP_400_BAD_REQUEST)

            return Response(resultado, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ContactarPropietarioView(APIView):
    """
    Contacta al asesor a través de WhatsApp con un mensaje predefinido.

    POST /contactar-asesor/
    {
        "inmueble_id": 12475,
        "plantilla": "Atencion_personalizada"
    }
    """
    def post(self, request):
        try:
            inmueble_id = int(request.data.get("inmueble_id"))
            plantilla = request.data.get("plantilla", "Atencion_personalizada")
            info_inmueble = ConsultarInmueblesPorId(inmueble_id)
            if not info_inmueble:
                return Response({"error": "No se encontró información del inmueble"}, status=404)

            notificar_asesor(inmueble_id, plantilla)

            return Response({"mensaje": "Asesor contactado correctamente"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class optenerInmueblesView(APIView):
    """
    Obtiene los inmuebles registrados en la base de datos.

    post 
    {
        "inmueble_id": 12475,
    }
    """
    def post(self, request):
        try:
            inmueble_id = int(request.data.get("inmueble_id"))
            info_inmueble = ConsultarInmueblesPorId(inmueble_id)
            if not info_inmueble:
                return Response({"error": "No se encontró información del inmueble"}, status=404)

            return Response(info_inmueble, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)