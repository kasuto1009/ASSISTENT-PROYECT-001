import requests, os, zipfile

def descargar_drive(id_archivo, nombre_destino):
    print(f"[Descarga] Descargando archivo desde Google Drive...")
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

    print(f"[Descarga] Archivo descargado como: {nombre_destino}")

def descomprimir(zip_path, destino="./"):
    print(f"[Descompresión] Extrayendo {zip_path} en {destino}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(destino)
    print("[Descompresión] Hecho.")

# === DATOS DEL ARCHIVO A DESCARGAR ===
ID = "1FrZEz6_QPFcVxxNbHkR9UAUjNglYxFBF"
NOMBRE_ZIP = "modelo_kazu_v2.zip"

if not os.path.exists("modelo_kazu_v2"):
    descargar_drive(ID, NOMBRE_ZIP)
    descomprimir(NOMBRE_ZIP)
    os.remove(NOMBRE_ZIP)
else:
    print("[✔️] El modelo ya está descargado.")
