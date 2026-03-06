import os
import sys
import json
import subprocess
import shutil
import uuid
import asyncio
import time
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional

# Cargar variables de entorno
load_dotenv()

app = FastAPI(title="Agente Agro-Inteligente API")

# Configuración CORS para permitir peticiones desde el navegador (index.html)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CROPS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tmp", "telegram_crops.json")

def run_tool(script_name, args):
    """Helper para ejecutar scripts de la carpeta execution/"""
    # Asumimos que web_server.py está en la raíz del proyecto
    base_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(base_dir, "execution", script_name)
    
    if not os.path.exists(script_path):
        return {"status": "error", "message": f"Script no encontrado: {script_path}"}

    cmd = [sys.executable, script_path] + args
    
    try:
        # Ejecutar script y capturar salida
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        # Intentar parsear la salida como JSON (estándar del framework)
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            # Si falla y hubo error en stderr, devolver eso
            if result.returncode != 0:
                return {"status": "error", "message": result.stderr.strip()}
            # Si no, devolver stdout como texto plano
            return {"status": "success", "content": result.stdout.strip()}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/chat")
async def chat_endpoint(message: str = Form(...), file: Optional[UploadFile] = File(None)):
    print(f"Recibido: {message}")
    if file:
        print(f"Archivo recibido en backend: {file.filename}, Tipo: {file.content_type}")
    else:
        print("Archivo NO recibido en backend.")
    image_path = None
    if file:
        # Guardar la imagen temporalmente
        file_ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4()}{file_ext}"
        save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tmp", "uploads")
        os.makedirs(save_dir, exist_ok=True)
        image_path = os.path.join(save_dir, filename)
        
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"Imagen recibida y guardada en: {image_path}")

    # --- INTERCEPTOR DE COMANDOS (Lógica del Agente) ---
    # Antes de llamar al LLM, verificamos si es un comando de acción directa
    msg_clean = message.strip()
    
    if msg_clean.startswith("/nuevo_cultivo"):
        try:
            parts = msg_clean.split(" ", 1)
            if len(parts) < 2:
                return {"reply": "⚠️ Uso: /nuevo_cultivo [Nombre/Variedad]"}
            
            new_name = parts[1].strip()
            
            # Leer cultivos actuales
            crops = {}
            if os.path.exists(CROPS_FILE):
                try:
                    with open(CROPS_FILE, 'r') as f:
                        crops = json.load(f)
                except: pass
            
            # Generar ID (CULT-XXX)
            max_n = 0
            for cid in crops:
                if cid.startswith("CULT-"):
                    try:
                        n = int(cid.split("-")[1])
                        if n > max_n: max_n = n
                    except: pass
            new_id = f"CULT-{max_n + 1:03d}"
            
            # Guardar nuevo cultivo
            crops[new_id] = { 
                "name": new_name, 
                "humidity": 60.0, 
                "temperature": 25.0, 
                "ph": 6.5, 
                "pest_detected": None,
                "last_update": time.time(), 
                "last_alert": 0 
            }
            
            with open(CROPS_FILE, 'w') as f:
                json.dump(crops, f)
            
            return {"reply": f"✅ *Cultivo Registrado (Web)*\n\n🌿 Nombre: {new_name}\n🆔 ID: `{new_id}`\n\nEl panel de estado se actualizará en breve."}
        except Exception as e:
            return {"reply": f"❌ Error al crear cultivo: {str(e)}"}

    elif msg_clean.startswith("/simular_plaga"):
        # Para probar las alertas desde la web
        try:
            if os.path.exists(CROPS_FILE):
                with open(CROPS_FILE, 'r') as f: crops = json.load(f)
                # Afectar al primer cultivo encontrado
                if crops:
                    cid = list(crops.keys())[0]
                    crops[cid]["pest_detected"] = "Pulgón (Simulado Web)"
                    crops[cid]["humidity"] = 20.0 # Estrés hídrico
                    with open(CROPS_FILE, 'w') as f: json.dump(crops, f)
                    return {"reply": f"⚠️ *Simulación Iniciada en {crops[cid]['name']}*\nPlaga detectada y humedad baja."}
        except: pass

    elif msg_clean.startswith("/borrar_cultivo"):
        try:
            parts = msg_clean.split(" ", 1)
            if len(parts) < 2:
                return {"reply": "⚠️ Uso: /borrar_cultivo [ID] (ej: CULT-001)"}
            
            target_id = parts[1].strip()
            
            if os.path.exists(CROPS_FILE):
                with open(CROPS_FILE, 'r') as f:
                    crops = json.load(f)
                
                if target_id in crops:
                    deleted_name = crops[target_id]["name"]
                    del crops[target_id]
                    with open(CROPS_FILE, 'w') as f:
                        json.dump(crops, f)
                    return {"reply": f"🗑️ *Cultivo Eliminado*\n\nSe ha eliminado: {deleted_name} ({target_id})"}
                else:
                    return {"reply": f"❌ No encontré ningún cultivo con el ID: `{target_id}`"}
            else:
                return {"reply": "❌ No hay base de datos de cultivos."}
        except Exception as e:
            return {"reply": f"❌ Error al borrar: {str(e)}"}
    
    # Aquí conectamos con el cerebro del agente.
    system_persona = (
        "Eres un Asistente Agrónomo de IA experto en agricultura de precisión. "
        "Respondes de forma técnica pero accesible para agricultores."
    )
    
    args = ["--prompt", message, "--system", system_persona]
    if image_path:
        args.extend(["--image", image_path])
        # Forzar el uso de Gemini para visión, ya que Llama 3 (Groq) es solo texto
        args.extend(["--provider", "gemini"])

    response = run_tool("chat_with_llm.py", args)
    print(f"DEBUG LLM: {response}")
    
    if response.get("status") == "error":
        reply = f"❌ Error del sistema: {response.get('message')}"
    elif "error" in response:
        reply = f"⚠️ Error del modelo: {response['error']}"
    else:
        reply = response.get("content", "Lo siento, no pude generar una respuesta.")

    return {"reply": reply}

