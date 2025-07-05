import threading
import pyautogui
import time
import tkinter as tk
from tkinter import Toplevel, messagebox, PhotoImage
import pymem
import psutil
import win32gui
import sys
import os

# === CONFIGS ===
running = False
pm = None
hp_address = None
max_hp_address = None
hp_percent = 50
mana_percent = 50
hotkey = 'f3'
mana_hotkey = 'f4'

# === OFFSETS ===
BASE_POINTER_OFFSET = 0x019C6628
FIRST_OFFSET = 0xE0
SECOND_OFFSET_HP = 0x28
MAX_HP_OFFSET = 0x2C
SECOND_OFFSET_MP = 0x70
MAX_MP_OFFSET = 0x74

# === WINDOW FUNCTIONS ===
def get_client_window_rect():
    def enum_handler(hwnd, result):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title.startswith("Tibia -"):
                result.append(hwnd)

    result = []
    win32gui.EnumWindows(enum_handler, result)

    if result:
        hwnd = result[0]
        return win32gui.GetWindowRect(hwnd)
    else:
        print("Janela do cliente não encontrada.")
        return None

def stick_bot_to_client(root_window, offset_x=20, offset_y=20):
    rect = get_client_window_rect()
    if rect:
        left, top, _, _ = rect
        x = left + offset_x
        y = top + offset_y
        root_window.geometry(f"+{x}+{y}")

def find_client_exe():
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == 'client.exe':
                return proc.info['pid']
    except:
        return None

def init_memory():
    global pm, hp_address, max_hp_address
    try:
        pid = find_client_exe()
        if not pid:
            print("client.exe não encontrado.")
            return False
        pm = pymem.Pymem(pid)
        base = pm.read_int(pm.base_address + BASE_POINTER_OFFSET)
        level1 = pm.read_int(base + FIRST_OFFSET)
        hp_address = level1 + SECOND_OFFSET_HP
        max_hp_address = level1 + MAX_HP_OFFSET
        return True
    except Exception as e:
        print(f"Erro ao inicializar memória: {e}")
        return False

# === MEMORY READ ===
def get_current_hp():
    try:
        return pm.read_int(hp_address)
    except:
        return None

def get_max_hp():
    try:
        return pm.read_int(max_hp_address)
    except:
        return 100

def get_current_mp():
    try:
        base = pm.read_int(pm.base_address + BASE_POINTER_OFFSET)
        level1 = pm.read_int(base + FIRST_OFFSET)
        return pm.read_int(level1 + SECOND_OFFSET_MP)
    except:
        return None

def get_max_mp():
    try:
        base = pm.read_int(pm.base_address + BASE_POINTER_OFFSET)
        level1 = pm.read_int(base + FIRST_OFFSET)
        return pm.read_int(level1 + MAX_MP_OFFSET)
    except:
        return 100

# === AÇÃO ===
def auto_heal(hotkey):
    pyautogui.press(hotkey)

def bot_loop():
    global running
    while running:
        if not pm:
            print("[INFO] Inicializando memória...")
            if not init_memory():
                print("[ERRO] Falha ao conectar memória. Tentando novamente...")
                time.sleep(1)
                continue
            print("[OK] Memória conectada.")

        current_hp = get_current_hp()
        max_hp = get_max_hp()
        current_mp = get_current_mp()
        max_mp = get_max_mp()

        print(f"[DEBUG] HP: {current_hp}/{max_hp} | MP: {current_mp}/{max_mp}")

        if current_hp is None or current_mp is None or max_hp <= 0 or max_mp <= 0:
            print("[WARN] Valores de HP/MP inválidos. Pulando iteração.")
            time.sleep(1)
            continue

        try:
            if current_hp < max_hp * (hp_percent / 100):
                print(f"[HEAL] HP abaixo de {hp_percent}%. Pressionando {hotkey.upper()}")
                auto_heal(hotkey)
            if current_mp < max_mp * (mana_percent / 100):
                print(f"[HEAL] MP abaixo de {mana_percent}%. Pressionando {mana_hotkey.upper()}")
                auto_heal(mana_hotkey)
        except Exception as e:
            print(f"[ERRO] Falha ao tentar curar: {e}")

        time.sleep(0.1)  # Pequeno delay para não sobrecarregar a CPU

def toggle_bot():
    global running
    running = not running
    status_label.config(text="Ligado" if running else "Desligado")
    heal_btn.config(image=img_on if running else img_off)
    if running:
        threading.Thread(target=bot_loop, daemon=True).start()

# === UI ===
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def open_config():
    def save():
        global hp_percent, hotkey, mana_percent, mana_hotkey
        try:
            hp_percent = float(entry_percent.get())
            hotkey = entry_hotkey.get().strip().lower()
            mana_percent = float(entry_mana_percent.get())
            mana_hotkey = entry_mana_hotkey.get().strip().lower()
            config.destroy()
        except:
            messagebox.showerror("Erro", "Valores inválidos")

    config = Toplevel(root)
    config.title("Configurações")
    config.geometry("250x200")
    config.configure(bg="#222222")
    config.wm_attributes("-topmost", True)
    config.focus_force()

    tk.Label(config, text="Curar HP abaixo de (%):", bg="#222222", fg="white").pack()
    entry_percent = tk.Entry(config)
    entry_percent.insert(0, str(hp_percent))
    entry_percent.pack()

    tk.Label(config, text="Tecla de cura HP:", bg="#222222", fg="white").pack()
    entry_hotkey = tk.Entry(config)
    entry_hotkey.insert(0, hotkey)
    entry_hotkey.pack()

    tk.Label(config, text="Curar MP abaixo de (%):", bg="#222222", fg="white").pack()
    entry_mana_percent = tk.Entry(config)
    entry_mana_percent.insert(0, str(mana_percent))
    entry_mana_percent.pack()

    tk.Label(config, text="Tecla de cura MP:", bg="#222222", fg="white").pack()
    entry_mana_hotkey = tk.Entry(config)
    entry_mana_hotkey.insert(0, mana_hotkey)
    entry_mana_hotkey.pack()

    tk.Button(config, text="Salvar", command=save).pack(pady=10)

# === JANELA PRINCIPAL ===
root = tk.Tk()
root.title("Auto Healer")
root.geometry("150x150")
root.configure(bg="#222222")

img_on = PhotoImage(file=resource_path("cura_ativado.png"))
img_off = PhotoImage(file=resource_path("cura_desativado.png"))

heal_btn = tk.Button(root, image=img_off, bg="black", bd=0, command=toggle_bot, relief="flat")
heal_btn.place(x=10, y=10)

status_label = tk.Label(root, text="Desligado", bg="#222222", fg="white", font=("Arial", 12))
status_label.place(x=10, y=70)

config_btn = tk.Button(root, text="⚙", font=("Arial", 12), bg="black", fg="white", command=open_config, relief="flat", bd=0, activebackground="gray")
config_btn.place(x=90, y=90, width=30, height=30)

stick_bot_to_client(root)
root.mainloop()
