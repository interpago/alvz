"""
Register .alvz file association in Windows.
Run with: python register_alvz.py
To uninstall: python register_alvz.py --uninstall
"""
import os
import sys
import platform

if platform.system() != 'Windows':
    print("Este script solo funciona en Windows.")
    sys.exit(1)

import winreg

def register():
    """Register .alvz file association with icon."""
    ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'alvz.ico')
    alvz_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Buscar alvz.exe o alvz.py
    exe_path = os.path.join(alvz_dir, 'dist', 'alvz.exe')
    if not os.path.exists(exe_path):
        exe_path = os.path.join(alvz_dir, 'alvz.bat')
    if not os.path.exists(exe_path):
        exe_path = os.path.join(alvz_dir, 'alvz.py')
    
    if not os.path.exists(ico_path):
        print(f"Error: no se encuentra {ico_path}")
        return False
    
    try:
        # Crear entrada para .alvz → Alvz.File
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                             r'Software\Classes\.alvz') as key:
            winreg.SetValue(key, '', winreg.REG_SZ, 'Alvz.File')
        
        # Crear ProgID Alvz.File
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                             r'Software\Classes\Alvz.File') as key:
            winreg.SetValue(key, '', winreg.REG_SZ, 'Archivo fuente Alvz')
        
        # DefaultIcon
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                             r'Software\Classes\Alvz.File\DefaultIcon') as key:
            winreg.SetValue(key, '', winreg.REG_SZ, f'"{ico_path}",0')
        
        # shell\open\command
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                             r'Software\Classes\Alvz.File\shell\open\command') as key:
            winreg.SetValue(key, '', winreg.REG_SZ, f'"{exe_path}" "%1"')
        
        print(f"[OK] Asociación .alvz registrada")
        print(f"  Icono: {ico_path}")
        print(f"  Abrir con: {exe_path}")
        print(f"  (Reinicia el Explorer o el equipo para ver el cambio)")
        return True
        
    except Exception as e:
        print(f"Error al registrar: {e}")
        return False

def unregister():
    """Remove .alvz file association."""
    try:
        for key_path in [r'Software\Classes\.alvz',
                         r'Software\Classes\Alvz.File']:
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            except FileNotFoundError:
                pass
            # Delete subkeys recursively
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER,
                                key_path + r'\DefaultIcon')
            except FileNotFoundError:
                pass
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER,
                                key_path + r'\shell\open\command')
            except FileNotFoundError:
                pass
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER,
                                key_path + r'\shell\open')
            except FileNotFoundError:
                pass
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER,
                                key_path + r'\shell')
            except FileNotFoundError:
                pass
        print("[OK] Asociación .alvz eliminada")
        return True
    except Exception as e:
        print(f"Error al eliminar: {e}")
        return False

if __name__ == '__main__':
    if '--uninstall' in sys.argv:
        unregister()
    else:
        register()
