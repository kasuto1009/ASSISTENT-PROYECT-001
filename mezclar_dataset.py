import os

# Archivos
archivo_base = "datos_completo.txt"
archivos_fuente = [
    "aprendizaje_incremental.txt",
    "memoria_larga.txt"
]  # Agrega aquí los archivos que quieras mezclar

mezclas_agregadas = 0

# Leer el archivo base
if os.path.exists(archivo_base):
    with open(archivo_base, "r", encoding="utf-8") as f:
        contenido_base = f.read()
else:
    contenido_base = ""
    with open(archivo_base, "w", encoding="utf-8") as f:
        pass  # Crea el archivo vacío si no existe

# Procesar cada archivo fuente
for archivo in archivos_fuente:
    if not os.path.exists(archivo):
        print(f"[⚠️] No se encontró: {archivo}")
        continue

    print(f"[📥] Mezclando contenido desde {archivo}...")
    with open(archivo, "r", encoding="utf-8") as f:
        bloques = f.read().strip().split("\n\n")

    nuevos_bloques = []
    for bloque in bloques:
        if bloque.strip() and bloque not in contenido_base:
            nuevos_bloques.append(bloque.strip())
            mezclas_agregadas += 1

    with open(archivo_base, "a", encoding="utf-8") as f:
        for bloque in nuevos_bloques:
            f.write("\n" + bloque + "\n\n")

print(f"\n✅ Mezcla completada.")
print(f"🧠 Nuevos bloques añadidos a {archivo_base}: {mezclas_agregadas}")
