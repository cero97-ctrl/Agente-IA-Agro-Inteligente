#!/usr/bin/env python3
import requests
import time
import random
import json
import os
from dotenv import load_dotenv

# Cargar variables de entorno del archivo .env local
load_dotenv()

# CONFIGURACIÓN
# Cambia esto por la URL directa de tu API en Hugging Face
# Normalmente es: https://<usuario>-<nombre-espacio>.hf.space
API_URL = "https://cero2k6-agente-agro-inteligente.hf.space/api/update_crop"

# La clave secreta para autenticar con el servidor. Debe estar en tu .env local.
API_KEY = os.getenv("SENSOR_API_KEY")
if not API_KEY:
    print("❌ Error: La variable SENSOR_API_KEY no está definida en tu archivo .env local.")
    exit()

# El ID del cultivo que quieres conectar (debe existir en la web primero)
CROP_ID = "CULT-001" 

print(f"📡 Iniciando transmisor de sensores para {CROP_ID}...")
print(f"🔗 Destino: {API_URL}")

while True:
    # --- AQUÍ LEERÍAS TUS SENSORES REALES ---
    # Ejemplo: humidity = sensor.read_humidity()
    
    # Por ahora, generamos datos "reales" desde tu PC
    real_humidity = random.uniform(45, 55) 
    real_temp = random.uniform(22, 24)
    
    payload = {
        "crop_id": CROP_ID,
        "humidity": round(real_humidity, 1),
        "temperature": round(real_temp, 1),
        "ph": 6.8,
        "pest_detected": None
    }
    
    try:
        headers = {"X-API-Key": API_KEY}
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=5)
        if resp.status_code == 200:
            print(f"✅ Datos enviados: {payload} | Respuesta: {resp.status_code}")
        else:
            print(f"❌ Error del servidor: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        
    time.sleep(5) # Enviar cada 5 segundos