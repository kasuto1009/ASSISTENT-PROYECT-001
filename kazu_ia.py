import pyttsx3, datetime, sqlite3, random, requests, os, json, webbrowser
from duckduckgo_search import DDGS
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import menu_kazu

# Configuración
MODELO_BASE = "./modelo_kazu_v2"
SERPAPI_KEY = "35da2325f00338592839e0e2c0cf3bf18ba184008f6bbca23d1ae196a79ccb65"
MEMORIA_LARGA = "memoria_larga.txt"
DATASET_TXT = "datos_completo.txt"

print(f"[Kazu_ia] Usando modelo fijo: {MODELO_BASE}")
tokenizer = AutoTokenizer.from_pretrained(MODELO_BASE)
modelo = AutoModelForCausalLM.from_pretrained(MODELO_BASE)
modelo_ia = pipeline("text-generation", model=modelo, tokenizer=tokenizer, device=0)

# Voz
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
    prohibidas = [
        "translate", "definition", "pronunciation", "meaning", "see", "example sentences",
        "in english", "diccionario", "spanishdict", "wordreference", "authoritative translations",
        "audio pronunciations", "learn", "see translations", "english version"
    ]
    return any(p in texto for p in prohibidas)

def generar_respuesta_ia(pregunta):
    pregunta_limpia = pregunta.strip()
    prompt = f"""Eres Kazu_ia, un asistente amigable y casual con estilo ecuatoriano. Responde en español, de forma completa y natural, usando lenguaje cercano y coloquial.

Usuario: {pregunta_limpia}
Kazu_ia:"""

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
    inputs = {k: v.to(modelo.device) for k, v in inputs.items()}

    for _ in range(3):
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
        if len(respuesta) >= 50 and not respuesta_invalida(respuesta):
            return respuesta

    return "Perdona, mi pana, no entendí bien tu pregunta. ¿Puedes reformularla?"

def procesar_comando(e, solo_texto=False):
    e = e.lower().strip()
    if e in ["hola", "buenas", "qué tal"]:
        respuesta = random.choice(respuestas_predefinidas["saludos"])
    elif e in ["cómo estás", "como estas"]:
        respuesta = random.choice(respuestas_predefinidas["como_estas"])
    elif e in ["bien y tú", "bien y tu"]:
        respuesta = random.choice(respuestas_predefinidas["bien_y_tu"])
    elif e in ["quién eres", "quien eres"]:
        respuesta = random.choice(respuestas_predefinidas["quien_eres"])
    elif "hora en japón" in e or "hora en japon" in e:
        ahora = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
        respuesta = f"En Japón son las {ahora.strftime('%H:%M')}"
    elif "hora" in e:
        respuesta = datetime.datetime.now().strftime("Son las %H:%M")
    elif "chiste" in e:
        respuesta = random.choice(respuestas_predefinidas["bromas"])
    elif "anota esto" in e:
        nota = e.replace("anota esto", "").strip()
        if nota:
            cursor.execute("INSERT INTO notas (texto) VALUES (?)", (nota,))
            conexion.commit()
            respuesta = "He anotado eso, mi pana."
        else:
            respuesta = "¿Qué quieres que anote?"
    elif "muestra notas" in e:
        notas = cursor.execute("SELECT texto FROM notas").fetchall()
        respuesta = "Tus notas:\n" + "\n".join("- " + n[0] for n in notas) if notas else "No tienes notas guardadas."
    elif "agrega a la lista" in e:
        prod = e.replace("agrega a la lista", "").strip()
        if prod:
            cursor.execute("INSERT INTO lista_compras (producto) VALUES (?)", (prod,))
            conexion.commit()
            respuesta = f"{prod} añadido a la lista."
        else:
            respuesta = "¿Qué quieres agregar?"
    elif "muestra lista" in e:
        productos = cursor.execute("SELECT producto FROM lista_compras").fetchall()
        respuesta = "Tu lista de compras:\n" + "\n".join("- " + p[0] for p in productos) if productos else "Tu lista está vacía."
    elif e in ["panel admin", "abrir panel"]:
        respuesta = "El panel no está disponible desde la web."
    else:
        guardada = buscar_en_memoria(e)
        if guardada:
            respuesta = guardada
        else:
            resultado_web = buscar_serpapi(e) or buscar_ddg(e)
            if resultado_web:
                respuesta = resultado_web
            else:
                respuesta = generar_respuesta_ia(e)
            guardar_en_memoria(e, respuesta)

    if solo_texto:
        return respuesta
    else:
        hablar(respuesta)
        return True

def iniciar_kazu():
    hablar("Hola, soy tu asistente personal. ¿En qué puedo ayudarte hoy, mi pana?")
    while True:
        entrada = input("Tú: ")
        if entrada.lower() == "salir":
            hablar("¡Hasta pronto, pilas!")
            break
        procesar_comando(entrada)

if __name__ == "__main__":
    iniciar_kazu()

