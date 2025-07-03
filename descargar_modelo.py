import requests
import os
from tqdm import tqdm

def descargar_drive(id_archivo, nombre_destino):
    URL = "https://docs.google.com/uc?export=download"
    sesion = requests.Session()

    print(f"📥 Iniciando descarga del archivo ID: {id_archivo}")

    respuesta = sesion.get(URL, params={'id': id_archivo}, stream=True)
    token = _obtener_token_confirmacion(respuesta)

    if token:
        params = {'id': id_archivo, 'confirm': token}
        respuesta = sesion.get(URL, params=params, stream=True)

    _guardar_archivo(respuesta, nombre_destino)
    print(f"✅ Archivo descargado correctamente como: {nombre_destino}")

def _obtener_token_confirmacion(respuesta):
    for key, value in respuesta.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None

def _guardar_archivo(respuesta, nombre_destino):
    total = int(respuesta.headers.get('content-length', 0))
    progreso = tqdm(total=total, unit='B', unit_scale=True, desc=nombre_destino)

    with open(nombre_destino, "wb") as f:
        for chunk in respuesta.iter_content(32768):
            if chunk:
                f.write(chunk)
                progreso.update(len(chunk))
    progreso.close()

# === DATOS DEL ARCHIVO A DESCARGAR ===
if __name__ == "__main__":
    ID = "1XlBVuDtDL8pnziFHxrbqQ06E-uALvKk-"
    NOMBRE_SALIDA = "modelo_entrenado_kazu.zip"
    descargar_drive(ID, NOMBRE_SALIDA)
