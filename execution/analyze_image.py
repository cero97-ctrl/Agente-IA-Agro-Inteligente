#!/usr/bin/env python3
import argparse
import json
import sys
import os
import subprocess

def main():
    """
    Este script actúa como un puente para el análisis de imágenes.
    Toma una imagen y un prompt, y los pasa al LLM multimodal (Gemini).
    """
    parser = argparse.ArgumentParser(description="Analizar una imagen con un LLM (Gemini).")
    parser.add_argument("--image", required=True, help="Ruta a la imagen a analizar.")
    parser.add_argument("--prompt", required=True, help="Prompt para guiar el análisis.")
    args = parser.parse_args()

    # Ruta al script de chat principal
    chat_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_with_llm.py")

    if not os.path.exists(args.image):
        print(json.dumps({"status": "error", "message": "Archivo de imagen no encontrado."}))
        sys.exit(1)

    # Forzar el uso de Gemini, ya que es el proveedor multimodal configurado
    cmd = [
        sys.executable,
        chat_script,
        "--image", args.image,
        "--prompt", args.prompt,
        "--provider", "gemini"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
        llm_response = json.loads(result.stdout)

        if "content" in llm_response:
            print(json.dumps({"status": "success", "description": llm_response["content"]}))
        else:
            error_msg = llm_response.get("error", "Respuesta del LLM vacía o inválida.")
            print(json.dumps({"status": "error", "message": error_msg}))

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))

if __name__ == "__main__":
    main()