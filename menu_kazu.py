import os
import shutil
import zipfile
import logging
import pyttsx3
import sqlite3
from datetime import datetime
from transformers import GPT2Tokenizer, GPT2LMHeadModel, TextDataset, DataCollatorForLanguageModeling, Trainer, TrainingArguments

# CONFIGURACIÓN
MODELO_DIR = "modelo_kazu_v2"
DATASET = "datos_completo.txt"
MEMORIA_LARGA = "memoria_larga.txt"
APRENDIZAJE_INCREMENTAL = "aprendizaje_incremental.txt"
DB = "kazu_memoria.db"
LOG = "registro_kazu.log"
lineas_ban = ["translate", "see", "definition", "authoritative", "meaning", "in english", "audio pronunciation"]

logging.basicConfig(filename=LOG, level=logging.INFO, format='%(asctime)s - %(message)s')

# ===== FUNCIONES DE MENÚ =====

def crear_respaldo():
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nombre_respaldo = f"respaldo_kazu_{fecha}.zip"
    archivos = [
        DATASET, MEMORIA_LARGA, APRENDIZAJE_INCREMENTAL,
        DB, LOG, "kazu_ia.py", "menu_kazu.py"
    ]
    carpetas = [MODELO_DIR]
    temp = "respaldo_temp"

    if os.path.exists(temp): shutil.rmtree(temp)
    os.makedirs(temp)

    # Copiar archivos individuales
    for archivo in archivos:
        if os.path.exists(archivo):
            shutil.copy(archivo, os.path.join(temp, os.path.basename(archivo)))

    # Copiar carpetas completas
    for carpeta in carpetas:
        if os.path.exists(carpeta):
            shutil.copytree(carpeta, os.path.join(temp, os.path.basename(carpeta)))

    # Copiar todos los .py adicionales que estén en la carpeta actual
    for archivo in os.listdir("."):
        if archivo.endswith(".py") and archivo not in archivos:
            shutil.copy(archivo, os.path.join(temp, archivo))

    # Crear el ZIP y limpiar
    shutil.make_archive(nombre_respaldo.replace(".zip", ""), 'zip', temp)
    shutil.rmtree(temp)

    print(f"✅ Respaldo completo creado: {nombre_respaldo}")

def restaurar_respaldo():
    nombre_zip = input("📦 Escribe el nombre del archivo ZIP de respaldo (incluye '.zip'): ")
    if not os.path.exists(nombre_zip):
        print("❌ Archivo no encontrado.")
        return
    temp = "restauracion_temp"
    if os.path.exists(temp): shutil.rmtree(temp)
    os.makedirs(temp)
    with zipfile.ZipFile(nombre_zip, 'r') as zip_ref:
        zip_ref.extractall(temp)
    for archivo in [DATASET, MEMORIA_LARGA, APRENDIZAJE_INCREMENTAL, DB, LOG]:
        ruta = os.path.join(temp, archivo)
        if os.path.exists(ruta):
            shutil.copy(ruta, archivo)
            print(f"✔ Restaurado: {archivo}")
    for carpeta in [MODELO_DIR]:
        ruta = os.path.join(temp, carpeta)
        if os.path.exists(ruta):
            if os.path.exists(carpeta): shutil.rmtree(carpeta)
            shutil.copytree(ruta, carpeta)
            print(f"✔ Restaurado: {carpeta}")
    shutil.rmtree(temp)
    print("🔁 Restauración completa.")

def limpiar_archivos():
    def limpiar(ruta):
        if not os.path.exists(ruta): return
        with open(ruta, "r", encoding="utf-8") as f:
            lineas = f.readlines()
        limpias = [l.strip() for l in lineas if not any(b in l.lower() for b in lineas_ban) and l.strip()]
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("\n".join(limpias) + "\n")
        logging.info(f"{ruta}: {len(lineas)} -> {len(limpias)} útiles")
    limpiar(DATASET)
    limpiar(MEMORIA_LARGA)
    limpiar(APRENDIZAJE_INCREMENTAL)
    if os.path.exists(DB):
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("DELETE FROM aprendizaje WHERE LOWER(respuesta) LIKE '%translate%' OR LOWER(respuesta) LIKE '%definition%' OR LOWER(respuesta) LIKE '%see%'")
        conn.commit()
        conn.close()
        logging.info("Base de datos limpiada")
    print("🧹 Limpieza completada.")

