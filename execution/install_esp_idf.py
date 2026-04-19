import argparse
import subprocess
import os
import glob
import sys

def run_cmd(cmd, cwd=None):
    print(f"Ejecutando: {cmd}")
    try:
        subprocess.check_call(cmd, shell=True, cwd=cwd)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando comando: {e}")
        return False

def install_deps():
    print("--- Instalando Dependencias del Sistema ---")
    # Comandos para sistemas basados en Debian/Ubuntu/Mint
    deps_cmd = (
        "sudo apt-get update && sudo apt-get install -y "
        "git wget flex bison gperf python3 python3-pip python3-venv "
        "cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0"
    )
    return run_cmd(deps_cmd)

def clone_idf(path):
    print(f"--- Clonando ESP-IDF v5.1 en {path} ---")
    parent_dir = os.path.dirname(path)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)
    
    clone_cmd = f"git clone --recursive -b v5.1 https://github.com/espressif/esp-idf.git {path}"
    return run_cmd(clone_cmd)

def install_tools(path):
    print("--- Instalando Herramientas para ESP32-S3 ---")
    install_script = os.path.join(path, "install.sh")
    if not os.path.exists(install_script):
        print("Error: No se encontró install.sh en la ruta especificada.")
        return False
    
    # 1. Ejecutar instalación estándar para el chip S3
    if not run_cmd(f"./install.sh esp32s3", cwd=path):
        return False

    # 2. Parche de compatibilidad para distribuciones Linux modernas (Ubuntu 24.04+)
    print("--- Aplicando Parche de Compatibilidad (setuptools < 70) ---")
    # Buscamos el binario de python en la carpeta .espressif (ruta dinámica según versión)
    espressif_path = os.path.expanduser("~/.espressif/python_env")
    py_envs = glob.glob(os.path.join(espressif_path, "idf*_env/bin/python"))

    if py_envs:
        target_python = py_envs[0]
        print(f"Downgrade de setuptools para compatibilidad en: {target_python}")
        run_cmd(f"{target_python} -m pip install --upgrade 'setuptools<70' 'pip<24.1' 'wheel' --force-reinstall")
        
        # 3. Sincronizar usando el archivo de restricciones (constraints) de ESP-IDF
        print("--- Sincronizando dependencias usando Constraints oficiales ---")
        constraints_file = os.path.expanduser("~/.espressif/espidf.constraints.v5.1.txt")
        req_file = os.path.join(path, "tools/requirements/requirements.core.txt")
        
        if os.path.exists(constraints_file):
            # Forzamos la reinstalación respetando las versiones que IDF v5.1 espera
            run_cmd(f"{target_python} -m pip install --force-reinstall -r {req_file} -c {constraints_file}")
        else:
            run_cmd(f"{target_python} -m pip install --force-reinstall -r {req_file}")
            
        # Versiones bloqueadas tras validación exitosa en entorno de producción
        print("--- Aplicando bloqueo de versiones validadas (ruamel.yaml 0.17.21) ---")
        run_cmd(f"{target_python} -m pip install 'setuptools<70' 'ruamel.yaml==0.17.21' 'idf-component-manager<3' 'click<8.2' 'pyparsing<3.1'")

    else:
        print("⚠️ No se encontró el entorno virtual en ~/.espressif para aplicar fix de setuptools.")

    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Instalador de ESP-IDF para el Agente Agro")
    parser.add_argument("--mode", choices=["deps", "clone", "install"], required=True)
    parser.add_argument("--path", help="Ruta de instalación de esp-idf")
    
    args = parser.parse_args()
    
    if args.mode == "deps":
        if install_deps():
            print("\n✅ Dependencias instaladas con éxito.")
        else:
            sys.exit(1)
            
    elif args.mode == "clone":
        if not args.path:
            print("Error: Se requiere --path para clonar.")
            sys.exit(1)
        if clone_idf(args.path):
            print("\n✅ Repositorio clonado.")
        else:
            sys.exit(1)
            
    elif args.mode == "install":
        if not args.path:
            print("Error: Se requiere --path para instalar herramientas.")
            sys.exit(1)
        if install_tools(args.path):
            print("\n✅ Herramientas instaladas.")
            print(f"\nPara usar idf.py, ejecuta siempre en tu terminal:")
            print(f"source {os.path.join(args.path, 'export.sh')}")
        else:
            sys.exit(1)