import os
import sys
import shutil
import platform

if platform.system() != 'Windows':
    print("Este instalador solo funciona en Windows.")
    sys.exit(1)

import tkinter as tk
from tkinter import messagebox, filedialog
import winreg
import ctypes

class AlvzInstaller:
    def __init__(self, root):
        self.root = root
        self.root.title("Instalador de Alvz Language")
        self.root.geometry("500x350")
        self.root.resizable(False, False)

        # Ruta por defecto: %APPDATA%\Alvz
        self.install_path = os.path.join(os.environ["APPDATA"], "Alvz")

        self.current_step = 0
        self.frames = []

        self.setup_frames()
        self.show_frame(0)

    def setup_frames(self):
        # Frame 1: Bienvenida
        f1 = tk.Frame(self.root, padx=20, pady=20)
        tk.Label(f1, text="Bienvenido al Instalador de Alvz", font=("Arial", 16, "bold")).pack(pady=10)
        tk.Label(f1, text="Este asistente instalará el lenguaje de programación Alvz\nen tu computadora de forma rápida y sencilla.", justify="center").pack(pady=20)
        tk.Button(f1, text="Siguiente >", command=self.next_step, width=15).pack(side="bottom", pady=20)
        self.frames.append(f1)

        # Frame 2: Ruta de instalación
        f2 = tk.Frame(self.root, padx=20, pady=20)
        tk.Label(f2, text="Selecciona la carpeta de instalación", font=("Arial", 12, "bold")).pack(pady=10)

        path_frame = tk.Frame(f2)
        path_frame.pack(fill="x", pady=10)
        self.path_entry = tk.Entry(path_frame)
        self.path_entry.insert(0, self.install_path)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        tk.Button(path_frame, text="Cambiar...", command=self.browse_path).pack(side="right")

        tk.Label(f2, text="Se agregará automáticamente al PATH de Windows para que\npuedas usar el comando 'alvz' en cualquier terminal.", fg="gray").pack(pady=10)

        btn_frame = tk.Frame(f2)
        btn_frame.pack(side="bottom", pady=20)
        tk.Button(btn_frame, text="< Atrás", command=self.prev_step, width=10).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Instalar", command=self.run_install, width=15, bg="#4CAF50", fg="white").pack(side="left", padx=5)
        self.frames.append(f2)

        # Frame 3: Progreso / Finalización
        f3 = tk.Frame(self.root, padx=20, pady=20)
        self.finish_label = tk.Label(f3, text="Instalando...", font=("Arial", 14, "bold"))
        self.finish_label.pack(pady=20)
        self.status_label = tk.Label(f3, text="Copiando archivos...")
        self.status_label.pack(pady=10)

        self.close_btn = tk.Button(f3, text="Finalizar", command=self.root.quit, width=15, state="disabled")
        self.close_btn.pack(side="bottom", pady=20)
        self.frames.append(f3)

    def show_frame(self, index):
        for f in self.frames:
            f.pack_forget()
        self.frames[index].pack(fill="both", expand=True)
        self.current_step = index

    def next_step(self):
        self.show_frame(self.current_step + 1)

    def prev_step(self):
        self.show_frame(self.current_step - 1)

    def browse_path(self):
        path = filedialog.askdirectory(initialdir=self.install_path)
        if path:
            self.install_path = path
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, self.install_path)

    def register_file_association(self, install_dir, icon_path):
        """Registra .alvz en el registro de Windows con icono y asociación al ejecutable."""
        alvz_exe = os.path.join(install_dir, "alvz.exe")
        if not os.path.exists(alvz_exe):
            return
        try:
            # ProgID: Alvz.File
            prog_id = "Alvz.File"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{prog_id}") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, "Archivo fuente Alvz")
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{prog_id}\\DefaultIcon") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f"{icon_path},0" if icon_path else f"{alvz_exe},0")
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{prog_id}\\Shell\\Open\\Command") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f'"{alvz_exe}" "%1"')
            # Asociar extensión .alvz al ProgID
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Software\\Classes\\.alvz") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, prog_id)
            # Notificar al Explorer
            ctypes.windll.user32.SHChangeNotify(0x08000000, 0, None, None)
        except Exception:
            pass

    def add_to_path(self, new_path):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS)
            try:
                current_path, _ = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                current_path = ""

            if new_path not in current_path:
                updated_path = current_path + ";" + new_path if current_path else new_path
                winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, updated_path)
                # Notificar al sistema del cambio en el entorno
                HWND_BROADCAST = 0xFFFF
                WM_SETTINGCHANGE = 0x001A
                ctypes.windll.user32.SendMessageW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment")
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def run_install(self):
        self.next_step()
        self.install_path = self.path_entry.get()

        try:
            # 1. Crear carpeta
            if not os.path.exists(self.install_path):
                os.makedirs(self.install_path)

            # 2. Obtener ruta del ejecutable empaquetado
            # PyInstaller guarda los archivos temporales en sys._MEIPASS
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))

            source_exe = os.path.join(base_path, "alvz.exe")

            # Si estamos en desarrollo y no existe en _MEIPASS, lo buscamos en dist
            if not os.path.exists(source_exe):
                source_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "alvz.exe")

            if not os.path.exists(source_exe):
                raise Exception("No se encontró el archivo alvz.exe para instalar.")

            # 3. Copiar archivo
            target_exe = os.path.join(self.install_path, "alvz.exe")
            shutil.copy2(source_exe, target_exe)

            # 4. Copiar icono
            icon_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alvz.ico")
            if not os.path.exists(icon_src) and hasattr(sys, '_MEIPASS'):
                icon_src = os.path.join(sys._MEIPASS, "alvz.ico")
            icon_target = os.path.join(self.install_path, "alvz.ico")
            if os.path.exists(icon_src):
                shutil.copy2(icon_src, icon_target)
            else:
                icon_target = ""

            # 5. Registrar extensión .alvz en Windows
            self.status_label.config(text="Registrando extensión .alvz...")
            self.root.update()
            try:
                self.register_file_association(self.install_path, icon_target)
            except Exception as e:
                print(f"Error registrando extensión: {e}")

            # 6. Agregar al PATH
            self.status_label.config(text="Configurando variables de entorno...")
            self.root.update()

            if self.add_to_path(self.install_path):
                self.finish_label.config(text="¡Instalación Completada!")
                self.status_label.config(text="Alvz se ha instalado correctamente.\nYa puedes usar el comando 'alvz' en una nueva terminal.\nLos archivos .alvz ahora tienen su propio icono.")
            else:
                self.finish_label.config(text="Instalación con advertencias")
                self.status_label.config(text="Se copiaron los archivos, pero no se pudo actualizar el PATH.\nDeberás agregarlo manualmente.")

            self.close_btn.config(state="normal")

        except Exception as e:
            messagebox.showerror("Error de Instalación", f"Hubo un problema: {str(e)}")
            self.prev_step()

if __name__ == "__main__":
    root = tk.Tk()
    app = AlvzInstaller(root)
    root.mainloop()
