import argparse
import json
import sys
import os
import uuid
import datetime
from pathlib import Path

try:
    import chromadb
    from pypdf import PdfReader
except ImportError:
    print(json.dumps({
        "status": "error",
        "error_message": "Faltan dependencias.",
        "details": "Por favor instala: pip install chromadb pypdf"
    }), file=sys.stderr)
    sys.exit(1)

def print_error(message: str, details: str, exit_code: int):
    error_data = {
        "status": "error",
        "error_message": message,
        "details": details.strip()
    }
    print(json.dumps(error_data, indent=2), file=sys.stderr)
    sys.exit(exit_code)

def main():
    parser = argparse.ArgumentParser(description="Ingestar un PDF desde docs/ a ChromaDB.")
    parser.add_argument("--filename", required=True, help="Nombre del archivo PDF en la carpeta docs/.")
    args = parser.parse_args()

    # Configuración de rutas
    base_dir = Path(__file__).resolve().parent.parent
    docs_dir = base_dir / "docs"
    db_path = base_dir / ".tmp" / "chroma_db"
    
    pdf_path = docs_dir / args.filename

    if not pdf_path.exists():
        print_error("Archivo no encontrado", f"El archivo {args.filename} no existe en {docs_dir}", 2)

    # Extracción de texto
    try:
        reader = PdfReader(str(pdf_path))
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    except Exception as e:
        print_error("Error de lectura PDF", str(e), 3)

    if not full_text.strip():
        print_error("PDF Vacío", "No se pudo extraer texto del PDF (puede ser una imagen escaneada).", 4)

    # Chunking (Ventana deslizante simple)
    chunk_size = 1000
    overlap = 200
    chunks = []
    
    text_len = len(full_text)
    start = 0
    while start < text_len:
        end = start + chunk_size
        chunk = full_text[start:end]
        chunks.append(chunk)
        start += (chunk_size - overlap)

    # Guardado en ChromaDB
    try:
        client = chromadb.PersistentClient(path=str(db_path))
        collection = client.get_or_create_collection(name="agent_memory")
        
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [{
            "source": args.filename,
            "type": "document_pdf",
            "timestamp": datetime.datetime.now().isoformat(),
            "chunk_index": i,
            "total_chunks": len(chunks)
        } for i in range(len(chunks))]
        
        collection.add(documents=chunks, metadatas=metadatas, ids=ids)
        
        print(json.dumps({"status": "success", "file": args.filename, "chunks_ingested": len(chunks)}))
    except Exception as e:
        print_error("Error de Base de Datos", str(e), 5)

if __name__ == "__main__":
    main()