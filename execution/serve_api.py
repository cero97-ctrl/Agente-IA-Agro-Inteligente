#!/usr/bin/env python3
import os
import sys
import asyncio
import json
from typing import List, Optional
from pydantic import BaseModel

# Añadir la ruta de 'execution' para poder importar los otros scripts
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from fastapi import FastAPI, HTTPException
    import uvicorn
    # Importar la lógica directamente desde los scripts de ejecución
    from chat_with_llm import main as chat_main_logic
    from query_memory import main as query_main_logic
    from save_memory import main as save_main_logic
    # Importar funciones de sincronización para un enfoque más robusto
    from sync_db import upload_db, download_db
except ImportError:
    print("❌ Error: Faltan dependencias. Ejecuta: pip install -r requirements.txt")
    sys.exit(1)

# --- Mock de argparse para que los scripts importados funcionen ---
class MockArgs:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

app = FastAPI(
    title="Agro-Inteligente API",
    description="API para conectar clientes Android con el Agente de IA",
    version="1.0.0"
)

# Modelo de datos para recibir peticiones desde Android
class AgentRequest(BaseModel):
    instruction: str
    provider: Optional[str] = None
    image_url: Optional[str] = None # Para análisis de imágenes desde una URL

class MemoryQuery(BaseModel):
    query: str
    n_results: Optional[int] = 3

class MemorySave(BaseModel):
    text: str
    category: Optional[str] = "general"

@app.get("/")
def read_root():
    return {"status": "online", "system": "Agro-Inteligente v1.0"}

@app.post("/chat")
def chat_interaction(req: AgentRequest, capsys: "pytest.CaptureFixture" = None):
    """
    Endpoint para interactuar con el LLM. Llama a la lógica de chat_with_llm.py.
    """
    try:
        # Simular los argumentos de línea de comandos para el script importado
        args = MockArgs(
            prompt=req.instruction,
            provider=req.provider,
            image=req.image_url,
            memory_query=None,
            memory_only=False,
            system=None
        )
        # Redirigir stdout para capturar la salida JSON del script
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        # Llamar a la función principal del script
        chat_main_logic(args)
        
        sys.stdout = old_stdout # Restaurar stdout
        response_json = captured_output.getvalue()
        return json.loads(response_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/query")
def query_memory_endpoint(req: MemoryQuery):
    """
    Consulta la base de datos vectorial ChromaDB desde Android
    """
    try:
        args = MockArgs(query=req.query, n_results=req.n_results, db_path=".tmp/chroma_db")
        
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        query_main_logic(args)
        sys.stdout = old_stdout
        
        return json.loads(captured_output.getvalue())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/save")
def save_memory_endpoint(req: MemorySave):
    """Guarda un recuerdo en la base de datos vectorial."""
    try:
        args = MockArgs(text=req.text, category=req.category, db_path=".tmp/chroma_db")
        
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        save_main_logic(args)
        sys.stdout = old_stdout
        
        return json.loads(captured_output.getvalue())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def sync_cycle():
    """Tarea en segundo plano para sincronizar la memoria con la nube."""
    token = os.getenv("HF_TOKEN")
    repo_id = os.getenv("HF_DATASET_ID")

    if not token or not repo_id:
        print("⚠️  Sincronización en la nube desactivada: Faltan HF_TOKEN o HF_DATASET_ID en .env")
        return
    
    # 1. Carga inicial al arrancar
    print("🔄 Iniciando carga de memoria desde la nube...")
    download_db(repo_id, token)
    
    # 2. Ciclo de guardado periódico
    while True:
        await asyncio.sleep(300) # Guardar cada 5 minutos
        print("💾 Auto-guardando memoria en la nube...")
        upload_db(repo_id, token)

@app.on_event("startup")
async def startup_event():
    # Iniciar el ciclo de sincronización sin bloquear el servidor
    asyncio.create_task(sync_cycle())

def main():
    # Escuchar en 0.0.0.0 permite acceso desde la red local (WiFi)
    print("🚀 Iniciando servidor API en puerto 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
