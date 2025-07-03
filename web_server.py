# web_server.py
import os
from flask import Flask, request, jsonify

# 1. Descarga y descomprime el modelo si no existe
if not os.path.exists("modelo_kazu_v2"):
    from descargar_modelo import descargar_drive, descomprimir

    ID = "1FrZEz6_QPFcVxxNbHkR9UAUjNglYxFBF"
    ZIP = "modelo_kazu_v2.zip"

    descargar_drive(ID, ZIP)
    descomprimir(ZIP)
    os.remove(ZIP)

# 2. Importa la IA
from kazu_ia import procesar_comando  # Asegúrate de que acepte el argumento solo_texto

# 3. Inicializa la app web
app = Flask(__name__)

@app.route("/responder", methods=["POST"])
def responder():
    data = request.get_json()
    entrada = data.get("texto", "")
    respuesta = procesar_comando(entrada, solo_texto=True)  # Retorna string directamente
    return jsonify({"respuesta": respuesta})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

