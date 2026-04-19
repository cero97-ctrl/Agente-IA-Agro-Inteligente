import os
import subprocess
import sys
import platform

def check_cmd(cmd):
    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return output.decode('utf-8').strip()
    except subprocess.CalledProcessError:
        return None

def run_diagnostic():
    print("--- DIAGNÓSTICO DE ENTORNO: AGENTE IA AGRO-INTELIGENTE ---")
    
    # 1. CORE INFO
    print(f"Sistema Operativo: {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"Versión de Python: {sys.version.split()[0]}")
    print(f"Entorno Conda: {os.environ.get('CONDA_DEFAULT_ENV', 'N/A')}")

    # 2. ESP-IDF ESPECÍFICO
    idf_path = os.environ.get('IDF_PATH')
    print(f"Variable IDF_PATH: {idf_path if idf_path else 'NO DEFINIDA'}")

    idf_ver = check_cmd("idf.py --version")
    if idf_ver:
        print(f"Herramienta idf.py: {idf_ver}")
    else:
        print("Herramienta idf.py: NO ENCONTRADA (¿Ejecutaste export.sh?)")

    # 3. COMPILADOR PARA ESP32-S3
    gcc_ver = check_cmd("xtensa-esp32s3-elf-gcc --version")
    if gcc_ver:
        print(f"Compilador S3: {gcc_ver.splitlines()[0]}")
    else:
        print("Compilador S3: NO ENCONTRADO")

    # 3.1 COMPROBACIÓN FÍSICA DE IDF
    if idf_path:
        idf_py_path = os.path.join(idf_path, "tools", "idf.py")
        if os.path.exists(idf_py_path):
            print(f"Archivo idf.py: Localizado en {idf_py_path}")
            if not idf_ver:
                print("   💡 El archivo existe pero NO está en el PATH. export.sh falló.")
        else:
            print(f"Archivo idf.py: NO ENCONTRADO en {idf_py_path}")

    # 4. RECURSOS
    try:
        import psutil
        # Verificar integridad de dependencias de IDF (pkg_resources)
        try:
            import pkg_resources
            print("Integridad Python: OK (pkg_resources disponible)")
        except ImportError:
            print("Integridad Python: ❌ ERROR (pkg_resources no encontrado)")
            
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        print(f"RAM Disponible: {mem.available / (1024**3):.2f} GB")
        print(f"SWAP Total: {swap.total / (1024**3):.2f} GB (Activo: {swap.used / (1024**3):.2f} GB)")
    except ImportError:
        print("RAM: Instala 'psutil' para ver detalles de memoria.")

    # VERDICTO
    print("\n--- CONCLUSIÓN ---")
    if idf_ver and "v5." in idf_ver:
        print("✅ Entorno ESP-IDF v5 compatible detectado.")
    elif idf_ver:
        print(f"⚠️ Versión detectada ({idf_ver}) no es v5.x. Se recomienda actualizar.")
    elif idf_path and os.path.exists(os.path.join(idf_path, "tools", "idf.py")):
        print("⚠️ ESP-IDF instalado físicamente pero con fallos de activación.")
        print("   💡 Ejecuta: /home/cero/.espressif/python_env/idf5.1_py3.10_env/bin/python -m pip install ruamel.yaml==0.17.21 setuptools<70")
    else:
        print("❌ Entorno no configurado o no detectado.")

if __name__ == "__main__":
    run_diagnostic()