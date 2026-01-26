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
from PIL import Image, ImageTk
import io

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

APP_VERSION = "0.0.1.1"

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
                os.replace(new_exe, sys.executable)
                subprocess.Popen([sys.executable])
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

# Ventana principal
ventana = ctk.CTk()
ventana.title("Gestor de Stock Almacén")
ventana.geometry("800x700")
ventana.minsize(600, 500)
ventana.resizable(True, True)

ventana.columnconfigure(0, weight=1)
ventana.columnconfigure(1, weight=1)
ventana.rowconfigure(0, weight=1)
ventana.rowconfigure(1, weight=0)

# Set app icon (taskbar)
def set_icon(url):
    try:
        response = requests.get(url, timeout=5)
        img = Image.open(io.BytesIO(response.content))
        ventana.iconphoto(True, ImageTk.PhotoImage(img))
    except:
        pass

set_icon("https://static.vecteezy.com/system/resources/previews/026/724/658/non_2x/printer-icon-silhouette-logo-vector.jpg")

# Cierre completo
def on_close():
    ventana.destroy()
    sys.exit(0)

ventana.protocol("WM_DELETE_WINDOW", on_close)

# Ventana de login (definida siempre, mostrada si no config)
login_window = ctk.CTk()
login_window.title("Login")
login_window.geometry("300x200")

ctk.CTkLabel(login_window, text="Usuario:").pack(pady=5)
entry_login_user = ctk.CTkEntry(login_window)
entry_login_user.pack(pady=5)

ctk.CTkLabel(login_window, text="Contraseña:").pack(pady=5)
entry_login_pass = ctk.CTkEntry(login_window, show="*")
entry_login_pass.pack(pady=5)

user = ""
passw = ""

def login():
    global user, passw
    user = entry_login_user.get()
    passw = entry_login_pass.get()
    if not user or not passw:
        messagebox.showerror("Error", "Usuario y contraseña requeridos.")
        return
    try:
        test_config = {'host': "192.168.1.131", 'port': 48216, 'user': user, 'password': passw, 'database': "stockalmacen"}
        conn = mysql.connector.connect(**test_config)
        if conn.is_connected():
            conn.close()
            if messagebox.askyesno("Guardar Credenciales", "Login correcto. ¿Guardar credenciales?"):
                save_config("192.168.1.131", user, passw, "stockalmacen", "48216")
            else:
                if os.path.exists(CONFIG_FILE):
                    os.remove(CONFIG_FILE)
            login_window.destroy()
            ventana.deiconify()
            check_for_updates()  # Después de login
            show_main_interface()
        else:
            messagebox.showerror("Error", "Credenciales inválidas.")
    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"Login fallido: {err}")

ctk.CTkButton(login_window, text="Login", command=login).pack(pady=10)

# Bind Enter to login
entry_login_pass.bind('<Return>', lambda e: login())