def configurar_voz():
    engine = pyttsx3.init()
    for voz in engine.getProperty("voices"):
        if "spanish" in voz.name.lower() or "español" in voz.name.lower():
            engine.setProperty("voice", voz.id)
            engine.setProperty("rate", 170)
            engine.setProperty("volume", 1)
            engine.say("Voz en español configurada correctamente.")
            engine.runAndWait()
            logging.info(f"Voz seleccionada: {voz.name}")
            print("🔊 Voz configurada:", voz.name)
            return
    print("⚠ No se encontró voz en español.")
    logging.warning("No se encontró voz en español.")

def reentrenar():
    if not os.path.exists(DATASET):
        print("❌ Dataset no encontrado.")
        return
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    tokenizer.pad_token = tokenizer.eos_token
    dataset = TextDataset(tokenizer=tokenizer, file_path=DATASET, block_size=128)
    collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    model = GPT2LMHeadModel.from_pretrained("gpt2")
    args = TrainingArguments(
        output_dir=MODELO_DIR,
        overwrite_output_dir=True,
        num_train_epochs=1,
        per_device_train_batch_size=2,
        save_steps=500,
        save_total_limit=1,
        logging_steps=10
    )
    trainer = Trainer(model=model, args=args, data_collator=collator, train_dataset=dataset)
    trainer.train()
    trainer.save_model(MODELO_DIR)
    tokenizer.save_pretrained(MODELO_DIR)
    print("📈 Reentrenamiento completado.")
    logging.info("Modelo reentrenado y guardado.")

def diagnostico():
    print("\n== DIAGNÓSTICO DE KAZU_IA ==")
    print("1. Modelo:")
    for f in ["config.json", "pytorch_model.bin", "vocab.json", "merges.txt"]:
        print(f"  {'✔' if os.path.exists(os.path.join(MODELO_DIR, f)) else '✘'} {f}")
    print("\n2. Archivos:")
    for archivo in [DATASET, MEMORIA_LARGA, APRENDIZAJE_INCREMENTAL]:
        existe = os.path.exists(archivo)
        print(f"  {'✔' if existe else '✘'} {archivo}", end="")
        if existe:
            print(f" ({os.path.getsize(archivo)} bytes)")
        else:
            print()
    print("\n3. Base de datos:")
    if os.path.exists(DB):
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        for tabla in ["notas", "lista_compras", "aprendizaje"]:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {tabla}")
                total = cur.fetchone()[0]
                print(f"  ✔ {tabla} ({total} registros)")
            except: print(f"  ✘ {tabla} no encontrada")
        conn.close()
    else:
        print("  ✘ Base de datos no encontrada.")
    print("\nRecomendaciones: Revisa la voz, elimina basura, entrena frecuentemente.")

# ===== MENÚ =====
def menu():
    while True:
        print("\n==== MENÚ DE KAZU_IA ====")
        print("1. 🔁 Restaurar respaldo")
        print("2. 💾 Crear respaldo")
        print("3. 🧹 Limpiar archivos y base de datos")
        print("4. 📈 Reentrenar modelo")
        print("5. 🔍 Diagnóstico general")
        print("6. 🚪 Salir")
        opcion = input("Selecciona una opción: ")
        if opcion == "1":
            restaurar_respaldo()
        elif opcion == "2":
            crear_respaldo()
        elif opcion == "3":
            limpiar_archivos()
            configurar_voz()
        elif opcion == "4":
            reentrenar()
        elif opcion == "5":
            diagnostico()
        elif opcion == "6":
            print("👋 Saliendo...")
            break
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    menu()
