import pyttsx3, datetime, sqlite3, random, requests, os, json, webbrowser
from duckduckgo_search import DDGS
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import menu_kazu


# Configuración
MODELO_BASE = "modelo_kazu_v2"
SERPAPI_KEY = "tu_clave_aquí"
MEMORIA_LARGA = "memoria_larga.txt"
DATASET_TXT = "datos_completo.txt"

print(f"[Kazu_ia] Usando modelo fijo: {MODELO_BASE}")
tokenizer = AutoTokenizer.from_pretrained(MODELO_BASE)
modelo = AutoModelForCausalLM.from_pretrained(MODELO_BASE)
modelo_ia = pipeline("text-generation", model=modelo, tokenizer=tokenizer, device=0)


# Voz (selección femenina en español segura)
voz = pyttsx3.init()
voz.setProperty("rate", 170)
voz.setProperty("volume", 1)

def seleccionar_voz_femenina_esp(engine):
    voces = engine.getProperty('voices')
    for v in voces:
        nombre = v.name.lower()
        idioma = ""
        try:
            if v.languages and len(v.languages) > 0:
                idioma = v.languages[0]
                if isinstance(idioma, bytes):
                    idioma = idioma.decode('utf-8')
        except:
            idioma = ""

        if ("es" in idioma or "spanish" in idioma or "español" in nombre) and any(n in nombre for n in ["mark"]):
            engine.setProperty("voice", v.id)
            print(f"[Kazu_ia] Voz seleccionada: {v.name}")
            return
    print("[Kazu_ia] Voz femenina en español no encontrada, usando predeterminada.")

seleccionar_voz_femenina_esp(voz)

