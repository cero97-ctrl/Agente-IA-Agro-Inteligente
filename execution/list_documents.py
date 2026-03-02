import json
import sys
import os
from pathlib import Path

try:
    import chromadb
except ImportError:
    print(json.dumps({"status": "error", "message": "Falta chromadb"}), file=sys.stderr)
    sys.exit(1)

def main():
    # Configuración de rutas igual que en ingest_pdf.py
    base_dir = Path(__file__).resolve().parent.parent
    db_path = base_dir / ".tmp" / "chroma_db"

    if not db_path.exists():
        print(json.dumps({"status": "success", "documents": []}))
        sys.exit(0)

    try:
        client = chromadb.PersistentClient(path=str(db_path))
        collection = client.get_or_create_collection(name="agent_memory")
        
        # Consultar solo metadatos donde el tipo sea documento PDF
        # Nota: ChromaDB permite filtrar por metadatos en el get()
        results = collection.get(where={"type": "document_pdf"}, include=["metadatas"])
        
        files = {}
        if results['metadatas']:
            for meta in results['metadatas']:
                source = meta.get('source', 'Desconocido')
                timestamp = meta.get('timestamp', '')
                # Guardamos solo la última fecha de ingesta por archivo
                if source not in files:
                    files[source] = timestamp
        
        # Formatear lista
        doc_list = [{"name": k, "ingested_at": v} for k, v in files.items()]
        
        print(json.dumps({"status": "success", "documents": doc_list}))
        
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))

if __name__ == "__main__":
    main()