import mysql.connector
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk  # Para UI moderna
import pandas as pd
from datetime import datetime
import configparser
import os
import requests  # Para chequeo de actualizaciones
import sys
import subprocess

ctk.set_appearance_mode("Dark")  # Tema oscuro (cambia a "Light" si prefieres claro)
ctk.set_default_color_theme("blue")  # Tema azul (opciones: blue, dark-blue, green)

# Versión actual de la app
APP_VERSION = "1.1"  # Actualiza esto cada vez que hagas cambios

# URL para chequeo de actualizaciones (sube un 'version.txt' con el número de versión y 'app_stock.exe' a un servidor o GitHub)
UPDATE_URL_VERSION = "https://tu-servidor-o-github.com/version.txt"  # Cambia esto a tu URL real
UPDATE_URL_EXE = "https://tu-servidor-o-github.com/app_stock.exe"    # URL del nuevo .exe

# Archivo de configuración
CONFIG_FILE = "config.ini"

def check_for_updates():
    try:
        response = requests.get(UPDATE_URL_VERSION, timeout=5)
        latest_version = response.text.strip()
        if latest_version > APP_VERSION:
            if messagebox.askyesno("Actualización disponible", f"Hay una nueva versión ({latest_version}). ¿Descargar y actualizar?"):
                # Descargar nuevo exe
                new_exe = "app_stock_new.exe"
                with open(new_exe, "wb") as f:
                    f.write(requests.get(UPDATE_URL_EXE).content)
                # Reemplazar el actual y reiniciar
                os.replace(new_exe, "app_stock.exe")
                subprocess.Popen(["app_stock.exe"])
                sys.exit(0)
    except Exception as e:
        pass  # Si no hay internet o error, ignora silenciosamente

def load_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        return config['DB']
    else:
        return None

def save_config(host, user, password, database):
    config = configparser.ConfigParser()
    config['DB'] = {'host': host, 'user': user, 'password': password, 'database': database}
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

