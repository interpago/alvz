import os
import sys
import platform

if platform.system() != 'Windows':
    print("Este instalador solo funciona en Windows.")
    sys.exit(1)

import winreg

def add_to_path(new_path):
    """Agrega una ruta al PATH del usuario en el Registro de Windows de forma permanente."""
    try:
        # Abrir la llave del registro del entorno del usuario
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS)
        
        # Obtener el valor actual del PATH
        try:
            current_path, _ = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current_path = ""

        # Verificar si la ruta ya existe para no duplicarla
        if new_path not in current_path:
            updated_path = current_path + ";" + new_path if current_path else new_path
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, updated_path)
            print(f"✅ Éxito: Se ha agregado {new_path} al PATH.")
            print("⚠️ IMPORTANTE: Debes reiniciar tu terminal para que los cambios surtan efecto.")
        else:
            print("ℹ️ La ruta ya estaba en el PATH.")
            
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"❌ Error al modificar el registro: {e}")
        return False

def install():
    print("--- Instalador de Lenguaje Alvz ---")
    
    # Obtener la ruta absoluta de la carpeta actual
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Asegurarnos de que el archivo .bat existe y apunta correctamente
    bat_content = f'@echo off\npython "{os.path.join(current_dir, "alvz.py")}" %*'
    bat_path = os.path.join(current_dir, "alvz.bat")
    
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat_content)
    
    print(f"✅ Archivo de ejecución generado en: {bat_path}")

    # 2. Agregar esta carpeta al PATH del usuario
    if add_to_path(current_dir):
        print("\n--- Instalación Completada ---")
        print("Ahora puedes cerrar esta terminal, abrir una nueva y escribir 'alvz' desde cualquier carpeta.")
    else:
        print("\nHubo un problema al configurar el PATH automáticamente.")

if __name__ == "__main__":
    install()
