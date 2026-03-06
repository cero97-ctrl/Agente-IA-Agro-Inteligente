import os
import sys
import json
import subprocess
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware 
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

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

# Para hacer la firma de la función más robusta, importamos Optional
from typing import Optional

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
    else:
        reply = response.get("content", f"No pude generar una respuesta. Debug: {response}")

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