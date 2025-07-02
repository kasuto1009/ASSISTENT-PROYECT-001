import os
import sqlite3
import json
import re

# Rutas y archivos importantes
modelo_path = "modelo_kazu_v2"
archivos_modelo = ["config.json", "pytorch_model.bin", "vocab.json", "merges.txt"]
archivos_memoria = ["memoria_larga.txt", "datos_completo.txt", "aprendizaje_incremental.txt"]
base_datos = "kazu_memoria.db"
script_principal = "kazu_ia.py"

diagnostico = []
diagnostico.append("== DIAGNÓSTICO COMPLETO DE KAZU_IA ==\n")

# --- 1. Modelo personalizado ---
diagnostico.append("** 1. Verificación del modelo personalizado:")
if os.path.isdir(modelo_path):
    for archivo in archivos_modelo:
        ruta = os.path.join(modelo_path, archivo)
        if os.path.isfile(ruta):
            diagnostico.append(f"✔ {archivo} encontrado.")
            # Validar vocab.json por JSON válido
            if archivo == "vocab.json":
                try:
                    with open(ruta, "r", encoding="utf-8") as f:
                        json.load(f)
                    diagnostico.append("  - vocab.json es un JSON válido.")
                except Exception as e:
                    diagnostico.append(f"  - ERROR: vocab.json inválido o corrupto: {e}")
        else:
            diagnostico.append(f"✘ {archivo} NO encontrado.")
else:
    diagnostico.append(f"✘ Carpeta del modelo '{modelo_path}' no encontrada.")

# --- 2. Archivos de memoria y dataset ---
diagnostico.append("\n** 2. Verificación de archivos de memoria y dataset:")
for archivo in archivos_memoria:
    if os.path.isfile(archivo):
        size = os.path.getsize(archivo)
        diagnostico.append(f"✔ {archivo} encontrado ({size} bytes).")
        # Análisis simple para detectar basura o líneas problemáticas
        with open(archivo, "r", encoding="utf-8", errors="ignore") as f:
            lineas = f.readlines()
        # Detectar líneas vacías y líneas con "Translate" u otros patrones problemáticos
        basura = [line for line in lineas if re.search(r"translate|see|meaning|in english|traducir", line, re.I)]
        if basura:
            diagnostico.append(f"  - ALERTA: {len(basura)} líneas potencialmente basura detectadas en {archivo}.")
        else:
            diagnostico.append(f"  - {archivo} parece limpio de líneas basura comunes.")
    else:
        diagnostico.append(f"✘ {archivo} NO encontrado.")

# --- 3. Base de datos ---
diagnostico.append("\n** 3. Verificación de la base de datos SQLite:")
if os.path.isfile(base_datos):
    try:
        conn = sqlite3.connect(base_datos)
        cursor = conn.cursor()
        tablas = ["notas", "lista_compras", "aprendizaje"]
        for tabla in tablas:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tabla}'")
            existe = cursor.fetchone()
            if existe:
                diagnostico.append(f"✔ Tabla '{tabla}' existe.")
                # Recuento filas básicas
                cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                total = cursor.fetchone()[0]
                diagnostico.append(f"  - Contiene {total} registros.")
            else:
                diagnostico.append(f"✘ Tabla '{tabla}' NO existe.")
        conn.close()
    except Exception as e:
        diagnostico.append(f"✘ Error abriendo base de datos: {e}")
else:
    diagnostico.append(f"✘ Archivo '{base_datos}' NO encontrado.")

