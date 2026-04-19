#!/usr/bin/env python3
import subprocess
import os
import sys

def run_sudo(cmd):
    print(f"Ejecutando con sudo: {cmd}")
    return subprocess.call(f"sudo {cmd}", shell=True)

def create_swap(size_gb=4):
    swap_path = "/swapfile_agro"
    if os.path.exists(swap_path):
        print(f"⚠️ El archivo {swap_path} ya existe.")
        return

    print(f"--- Creando SWAP de {size_gb}GB para permitir compilación ---")
    if run_sudo(f"fallocate -l {size_gb}G {swap_path}") != 0:
        # Fallback si fallocate falla (sistemas de archivos antiguos)
        run_sudo(f"dd if=/dev/zero of={swap_path} bs=1M count={size_gb * 1024}")
    
    run_sudo(f"chmod 600 {swap_path}")
    run_sudo(f"mkswap {swap_path}")
    run_sudo(f"swapon {swap_path}")
    
    print(f"\n✅ SWAP de {size_gb}GB activado temporalmente.")
    print(f"💡 Para hacerlo permanente, añade esta línea a /etc/fstab:")
    print(f"{swap_path} none swap sw 0 0")

if __name__ == "__main__":
    create_swap()