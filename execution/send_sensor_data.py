#!/usr/bin/env python3
import requests
import time
import random
import json

# CONFIGURACIÓN
# Cambia esto por la URL directa de tu API en Hugging Face
# Normalmente es: https://<usuario>-<nombre-espacio>.hf.space
API_URL = "https://cero2k6-agente-agro-inteligente.hf.space/api/update_crop"

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
        resp = requests.post(API_URL, json=payload, timeout=5)
        print(f"✅ Datos enviados: {payload} | Respuesta: {resp.status_code}")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        
    time.sleep(5) # Enviar cada 5 segundos