# Base de datos
conexion = sqlite3.connect("kazu_memoria.db")
cursor = conexion.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS notas (id INTEGER PRIMARY KEY, texto TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS lista_compras (id INTEGER PRIMARY KEY, producto TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS aprendizaje (pregunta TEXT PRIMARY KEY, respuesta TEXT)")
conexion.commit()

# Respuestas predefinidas (estilo casual)
respuestas_predefinidas = {
    "saludos": ["¡Hola, mi pana! ¿Cómo estás? ¿Pilas?", "¡Buenas! ¿Qué tal todo, mi pana?"],
    "como_estas": ["Estoy pilas, gracias por preguntar. ¡Y tú qué cuentas!", "Todo chévere por aquí, ¿y tú?"],
    "quien_eres": ["Soy Kazu_ia, tu asistente inteligente y pana con estilo ecuatoriano. Siempre listo para ayudarte, ¡una locura!"],
    "bien_y_tu": ["¡Me alegra! Yo también estoy bien, mi pana.", "Contento de hablar contigo, pilas siempre."],
    "bromas": ["¿Por qué los programadores confunden Halloween con Navidad? Porque OCT 31 = DEC 25, ¡una locura!"]
}

def hablar(texto):
    print(f"Kazu_ia: {texto}")
    voz.say(texto)
    voz.runAndWait()

def guardar_memoria_larga(pregunta, respuesta):
    with open(MEMORIA_LARGA, "a", encoding="utf-8") as f:
        f.write(f"Usuario: {pregunta.strip()}\nKazu_ia: {respuesta.strip()}\n\n")

def agregar_a_dataset(pregunta, respuesta):
    nueva_entrada = f"<|usuario|>: {pregunta.strip()}\n<|asistente|>: {respuesta.strip()}\n"
    if not os.path.exists(DATASET_TXT):
        with open(DATASET_TXT, "w", encoding="utf-8") as f:
            f.write(nueva_entrada)
    else:
        with open(DATASET_TXT, "r", encoding="utf-8") as f:
            contenido = f.read()
        if nueva_entrada not in contenido:
            with open(DATASET_TXT, "a", encoding="utf-8") as f2:
                f2.write(nueva_entrada)

def obtener_hora():
    hablar(datetime.datetime.now().strftime("Son las %H:%M"))

def obtener_hora_japon():
    ahora = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    hablar(f"En Japón son las {ahora.strftime('%H:%M')}")

def contar_chiste():
    hablar(random.choice(respuestas_predefinidas["bromas"]))

def abrir_youtube():
    webbrowser.open("https://youtube.com")
    hablar("Abriendo YouTube...")

def anotar(texto):
    nota = texto.replace("anota esto", "").strip()
    if nota:
        cursor.execute("INSERT INTO notas (texto) VALUES (?)", (nota,))
        conexion.commit()
        hablar("He anotado eso, mi pana.")
    else:
        hablar("¿Qué quieres que anote?")

def mostrar_notas():
    notas = cursor.execute("SELECT texto FROM notas").fetchall()
    if notas:
        hablar("Aquí tienes tus notas, pilas:")
        for n in notas:
            print("- " + n[0])
    else:
        hablar("No tienes notas guardadas.")

def agregar_lista(texto):
    prod = texto.replace("agrega a la lista", "").strip()
    if prod:
        cursor.execute("INSERT INTO lista_compras (producto) VALUES (?)", (prod,))
        conexion.commit()
        hablar(f"{prod} añadido a la lista, ¡una locura!")
    else:
        hablar("¿Qué quieres agregar?")

def mostrar_lista():
    productos = cursor.execute("SELECT producto FROM lista_compras").fetchall()
    if productos:
        hablar("Tu lista de compras, pilas:")
        for p in productos:
            print("- " + p[0])
    else:
        hablar("Tu lista está vacía.")

def buscar_en_memoria(pregunta):
    row = cursor.execute("SELECT respuesta FROM aprendizaje WHERE pregunta=?", (pregunta,)).fetchone()
    return row[0] if row else None

def guardar_en_memoria(pregunta, respuesta):
    cursor.execute("INSERT OR REPLACE INTO aprendizaje (pregunta, respuesta) VALUES (?, ?)", (pregunta, respuesta))
    conexion.commit()
    guardar_memoria_larga(pregunta, respuesta)
    agregar_a_dataset(pregunta, respuesta)

def buscar_ddg(query):
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=3):
            if r.get("body") and "wikipedia" not in r.get("href", "").lower():
                return r["body"]
    return None

def buscar_serpapi(query):
    if not SERPAPI_KEY:
        return None
    try:
        r = requests.get("https://serpapi.com/search.json", params={
            "q": query, "engine": "google", "api_key": SERPAPI_KEY
        }).json()
        for item in r.get("organic_results", []):
            if item.get("snippet") and "wikipedia.org" not in item.get("link", ""):
                return item["snippet"]
    except:
        return None
    return None

def respuesta_invalida(texto):
    if not texto:
        return True
    texto = texto.lower()
    palabras_prohibidas = [
        "translate", "definition", "pronunciation", "meaning", "see", "example sentences",
        "in english", "diccionario", "spanishdict", "wordreference", "authoritative translations",
        "audio pronunciations", "learn", "see translations", "english version"
    ]
    return any(p in texto for p in palabras_prohibidas)

def generar_respuesta_ia(pregunta):
    pregunta_limpia = pregunta.strip()

    if "quién eres" in pregunta_limpia.lower() or "quien eres" in pregunta_limpia.lower():
        return random.choice(respuestas_predefinidas["quien_eres"])

    if "dime un poema de amor" in pregunta_limpia.lower():
        return (
            "Claro, mi pana, aquí te va un poema de amor corto:\n\n"
            "El amor es un fuego que arde sin verse,\n"
            "es herida que duele y no se siente,\n"
            "es un contento descontente,\n"
            "es un dolor que desatina sin dolerse."
        )

    if "qué sabes sobre computación" in pregunta_limpia.lower() or "que sabes sobre computación" in pregunta_limpia.lower():
        return (
            "Computación es la ciencia y tecnología que estudia el procesamiento automático de la información "
            "usando computadoras y sistemas. Incluye programación, hardware, redes y más, mi pana."
        )

    prompt = f"""Eres Kazu_ia, un asistente amigable y casual con estilo ecuatoriano. Responde en español, de forma completa y natural, usando lenguaje cercano y coloquial.

Usuario: {pregunta_limpia}
Kazu_ia:"""

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
    inputs = {k: v.to(modelo.device) for k, v in inputs.items()}

    max_intentos = 3
    intentos = 0
    respuesta = ""
    while intentos < max_intentos:
        salida = modelo.generate(
            **inputs,
            max_new_tokens=150,
            pad_token_id=tokenizer.eos_token_id,
            do_sample=True,
            top_p=0.9,
            temperature=0.7,
            no_repeat_ngram_size=3
        )
        respuesta = tokenizer.decode(salida[0], skip_special_tokens=True).strip()
        if respuesta.startswith(prompt):
            respuesta = respuesta[len(prompt):].strip()
        if (len(respuesta) >= 50 and
            not respuesta.lower().startswith(pregunta_limpia.lower()) and
            not respuesta_invalida(respuesta)):
            break
        intentos += 1

    if respuesta_invalida(respuesta):
        respuesta = "Perdona, mi pana, no entendí bien tu pregunta. ¿Puedes reformularla?"

    return respuesta

def responder_con_ia(texto):
    texto = texto.lower().strip()

    if texto in ["hola", "buenas", "qué tal"]:
        hablar(random.choice(respuestas_predefinidas["saludos"]))
        return
    if texto in ["cómo estás", "como estas"]:
        hablar(random.choice(respuestas_predefinidas["como_estas"]))
        return
    if texto in ["bien y tú", "bien y tu"]:
        hablar(random.choice(respuestas_predefinidas["bien_y_tu"]))
        return
    if texto in ["quién eres", "quien eres"]:
        hablar(random.choice(respuestas_predefinidas["quien_eres"]))
        return

    guardada = buscar_en_memoria(texto)
    if guardada:
        hablar(guardada)
        return

    resultado_web = buscar_serpapi(texto) or buscar_ddg(texto)
    if resultado_web:
        hablar(resultado_web)
        guardar_en_memoria(texto, resultado_web)
        return

    respuesta = generar_respuesta_ia(texto)
    hablar(respuesta)
    guardar_en_memoria(texto, respuesta)

def procesar_comando(e):
    e = e.lower().strip()
    if "hora en japón" in e or "hora en japon" in e:
        obtener_hora_japon()
    elif "abre youtube" in e:
        abrir_youtube()
    elif "hora" in e:
        obtener_hora()
    elif "chiste" in e:
        contar_chiste()
    elif "anota esto" in e:
        anotar(e)
    elif "muestra notas" in e:
        mostrar_notas()
    elif "agrega a la lista" in e:
        agregar_lista(e)
    elif "muestra lista" in e:
        mostrar_lista()
    elif e == "panel admin" or e == "abrir panel":
        menu_kazu.menu()    # <-- Aquí corregí indentación (debe estar indentado)
    else:
        responder_con_ia(e)
    return True

def iniciar_kazu():
    hablar("Hola, soy asistente personal. ¿En qué puedo ayudarte hoy, mi pana?")
    while True:
        entrada = input("Tú: ")
        if entrada.lower() == "salir":
            hablar("¡Hasta pronto, pilas!")
            break
        procesar_comando(entrada)

if __name__ == "__main__":
    iniciar_kazu()