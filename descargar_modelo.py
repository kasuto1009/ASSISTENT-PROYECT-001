import requests
import zipfile
import os
import shutil

# === CONFIGURACIÓN ===
ID = "1FrZEz6_QPFcVxxNbHkR9UAUjNglYxFBF"  # ID de tu modelo_kazu_v2.zip en Google Drive
NOMBRE_ZIP = "modelo_kazu_v2.zip"
CARPETA_DESTINO = "./"

def descargar_drive(id_archivo, nombre_destino):
    print("[Descarga] Descargando archivo desde Google Drive...")
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()

    # Paso 1: obtener posible token
    respuesta = session.get(URL, params={'id': id_archivo}, stream=True)
    token = None
    for key, value in respuesta.cookies.items():
        if key.startswith('download_warning'):
            token = value

    # Paso 2: si hay token, descargar con confirmación
    if token:
        respuesta = session.get(URL, params={'id': id_archivo, 'confirm': token}, stream=True)

    # Paso 3: escribir archivo binario
    with open(nombre_destino, "wb") as f:
        for chunk in respuesta.iter_content(32768):
            if chunk:
                f.write(chunk)

    print(f"✅ Archivo descargado como: {nombre_destino}")

def descomprimir(zip_path):
    print(f"[Descompresión] Extrayendo {zip_path} en {CARPETA_DESTINO}...")
    if not zipfile.is_zipfile(zip_path):
        raise zipfile.BadZipFile(f"{zip_path} no es un archivo ZIP válido")

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(CARPETA_DESTINO)

    print("✅ Descompresión completada.")

# === EJECUCIÓN ===
if not os.path.exists(NOMBRE_ZIP):
    descargar_drive(ID, NOMBRE_ZIP)

descomprimir(NOMBRE_ZIP)