# Función para la interfaz principal
def show_main_interface():
    db_config = load_config() or {'host': "192.168.1.131", 'port': '48216', 'user': user, 'password': passw, 'database': "stockalmacen"}

    def conectar_db():
        try:
            conn = mysql.connector.connect(**db_config)
            return conn
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"No se pudo conectar: {err}")
            return None

    # Variables para interfaz
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
    var_mode = tk.StringVar(value="Salida")

    def update_quedan(*args):
        try:
            if var_mode.get() == "Salida":
                quedan = var_habia.get() - var_cantidad.get()
            else:
                quedan = var_habia.get() + var_cantidad.get()
            var_quedan.set(quedan if quedan >= 0 else 0)
        except tk.TclError:
            var_quedan.set(0)

    var_habia.trace("w", update_quedan)
    var_cantidad.trace("w", update_quedan)
    var_mode.trace("w", update_quedan)

    def toggle_toner_tambor(*args):
        if var_tipo.get() == "Toner":
            label_toner.grid(row=8, column=0, pady=5, sticky="w")
            entry_toner.grid(row=9, column=0, pady=5, sticky="ew")
            label_tambor.grid_remove()
            entry_tambor.grid_remove()
        elif var_tipo.get() == "Tambor":
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

    def open_calendar():
        cal_window = ctk.CTkToplevel(ventana)
        cal_window.title("Seleccionar Fecha")
        cal_window.grab_set()
        cal = Calendar(cal_window, selectmode="day", date_pattern="yyyy-mm-dd")
        cal.pack(pady=10)
        cal.bind("<<CalendarSelected>>", lambda e: set_date(cal.get_date(), cal_window))

        def set_date(date, window):
            var_fecha.set(date)
            window.destroy()

        def set_today():
            today = datetime.now().strftime("%Y-%m-%d")
            var_fecha.set(today)
            cal_window.destroy()

        ctk.CTkButton(cal_window, text="Hoy", command=set_today).pack(pady=5)

    def insertar_datos(event=None):
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

        if cantidad <= 0:
            messagebox.showerror("Error", "Cantidad debe ser positiva.")
            return

        if var_mode.get() == "Salida" and habia < cantidad:
            messagebox.showerror("Error", "Insuficiente stock.")
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
                ver_stock()
            except mysql.connector.Error as err:
                messagebox.showerror("Error", f"Fallo al insertar: {err}")
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
                ver_stock()
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
        var_tipo.set("")
        var_fecha.set("")
        var_entregado_a.set("")
        var_de.set("")
        var_impresora.set("")
        var_cantidad.set(0)
        var_toner.set("")
        var_tambor.set("")
        var_habia.set(0)
        var_quedan.set(0)
        toggle_toner_tambor()

    def ver_stock():
        conn = conectar_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
            (SELECT toner, quedan FROM stock WHERE toner != '' ORDER BY id DESC LIMIT 1)
            UNION
            (SELECT tambor, quedan FROM stock WHERE tambor != '' ORDER BY id DESC LIMIT 1)
            """)
            resultados = cursor.fetchall()
            stock_text = "Stock Actual:\n"
            for fila in resultados:
                stock_text += f"{fila[0]}: {fila[1]} unidades\n"
            stock_label.configure(text=stock_text if resultados else "No hay stock registrado.")
            cursor.close()
            conn.close()

    # Frame para formulario (izquierda)
    frame_form = ctk.CTkScrollableFrame(ventana)
    frame_form.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    frame_form.columnconfigure(0, weight=1)
    frame_form.columnconfigure(1, weight=0)

    row = 0
    frame_form.rowconfigure(row, weight=1)
    ctk.CTkLabel(frame_form, text="Modo:").grid(row=row, column=0, pady=5, sticky="w")
    row += 1
    frame_form.rowconfigure(row, weight=1)
    combo_mode = ctk.CTkComboBox(frame_form, values=["Salida", "Pedido"], variable=var_mode)
    combo_mode.grid(row=row, column=0, pady=5, sticky="ew")
    row += 1

    frame_form.rowconfigure(row, weight=1)
    ctk.CTkLabel(frame_form, text="Tipo:", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
    row += 1
    frame_form.rowconfigure(row, weight=1)
    combo_tipo = ctk.CTkComboBox(frame_form, values=["Toner", "Tambor"], variable=var_tipo)
    combo_tipo.grid(row=row, column=0, pady=5, sticky="ew")
    row += 1

    frame_form.rowconfigure(row, weight=1)
    ctk.CTkLabel(frame_form, text="Fecha:", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
    row += 1
    frame_form.rowconfigure(row, weight=1)
    entry_fecha = ctk.CTkEntry(frame_form, textvariable=var_fecha, state="readonly")
    entry_fecha.grid(row=row, column=0, pady=5, sticky="ew")
    ctk.CTkButton(frame_form, text="Seleccionar Fecha", command=open_calendar, width=150).grid(row=row, column=1, pady=5, padx=5)
    row += 1

    frame_form.rowconfigure(row, weight=1)
    ctk.CTkLabel(frame_form, text="Entregado a:", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
    row += 1
    frame_form.rowconfigure(row, weight=1)
    entry_entregado_a = ctk.CTkEntry(frame_form, textvariable=var_entregado_a)
    entry_entregado_a.grid(row=row, column=0, pady=5, sticky="ew")
    row += 1

    frame_form.rowconfigure(row, weight=1)
    ctk.CTkLabel(frame_form, text="De:", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
    row += 1
    frame_form.rowconfigure(row, weight=1)
    combo_de = ctk.CTkComboBox(frame_form, values=["PM", "AB", "CR", "TO", "CU", "VL", "JA"], variable=var_de)
    combo_de.grid(row=row, column=0, pady=5, sticky="ew")
    row += 1

    frame_form.rowconfigure(row, weight=1)
    ctk.CTkLabel(frame_form, text="Impresora:", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
    row += 1
    frame_form.rowconfigure(row, weight=1)
    entry_impresora = ctk.CTkEntry(frame_form, textvariable=var_impresora)
    entry_impresora.grid(row=row, column=0, pady=5, sticky="ew")
    row += 1

    frame_form.rowconfigure(row, weight=1)
    ctk.CTkLabel(frame_form, text="Cantidad:", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
    row += 1
    frame_form.rowconfigure(row, weight=1)
    entry_cantidad = ctk.CTkEntry(frame_form, textvariable=var_cantidad)
    entry_cantidad.grid(row=row, column=0, pady=5, sticky="ew")
    row += 1

    label_toner = ctk.CTkLabel(frame_form, text="Toner:", font=("Arial", 12))
    entry_toner = ctk.CTkEntry(frame_form, textvariable=var_toner)

    label_tambor = ctk.CTkLabel(frame_form, text="Tambor:", font=("Arial", 12))
    entry_tambor = ctk.CTkEntry(frame_form, textvariable=var_tambor)

    frame_form.rowconfigure(row, weight=1)
    ctk.CTkLabel(frame_form, text="Había/Stock Inicial:", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
    row += 1
    frame_form.rowconfigure(row, weight=1)
    entry_habia = ctk.CTkEntry(frame_form, textvariable=var_habia)
    entry_habia.grid(row=row, column=0, pady=5, sticky="ew")
    row += 1

    frame_form.rowconfigure(row, weight=1)
    ctk.CTkLabel(frame_form, text="Quedan:", font=("Arial", 12)).grid(row=row, column=0, pady=5, sticky="w")
    row += 1
    frame_form.rowconfigure(row, weight=1)
    entry_quedan = ctk.CTkEntry(frame_form, textvariable=var_quedan, state="readonly")
    entry_quedan.grid(row=row, column=0, pady=5, sticky="ew")
    row += 1

    frame_form.rowconfigure(row, weight=1)
    ctk.CTkButton(frame_form, text="Insertar Datos", command=insertar_datos, height=40).grid(row=row, column=0, pady=10, sticky="ew")
    row += 1
    frame_form.rowconfigure(row, weight=1)
    ctk.CTkButton(frame_form, text="Importar desde XLSX", command=importar_xlsx, height=40).grid(row=row, column=0, pady=10, sticky="ew")
    row += 1
    frame_form.rowconfigure(row, weight=1)
    ctk.CTkButton(frame_form, text="Limpiar Formulario", command=limpiar_formulario, height=40).grid(row=row, column=0, pady=10, sticky="ew")
    row += 1

    # Frame para datos (derecha)
    frame_datos = ctk.CTkFrame(ventana)
    frame_datos.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
    frame_datos.rowconfigure(1, weight=1)
    frame_datos.columnconfigure(0, weight=1)

    stock_label = ctk.CTkLabel(frame_datos, text="Stock Actual:", font=("Arial", 12, "bold"))
    stock_label.grid(row=0, column=0, pady=5, sticky="w")
    ver_stock()  # Inicial

    ctk.CTkLabel(frame_datos, text="Datos en la BD:", font=("Arial", 14, "bold")).grid(row=2, column=0, pady=10, sticky="ew")

    scrollable_frame = ctk.CTkScrollableFrame(frame_datos)
    scrollable_frame.grid(row=3, column=0, sticky="nsew")
    scrollable_frame.columnconfigure(0, weight=1)
    scrollable_frame.rowconfigure(0, weight=1)

    texto_datos = ctk.CTkTextbox(scrollable_frame, font=("Arial", 12))
    texto_datos.grid(row=0, column=0, sticky="nsew")

    ctk.CTkButton(frame_datos, text="Mostrar Datos", command=mostrar_datos, height=40).grid(row=4, column=0, pady=10, sticky="ew")

    # Consola SQL
    ctk.CTkLabel(frame_datos, text="Consola SQL: No disponible").grid(row=5, column=0, pady=5, sticky="w")

    sql_text = ctk.CTkTextbox(frame_datos, height=100)
    sql_text.grid(row=6, column=0, pady=5, sticky="ew")

    def send_suggestion():
        sql = sql_text.get("1.0", tk.END).strip()
        if sql:
            conn = conectar_db()
            if conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO suggestions (sql_code, user) VALUES (%s, %s)", (sql, user))
                conn.commit()
                cursor.close()
                conn.close()
                messagebox.showinfo("Sugerencia", "Enviada al administrador.")
                sql_text.delete("1.0", tk.END)

    ctk.CTkButton(frame_datos, text="Enviar Sugerencia", command=send_suggestion).grid(row=7, column=0, pady=5)

    # Etiqueta de versión abajo a la izquierda
    version_label = ctk.CTkLabel(ventana, text=f"Versión {APP_VERSION}", font=("Arial", 10), text_color="gray")
    version_label.grid(row=1, column=0, padx=10, pady=5, sticky="sw")

    def load_image(url, size=(100, 100)):
        try:
            response = requests.get(url, timeout=5)
            img = Image.open(io.BytesIO(response.content))
            img = img.resize(size)
            return ctk.CTkImage(light_image=img, dark_image=img, size=size)
        except:
            return None

    flag_image = load_image("https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Flag_of_Spain.svg/1280px-Flag_of_Spain.svg.png", (50, 30))
    flag_label = ctk.CTkLabel(ventana, image=flag_image, text="")
    flag_label.grid(row=1, column=1, padx=10, pady=5, sticky="se")

    toro_image = load_image("https://upload.wikimedia.org/wikipedia/commons/2/2d/Toro_Osborne_Cabezas_de_San_Juan.JPG", (50, 50))
    toro_label = ctk.CTkLabel(ventana, image=toro_image, text="")
    toro_label.grid(row=1, column=1, padx=60, pady=5, sticky="se")

# Chequeo config.ini
config = load_config()
if config:
    user = config['user']
    passw = config['password']
    ventana.deiconify()
    check_for_updates()
    show_main_interface()
else:
    entry_login_pass.bind('<Return>', lambda e: login())
    login_window.mainloop()

ventana.mainloop()