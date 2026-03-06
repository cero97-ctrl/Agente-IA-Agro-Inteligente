#!/usr/bin/env python3
import os
import sys
import argparse
from huggingface_hub import HfApi, hf_hub_download
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_FILE = os.path.join(BASE_DIR, ".tmp", "telegram_crops.json")
REPO_FILENAME = "telegram_crops.json"

def main():
    parser = argparse.ArgumentParser(description="Sincronizar base de datos con Hugging Face Datasets")
    parser.add_argument("--action", choices=["load", "save"], required=True, help="Acción: load (bajar) o save (subir)")
    args = parser.parse_args()

    repo_id = os.getenv("DATASET_REPO_ID")
    token = os.getenv("HF_TOKEN")

    if not repo_id:
        print("⚠️  DATASET_REPO_ID no configurado. Saltando sincronización.")
        return

    if not token:
        print("⚠️  HF_TOKEN no configurado. Saltando sincronización.")
        return

    api = HfApi(token=token)

    if args.action == "save":
        if not os.path.exists(LOCAL_FILE):
            print(f"⚠️  Archivo local no encontrado: {LOCAL_FILE}")
            return
        
        print(f"☁️  Subiendo datos a {repo_id}...")
        try:
            api.upload_file(
                path_or_fileobj=LOCAL_FILE,
                path_in_repo=REPO_FILENAME,
                repo_id=repo_id,
                repo_type="dataset"
            )
            print("✅ Guardado en la nube exitoso.")
        except Exception as e:
            print(f"❌ Error al subir: {e}")

    elif args.action == "load":
        print(f"☁️  Descargando datos de {repo_id}...")
        try:
            hf_hub_download(
                repo_id=repo_id,
                filename=REPO_FILENAME,
                repo_type="dataset",
                local_dir=os.path.dirname(LOCAL_FILE), # Descarga en .tmp/
                token=token
            )
            print("✅ Datos recuperados exitosamente.")
        except Exception as e:
            print(f"⚠️  No se pudo descargar (¿Es la primera vez?): {e}")

if __name__ == "__main__":
    main()