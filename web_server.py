# web_server.py
from flask import Flask, request, jsonify
from kazu_ia import procesar_comando  # Tu archivo kazu_ia adaptado

app = Flask(__name__)

@app.route("/responder", methods=["POST"])
def responder():
    data = request.get_json()
    entrada = data.get("texto", "")
    respuesta = procesar_comando(entrada, solo_texto=True)  # Ajusta kazu_ia para esto
    return jsonify({"respuesta": respuesta})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
