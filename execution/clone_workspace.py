#!/usr/bin/env python3
import os
import shutil
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Clonar el proyecto actual a una nueva ubicación.")
    parser.add_argument("--dest", required=True, help="Ruta de destino para la copia.")
    args = parser.parse_args()

    source_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dest_dir = os.path.abspath(args.dest)

    if os.path.exists(dest_dir):
        print(f"❌ Error: El directorio destino ya existe: {dest_dir}")
        print("   Por favor, especifica una ruta nueva o borra el directorio existente.")
        sys.exit(1)

    print(f"📦 Clonando espacio de trabajo...")
    print(f"   Origen:  {source_dir}")
    print(f"   Destino: {dest_dir}")

    # Excluir carpetas de sistema, git y temporales para una copia limpia
    # Se mantiene la estructura y el código fuente.
    ignore_patterns = shutil.ignore_patterns(
        ".git", 
        ".tmp", 
        "__pycache__", 
        "venv", 
        "env", 
        ".venv", 
        ".DS_Store",
        "*.pyc"
    )

    try:
        shutil.copytree(source_dir, dest_dir, ignore=ignore_patterns)
        print(f"✅ Copia completada exitosamente.")
        print(f"   📂 Nuevo proyecto ubicado en: {dest_dir}")
        print("\n   Pasos siguientes sugeridos:")
        print(f"   1. cd {dest_dir}")
        print("   2. bash setup.sh (para configurar el nuevo entorno)")
    except Exception as e:
        print(f"❌ Error al copiar: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()