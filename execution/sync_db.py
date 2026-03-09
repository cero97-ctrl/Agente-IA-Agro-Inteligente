#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path

try:
    from huggingface_hub import HfApi, snapshot_download
except ImportError:
    print("❌ Error: Falta 'huggingface_hub'. Instala: pip install huggingface_hub", file=sys.stderr)
    sys.exit(1)

# Configuración: Apunta a .tmp/chroma_db en la raíz del proyecto
DB_LOCAL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp", "chroma_db")

def upload_db(repo_id, token):
    if not os.path.exists(DB_LOCAL_PATH):
        print(f"⚠️ No hay base de datos local en {DB_LOCAL_PATH} para subir.")
        return

    api = HfApi(token=token)
    print(f"☁️  Subiendo memoria a {repo_id}...")
    try:
        api.upload_folder(
            folder_path=DB_LOCAL_PATH,
            repo_id=repo_id,
            repo_type="dataset",
            path_in_repo="chroma_db",
            commit_message="Auto-save: Actualización de memoria del agente"
        )
        print("✅ Subida completada.")
    except Exception as e:
        print(f"❌ Error subiendo: {e}")

def download_db(repo_id, token):
    print(f"☁️  Descargando memoria de {repo_id}...")
    try:
        # Descargar en la carpeta .tmp raíz. snapshot_download recreará la estructura.
        local_dir = os.path.dirname(DB_LOCAL_PATH)
        snapshot_download(
            repo_id=repo_id,
            repo_type="dataset",
            local_dir=local_dir,
            allow_patterns=["chroma_db/*"],
            token=token
        )
        print("✅ Descarga completada.")
    except Exception as e:
        print(f"⚠️  No se pudo descargar (¿Es la primera vez o el dataset está vacío?): {e}")

def main():
    parser = argparse.ArgumentParser(description="Sincronizar ChromaDB con Hugging Face.")
    parser.add_argument("--action", choices=["save", "load"], required=True)
    args = parser.parse_args()

    token = os.getenv("HF_TOKEN")
    repo_id = os.getenv("HF_DATASET_ID") # Ej: "usuario/agro-memory-db"

    if not token or not repo_id:
        print("⚠️  Saltando sync: Faltan HF_TOKEN o HF_DATASET_ID en .env")
        return

    if args.action == "save":
        upload_db(repo_id, token)
    elif args.action == "load":
        download_db(repo_id, token)

if __name__ == "__main__":
    main()