# --- 4. Revisión de dataset completo para duplicados ---
diagnostico.append("\n** 4. Revisión de duplicados en datos_completo.txt:")
archivo_dataset = "datos_completo.txt"
if os.path.isfile(archivo_dataset):
    with open(archivo_dataset, "r", encoding="utf-8", errors="ignore") as f:
        contenido = f.read()
    entradas = re.findall(r"<\|usuario\|>:(.*?)<\|asistente\|>:(.*?)(?=(<\|usuario\|>:|$))", contenido, re.S)
    if entradas:
        preguntas = [p[0].strip() for p in entradas]
        total_entradas = len(preguntas)
        unicas = len(set(preguntas))
        diagnostico.append(f"  - Total de entradas: {total_entradas}")
        diagnostico.append(f"  - Entradas únicas: {unicas}")
        if total_entradas > unicas:
            diagnostico.append(f"  - ALERTA: Hay {total_entradas - unicas} entradas duplicadas que pueden ser limpiadas.")
        else:
            diagnostico.append("  - No se detectaron entradas duplicadas.")
    else:
        diagnostico.append("  - No se detectaron entradas formateadas correctamente en el dataset.")
else:
    diagnostico.append(f"✘ Archivo '{archivo_dataset}' NO encontrado.")

# --- 5. Análisis del script principal (kazu_ia.py) ---
diagnostico.append("\n** 5. Análisis básico del script principal 'kazu_ia.py':")
if os.path.isfile(script_principal):
    with open(script_principal, "r", encoding="utf-8", errors="ignore") as f:
        codigo = f.read()
    # Buscar funciones y comandos clave
    funciones_clave = ["hablar", "responder_con_ia", "procesar_comando", "generar_respuesta_ia", "guardar_en_memoria"]
    comandos_personalizados = ["hora en japón", "abre youtube", "hora", "chiste", "anota esto", "muestra notas", "agrega a la lista", "muestra lista"]
    for fn in funciones_clave:
        if fn in codigo:
            diagnostico.append(f"✔ Función '{fn}' encontrada.")
        else:
            diagnostico.append(f"✘ Función '{fn}' NO encontrada, revisa implementación.")
    # Revisión básica de comandos personalizados
    encontrados = [cmd for cmd in comandos_personalizados if cmd in codigo.lower()]
    if encontrados:
        diagnostico.append(f"✔ Comandos personalizados detectados: {', '.join(encontrados)}")
    else:
        diagnostico.append("✘ No se detectaron comandos personalizados comunes.")
    # Revisión de configuración voz pyttsx3
    if "pyttsx3" in codigo.lower():
        diagnostico.append("✔ Se usa pyttsx3 para voz.")
        # Buscar si hay configuración de voz en español
        if re.search(r"voz\.setProperty\(\s*['\"]voice['\"]\s*,\s*['\"].*spanish.*['\"]\s*\)", codigo, re.I):
            diagnostico.append("✔ Voz configurada para idioma español.")
        else:
            diagnostico.append("⚠ No se detectó configuración explícita para voz en español, revisa para mejor naturalidad.")
else:
    diagnostico.append(f"✘ Archivo '{script_principal}' NO encontrado.")

# --- 6. Recomendaciones generales ---
diagnostico.append("\n** 6. Recomendaciones y conclusiones:")
diagnostico.append("- Limpia líneas basura o traducciones automáticas de archivos de memoria y dataset para evitar respuestas erróneas.")
diagnostico.append("- Revisa y corrige entradas duplicadas en el dataset para mejorar coherencia del modelo.")
diagnostico.append("- Asegúrate de que el vocab.json y merges.txt estén íntegros y sin errores JSON o formato.")
diagnostico.append("- Configura pyttsx3 para usar voces naturales en español latinoamericano o México para mejor experiencia.")
diagnostico.append("- Mantén la base de datos con integridad y revisa que todas las tablas necesarias existan.")
diagnostico.append("- Añade manejo de errores para evitar que la IA responda con traducciones automáticas no deseadas.")
diagnostico.append("- Considera un sistema automático de limpieza de dataset y memoria periódicamente.")
diagnostico.append("- Implementa logs para detectar cuándo ocurren respuestas inválidas o bloqueadas.")

# Guardar diagnóstico
nombre_archivo = "diagnostico_completo_kazu.txt"
with open(nombre_archivo, "w", encoding="utf-8") as f:
    f.write("\n".join(diagnostico))

print(f"Diagnóstico completo generado en '{nombre_archivo}'.")
