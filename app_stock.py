# cd C:/xampp/htdocs/
# pyinstaller --onefile --windowed app_stock.py
# git add .
# git commit -m "Versión 1.2: [describe los cambios, ej: Añadido puerto personalizado]"
# git push
# git add version.txt
# git commit -m "Actualización de versión a 1.2"
# git push
import mysql.connector
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from tkcalendar import Calendar
import pandas as pd
from datetime import datetime
import configparser
import os
import requests
import sys
import subprocess

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

APP_VERSION = "0.0.0.5"

UPDATE_URL_VERSION = "https://raw.githubusercontent.com/reca1338a-wq/stock/main/version.txt"
UPDATE_URL_EXE = "https://github.com/reca1338a-wq/stock/releases/latest/download/app_stock.exe"

CONFIG_FILE = "config.ini"

def check_for_updates():
    try:
        response = requests.get(UPDATE_URL_VERSION, timeout=5)
        latest_version = response.text.strip()
        if latest_version > APP_VERSION:
            if messagebox.askyesno("Actualización disponible", f"Hay una nueva versión ({latest_version}). ¿Descargar y actualizar?"):
                new_exe = "app_stock_new.exe"
                with open(new_exe, "wb") as f:
                    f.write(requests.get(UPDATE_URL_EXE).content)
                os.replace(new_exe, "app_stock.exe")
                subprocess.Popen(["app_stock.exe"])
                sys.exit(0)
    except Exception:
        pass

def load_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        return config['DB']
    return None

def save_config(host, user, password, database, port):
    config = configparser.ConfigParser()
    config['DB'] = {'host': host, 'user': user, 'password': password, 'database': database, 'port': port}
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