@app.get("/")
@app.get("/index.html")
async def read_root():
    return FileResponse("index.html")

@app.get("/status/crops")
async def get_crops_status():
    """
    Endpoint para leer el estado actual de los cultivos desde el archivo JSON
    que es actualizado por el listener de Telegram.
    """
    if not os.path.exists(CROPS_FILE):
        return {"status": "error", "message": "El archivo de estado de cultivos no existe. ¿Está corriendo listen_telegram.py?"}
    try:
        with open(CROPS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {"status": "error", "message": f"No se pudo leer o parsear el archivo de cultivos: {str(e)}"}

class CropUpdate(BaseModel):
    crop_id: str
    humidity: float
    temperature: float
    ph: float
    pest_detected: Optional[str] = None

@app.post("/api/update_crop")
async def update_crop_api(data: CropUpdate, x_api_key: Optional[str] = Header(None)):
    """Endpoint para recibir datos de sensores reales desde el PC."""
    # --- Seguridad del Endpoint ---
    server_secret_key = os.getenv("SENSOR_API_KEY")
    # Si la clave está configurada en el servidor, se vuelve obligatoria.
    if server_secret_key and x_api_key != server_secret_key:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="API Key inválida o no proporcionada")

    try:
        crops = {}
        if os.path.exists(CROPS_FILE):
            with open(CROPS_FILE, 'r') as f:
                crops = json.load(f)
        
        # Si el cultivo existe, actualizamos sus valores y lo marcamos como REAL
        if data.crop_id in crops:
            crops[data.crop_id]["humidity"] = data.humidity
            crops[data.crop_id]["temperature"] = data.temperature
            crops[data.crop_id]["ph"] = data.ph
            crops[data.crop_id]["pest_detected"] = data.pest_detected
            crops[data.crop_id]["last_update"] = time.time()
            crops[data.crop_id]["mode"] = "real" # Desactiva la simulación para este cultivo
            
            with open(CROPS_FILE, 'w') as f:
                json.dump(crops, f)
            return {"status": "success", "message": f"Cultivo {data.crop_id} actualizado desde sensores remotos."}
        else:
            return {"status": "error", "message": f"Cultivo {data.crop_id} no encontrado. Créalo primero en el chat."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def sync_cycle():
    """Ciclo de sincronización: Carga inicial + Guardado periódico."""
    # Esperar 5s para que el servidor arranque y pase el health check
    await asyncio.sleep(5)
    
    print("🔄 Ejecutando carga inicial de datos...")
    res = run_tool("sync_db.py", ["--action", "load"])
    print(f"☁️ Carga inicial: {res}")

    while True:
        await asyncio.sleep(60) # Esperar 60 segundos
        res = run_tool("sync_db.py", ["--action", "save"])
        print(f"☁️ Auto-Guardado: {res}")

@app.on_event("startup")
async def startup_event():
    print("🚀 Servidor iniciado. Programando sincronización en segundo plano.")
    
    # Iniciar el cerebro del agente (Telegram + Cultivos) en segundo plano
    print("🌱 Arrancando agente de cultivos (listen_telegram.py)...")
    subprocess.Popen([sys.executable, "execution/listen_telegram.py"])
    
    asyncio.create_task(sync_cycle())