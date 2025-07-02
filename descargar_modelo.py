import requests
import os

def descargar_drive(id_archivo, nombre_destino):
    URL = "https://docs.google.com/uc?export=download"
    sesion = requests.Session()

    respuesta = sesion.get(URL, params={'id': id_archivo}, stream=True)

    def obtener_token_confirmacion(resp):
        for key, value in resp.cookies.items():
            if key.startswith('download_warning'):
                return value
        return None

    token = obtener_token_confirmacion(respuesta)
    if token:
        respuesta = sesion.get(URL, params={'id': id_archivo, 'confirm': token}, stream=True)

    with open(nombre_destino, "wb") as f:
        for chunk in respuesta.iter_content(32768):
            if chunk:
                f.write(chunk)

    print(f"✅ Archivo descargado como: {nombre_destino}")

# === DATOS DEL ARCHIVO A DESCARGAR ===
ID = "1XlBVuDtDL8pnziFHxrbqQ06E-uALvKk-"
NOMBRE_SALIDA = "modelo_entrenado_kazu.zip"

descargar_drive(ID, NOMBRE_SALIDA)