db_config = load_config()
if not db_config:
    config_window = ctk.CTk()
    config_window.title("Configurar BD")
    config_window.geometry("400x350")
    config_window.resizable(True, True)

    ctk.CTkLabel(config_window, text="Host (ej: 192.168.1.131):").grid(row=0, column=0, padx=10, pady=5, sticky="w")
    entry_host = ctk.CTkEntry(config_window)
    entry_host.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
    entry_host.insert(0, "192.168.1.131")

    ctk.CTkLabel(config_window, text="Puerto (ej: 48216):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
    entry_port = ctk.CTkEntry(config_window)
    entry_port.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
    entry_port.insert(0, "48216")

    ctk.CTkLabel(config_window, text="Usuario:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
    entry_user = ctk.CTkEntry(config_window)
    entry_user.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
    entry_user.insert(0, "root")

    ctk.CTkLabel(config_window, text="Contraseña:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
    entry_password = ctk.CTkEntry(config_window, show="*")
    entry_password.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

    ctk.CTkLabel(config_window, text="Base de datos:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
    entry_database = ctk.CTkEntry(config_window)
    entry_database.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
    entry_database.insert(0, "stockalmacen")

    def save_and_close():
        save_config(entry_host.get(), entry_user.get(), entry_password.get(), entry_database.get(), entry_port.get())
        config_window.destroy()

    ctk.CTkButton(config_window, text="Guardar Configuración", command=save_and_close).grid(row=5, column=0, columnspan=2, pady=20, sticky="ew")

    config_window.columnconfigure(1, weight=1)
    config_window.mainloop()
    db_config = load_config()

DB_CONFIG = dict(db_config)
if 'port' not in DB_CONFIG:
    DB_CONFIG['port'] = '48216'

def conectar_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"No se pudo conectar: {err}")
        return None

# Variables Tk para bindings
var_tipo = tk.StringVar()
var_fecha = tk.StringVar()
var_entregado_a = tk.StringVar()
var_de = tk.StringVar()
var_impresora = tk.StringVar()
var_cantidad = tk.IntVar(value=0)
var_toner = tk.StringVar()
var_tambor = tk.StringVar()
var_habia = tk.IntVar(value=0)
var_quedan = tk.IntVar(value=0)

# Función para actualizar quedan automáticamente
def update_quedan(*args):
    try:
        quedan = var_habia.get() - var_cantidad.get()
        var_quedan.set(quedan if quedan >= 0 else 0)
    except tk.TclError:
        var_quedan.set(0)

var_habia.trace("w", update_quedan)
var_cantidad.trace("w", update_quedan)

# Función para mostrar/ocultar toner/tambor
def toggle_toner_tambor(*args):
    if var_tipo.get() == "toner":
        label_toner.grid(row=8, column=0, pady=5, sticky="w")
        entry_toner.grid(row=9, column=0, pady=5, sticky="ew")
        label_tambor.grid_remove()
        entry_tambor.grid_remove()
    elif var_tipo.get() == "tambor":
        label_tambor.grid(row=8, column=0, pady=5, sticky="w")
        entry_tambor.grid(row=9, column=0, pady=5, sticky="ew")
        label_toner.grid_remove()
        entry_toner.grid_remove()
    else:
        label_toner.grid_remove()
        entry_toner.grid_remove()
        label_tambor.grid_remove()
        entry_tambor.grid_remove()

var_tipo.trace("w", toggle_toner_tambor)

# Función para calendario
def open_calendar():
    cal_window = ctk.CTkToplevel()
    cal_window.title("Seleccionar Fecha")
    cal = Calendar(cal_window, selectmode="day", date_pattern="yyyy-mm-dd")
    cal.pack(pady=10)

    def select_date():
        var_fecha.set(cal.get_date())
        cal_window.destroy()

    ctk.CTkButton(cal_window, text="Seleccionar", command=select_date).pack(pady=5)

    def set_today():
        today = datetime.now().strftime("%Y-%m-%d")
        var_fecha.set(today)
        cal_window.destroy()

    ctk.CTkButton(cal_window, text="Hoy", command=set_today).pack(pady=5)

def insertar_datos():
    tipo = var_tipo.get().lower()
    if tipo not in ['toner', 'tambor']:
        messagebox.showerror("Error", "Selecciona un tipo válido.")
        return

    fecha = var_fecha.get()
    if not fecha:
        messagebox.showerror("Error", "Selecciona una fecha.")
        return

    entregado_a = var_entregado_a.get()
    de = var_de.get()
    impresora = var_impresora.get()
    cantidad = var_cantidad.get()
    habia = var_habia.get()
    quedan = var_quedan.get()
    toner = var_toner.get() if tipo == 'toner' else ''
    tambor = var_tambor.get() if tipo == 'tambor' else ''

    if cantidad <= 0 or habia < cantidad:
        messagebox.showerror("Error", "Cantidad inválida o insuficiente stock.")
        return

    conn = conectar_db()
    if conn:
        cursor = conn.cursor()
        query = """
        INSERT INTO stock (tipo, fecha, `entregado a`, de, impresora, cantidad, toner, tambor, habia, quedan)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        valores = (tipo, fecha, entregado_a, de, impresora, cantidad, toner, tambor, habia, quedan)
        try:
            cursor.execute(query, valores)
            conn.commit()
            messagebox.showinfo("Éxito", "Datos insertados.")
            limpiar_formulario()
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Fallo al insertar: {err}")
        finally:
            cursor.close()
            conn.close()

# ... (importar_xlsx, mostrar_datos, limpiar_formulario permanecen igual, pero optimizados si es necesario)

check_for_updates()

ventana = ctk.CTk()
ventana.title("Gestor de Stock Almacén")
ventana.geometry("800x700")
ventana.minsize(600, 500)
ventana.resizable(True, True)

ventana.columnconfigure(0, weight=1)
ventana.columnconfigure(1, weight=1)
ventana.rowconfigure(0, weight=1)

frame_form = ctk.CTkFrame(ventana)
frame_form.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
frame_form.columnconfigure(0, weight=1)

row = 0
ctk.CTkLabel(frame_form, text="Tipo:", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
row += 1
combo_tipo = ctk.CTkComboBox(frame_form, values=["Toner", "Tambor"], variable=var_tipo)
combo_tipo.grid(row=row, column=0, pady=5, sticky="ew")
row += 1

ctk.CTkLabel(frame_form, text="Fecha:", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
row += 1
entry_fecha = ctk.CTkEntry(frame_form, textvariable=var_fecha, state="readonly")
entry_fecha.grid(row=row, column=0, pady=5, sticky="ew")
ctk.CTkButton(frame_form, text="Seleccionar Fecha", command=open_calendar, width=150).grid(row=row, column=1, pady=5, padx=5)
row += 1

ctk.CTkLabel(frame_form, text="Entregado a:", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
row += 1
entry_entregado_a = ctk.CTkEntry(frame_form, textvariable=var_entregado_a)
entry_entregado_a.grid(row=row, column=0, pady=5, sticky="ew")
row += 1

ctk.CTkLabel(frame_form, text="De:", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
row += 1
combo_de = ctk.CTkComboBox(frame_form, values=["PM", "AB", "CR", "TO", "CU", "VL", "JA"], variable=var_de)
combo_de.grid(row=row, column=0, pady=5, sticky="ew")
row += 1

ctk.CTkLabel(frame_form, text="Impresora:", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
row += 1
entry_impresora = ctk.CTkEntry(frame_form, textvariable=var_impresora)
entry_impresora.grid(row=row, column=0, pady=5, sticky="ew")
row += 1

ctk.CTkLabel(frame_form, text="Cantidad:", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
row += 1
entry_cantidad = ctk.CTkEntry(frame_form, textvariable=var_cantidad)
entry_cantidad.grid(row=row, column=0, pady=5, sticky="ew")
row += 1

label_toner = ctk.CTkLabel(frame_form, text="Toner:", font=("Arial", 12))
entry_toner = ctk.CTkEntry(frame_form, textvariable=var_toner)

label_tambor = ctk.CTkLabel(frame_form, text="Tambor:", font=("Arial", 12))
entry_tambor = ctk.CTkEntry(frame_form, textvariable=var_tambor)

ctk.CTkLabel(frame_form, text="Había:", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
row += 1
entry_habia = ctk.CTkEntry(frame_form, textvariable=var_habia)
entry_habia.grid(row=row, column=0, pady=5, sticky="ew")
row += 1

ctk.CTkLabel(frame_form, text="Quedan:", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
row += 1
entry_quedan = ctk.CTkEntry(frame_form, textvariable=var_quedan, state="readonly")
entry_quedan.grid(row=row, column=0, pady=5, sticky="ew")
row += 1

ctk.CTkButton(frame_form, text="Insertar Datos", command=insertar_datos, height=40).grid(row=row, column=0, pady=10, sticky="ew")
row += 1
ctk.CTkButton(frame_form, text="Importar desde XLSX", command=importar_xlsx, height=40).grid(row=row, column=0, pady=10, sticky="ew")
row += 1
ctk.CTkButton(frame_form, text="Limpiar Formulario", command=limpiar_formulario, height=40).grid(row=row, column=0, pady=10, sticky="ew")
row += 1

# Frame para datos (derecha)
frame_datos = ctk.CTkFrame(ventana)
frame_datos.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
frame_datos.rowconfigure(1, weight=1)
frame_datos.columnconfigure(0, weight=1)

ctk.CTkLabel(frame_datos, text="Datos en la BD:", font=("Arial", 14, "bold")).grid(row=0, column=0, pady=10, sticky="ew")

scrollable_frame = ctk.CTkScrollableFrame(frame_datos)
scrollable_frame.grid(row=1, column=0, sticky="nsew")
scrollable_frame.columnconfigure(0, weight=1)
scrollable_frame.rowconfigure(0, weight=1)

texto_datos = ctk.CTkTextbox(scrollable_frame, font=("Arial", 12))
texto_datos.grid(row=0, column=0, sticky="nsew")

ctk.CTkButton(frame_datos, text="Mostrar Datos", command=mostrar_datos, height=40).grid(row=2, column=0, pady=10, sticky="ew")

# Etiqueta de versión abajo a la izquierda
version_label = ctk.CTkLabel(ventana, text=f"Versión {APP_VERSION}", font=("Arial", 10), text_color="gray")
version_label.grid(row=1, column=0, padx=10, pady=5, sticky="sw")

# Iniciar app
ventana.mainloop()