# Configuración inicial de BD
db_config = load_config()
if not db_config:
    # Ventana para configurar BD si no existe config
    config_window = ctk.CTk()
    config_window.title("Configurar BD")
    config_window.geometry("400x300")
    config_window.resizable(True, True)

    ctk.CTkLabel(config_window, text="Host (ej: localhost o IP remota):").grid(row=0, column=0, padx=10, pady=5, sticky="w")
    entry_host = ctk.CTkEntry(config_window)
    entry_host.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
    entry_host.insert(0, "localhost")

    ctk.CTkLabel(config_window, text="Usuario:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
    entry_user = ctk.CTkEntry(config_window)
    entry_user.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
    entry_user.insert(0, "root")

    ctk.CTkLabel(config_window, text="Contraseña:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
    entry_password = ctk.CTkEntry(config_window, show="*")
    entry_password.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

    ctk.CTkLabel(config_window, text="Base de datos:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
    entry_database = ctk.CTkEntry(config_window)
    entry_database.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
    entry_database.insert(0, "stockalmacen")

    def save_and_close():
        save_config(entry_host.get(), entry_user.get(), entry_password.get(), entry_database.get())
        config_window.destroy()

    ctk.CTkButton(config_window, text="Guardar Configuración", command=save_and_close).grid(row=4, column=0, columnspan=2, pady=20, sticky="ew")

    config_window.columnconfigure(1, weight=1)
    config_window.mainloop()
    db_config = load_config()

DB_CONFIG = dict(db_config)

def conectar_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        messagebox.showerror("Error de Conexión", f"No se pudo conectar: {err}\nRevisa config.ini o reconfíguralo.")
        return None

def insertar_datos():
    tipo = entry_tipo.get().lower()
    if tipo not in ['toner', 'tambor']:
        messagebox.showerror("Error", "El tipo debe ser 'toner' o 'tambor'.")
        return
    
    fecha = entry_fecha.get()
    if not fecha:
        fecha = datetime.now().strftime('%Y-%m-%d')
    
    entregado_a = entry_entregado_a.get()
    de = entry_de.get()
    impresora = entry_impresora.get()
    try:
        cantidad = int(entry_cantidad.get())
        habia = int(entry_habia.get())
        quedan = int(entry_quedan.get())
    except ValueError:
        messagebox.showerror("Error", "Cantidad, había y quedan deben ser números enteros.")
        return
    
    toner = entry_toner.get() if tipo == 'toner' else ''
    tambor = entry_tambor.get() if tipo == 'tambor' else ''
    
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
            messagebox.showinfo("Éxito", "Datos insertados correctamente.")
            limpiar_formulario()
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"No se pudo insertar: {err}")
        finally:
            cursor.close()
            conn.close()

def importar_xlsx():
    archivo = filedialog.askopenfilename(title="Seleccionar XLSX", filetypes=[("Excel files", "*.xlsx")])
    if not archivo:
        return
    
    try:
        df = pd.read_excel(archivo)
        required_cols = ['tipo', 'fecha', 'entregado a', 'de', 'impresora', 'cantidad', 'toner', 'tambor', 'habia', 'quedan']
        if not all(col in df.columns for col in required_cols):
            messagebox.showerror("Error", f"El XLSX debe tener estas columnas: {', '.join(required_cols)}")
            return
        
        conn = conectar_db()
        if conn:
            cursor = conn.cursor()
            query = """
            INSERT INTO stock (tipo, fecha, `entregado a`, de, impresora, cantidad, toner, tambor, habia, quedan)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            for _, row in df.iterrows():
                valores = (
                    row['tipo'], row['fecha'], row['entregado a'], row['de'], row['impresora'],
                    row['cantidad'], row['toner'], row['tambor'], row['habia'], row['quedan']
                )
                cursor.execute(query, valores)
            conn.commit()
            messagebox.showinfo("Éxito", f"{len(df)} registros importados correctamente.")
            cursor.close()
            conn.close()
    except Exception as e:
        messagebox.showerror("Error", f"Error al importar: {e}")

def mostrar_datos():
    conn = conectar_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stock")
        resultados = cursor.fetchall()
        
        texto_datos.delete("1.0", tk.END)
        
        if resultados:
            for fila in resultados:
                texto_datos.insert(tk.END, f"ID: {fila[0]} | Tipo: {fila[1]} | Fecha: {fila[2]} | Entregado a: {fila[3]} | De: {fila[4]} | Impresora: {fila[5]}\n"
                                           f"Cantidad: {fila[6]} | Toner: {fila[7]} | Tambor: {fila[8]} | Había: {fila[9]} | Quedan: {fila[10]}\n\n")
        else:
            texto_datos.insert(tk.END, "No hay datos en la tabla.\n")
        
        cursor.close()
        conn.close()

def limpiar_formulario():
    for entry in [entry_tipo, entry_fecha, entry_entregado_a, entry_de, entry_impresora, entry_cantidad, entry_toner, entry_tambor, entry_habia, entry_quedan]:
        entry.delete(0, tk.END)

# Chequeo de actualizaciones al inicio
check_for_updates()

# Ventana principal
ventana = ctk.CTk()
ventana.title("Gestor de Stock Almacén")
ventana.geometry("800x700")
ventana.minsize(600, 500)  # Tamaño mínimo para evitar que sea demasiado pequeño
ventana.resizable(True, True)  # Permitir redimensionar

# Usar grid para layout responsivo
ventana.columnconfigure(0, weight=1)
ventana.columnconfigure(1, weight=1)
ventana.rowconfigure(0, weight=1)

# Frame para formulario (izquierda)
frame_form = ctk.CTkFrame(ventana)
frame_form.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
frame_form.columnconfigure(0, weight=1)

row = 0
ctk.CTkLabel(frame_form, text="Tipo (toner o tambor):", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
row += 1
entry_tipo = ctk.CTkEntry(frame_form)
entry_tipo.grid(row=row, column=0, pady=5, sticky="ew")
row += 1

ctk.CTkLabel(frame_form, text="Fecha (YYYY-MM-DD, o vacío para hoy):", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
row += 1
entry_fecha = ctk.CTkEntry(frame_form)
entry_fecha.grid(row=row, column=0, pady=5, sticky="ew")
row += 1

ctk.CTkLabel(frame_form, text="Entregado a:", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
row += 1
entry_entregado_a = ctk.CTkEntry(frame_form)
entry_entregado_a.grid(row=row, column=0, pady=5, sticky="ew")
row += 1

ctk.CTkLabel(frame_form, text="De:", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
row += 1
entry_de = ctk.CTkEntry(frame_form)
entry_de.grid(row=row, column=0, pady=5, sticky="ew")
row += 1

ctk.CTkLabel(frame_form, text="Impresora:", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
row += 1
entry_impresora = ctk.CTkEntry(frame_form)
entry_impresora.grid(row=row, column=0, pady=5, sticky="ew")
row += 1

ctk.CTkLabel(frame_form, text="Cantidad:", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
row += 1
entry_cantidad = ctk.CTkEntry(frame_form)
entry_cantidad.grid(row=row, column=0, pady=5, sticky="ew")
row += 1

ctk.CTkLabel(frame_form, text="Toner (solo si toner):", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
row += 1
entry_toner = ctk.CTkEntry(frame_form)
entry_toner.grid(row=row, column=0, pady=5, sticky="ew")
row += 1

ctk.CTkLabel(frame_form, text="Tambor (solo si tambor):", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
row += 1
entry_tambor = ctk.CTkEntry(frame_form)
entry_tambor.grid(row=row, column=0, pady=5, sticky="ew")
row += 1

ctk.CTkLabel(frame_form, text="Había:", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
row += 1
entry_habia = ctk.CTkEntry(frame_form)
entry_habia.grid(row=row, column=0, pady=5, sticky="ew")
row += 1

ctk.CTkLabel(frame_form, text="Quedan:", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
row += 1
entry_quedan = ctk.CTkEntry(frame_form)
entry_quedan.grid(row=row, column=0, pady=5, sticky="ew")
row += 1

# Botones en el formulario
ctk.CTkButton(frame_form, text="Insertar Datos", command=insertar_datos, height=40).grid(row=row, column=0, pady=10, sticky="ew")
row += 1
ctk.CTkButton(frame_form, text="Importar desde XLSX", command=importar_xlsx, height=40).grid(row=row, column=0, pady=10, sticky="ew")
row += 1
ctk.CTkButton(frame_form, text="Limpiar Formulario", command=limpiar_formulario, height=40).grid(row=row, column=0, pady=10, sticky="ew")
row += 1

# Frame para mostrar datos (derecha, con scroll)
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

# Iniciar app
ventana.mainloop()