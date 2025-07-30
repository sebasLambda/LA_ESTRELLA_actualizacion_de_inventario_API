import os
import pandas as pd
from datetime import datetime


def registrar_cambio_precio(self, inmueble_data, precio_anterior, precio_nuevo):
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
            "registrado_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        
def registrar_en_excel(self, inmueble_data, mensaje, retirado, fecha_disponible):
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
            "registrado_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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