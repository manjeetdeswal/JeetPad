import customtkinter as ctk
import tkinter as tk 
import threading
import pygame
from pynput.mouse import Controller as MouseController, Button as MouseButton
from pynput.keyboard import Controller as KeyboardController, Key
import pystray
from PIL import Image
import sys
import os
import time
import platform
import json
from pathlib import Path

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")
if platform.system() == "Linux":
    ctk.set_widget_scaling(1.5)  # Makes buttons, fonts, and sliders 20% larger
    ctk.set_window_scaling(1.5)

# --- RESOURCE PATH HELPER ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- CONFIGURATION FILE ---
if platform.system() == "Windows":
    CONFIG_DIR = Path(os.getenv('APPDATA')) / "JeetPad"
else:
    CONFIG_DIR = Path.home() / ".config" / "JeetPad"

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = CONFIG_DIR / "config.json"

# --- EXPANDED AVAILABLE ACTIONS ---
AVAILABLE_ACTIONS = [
    "None", "Mouse: Left", "Mouse: Right", "Mouse: Middle", "Mouse: Scroll Up", "Mouse: Scroll Down",
    "Key: space", "Key: enter", "Key: backspace", "Key: tab", "Key: escape", "Key: caps_lock",
    "Key: up", "Key: down", "Key: left", "Key: right",
    "Key: insert", "Key: delete", "Key: home", "Key: end", "Key: page_up", "Key: page_down",
    "Key: print_screen", "Key: scroll_lock", "Key: pause", "Key: num_lock",
    "Key: cmd", "Key: shift", "Key: ctrl", "Key: alt"
]
AVAILABLE_ACTIONS.extend([f"Key: f{i}" for i in range(1, 13)])       
AVAILABLE_ACTIONS.extend([f"Key: {chr(i)}" for i in range(97, 123)]) 
AVAILABLE_ACTIONS.extend([f"Key: {i}" for i in range(10)])           
AVAILABLE_ACTIONS.extend([f"Key: {c}" for c in "`-=[]\\;',./*+"])    

# --- SHARED APP STATE & MAPPINGS ---
APP_STATE = {
    "enabled": True, "mouse_speed": 12.0, "scroll_speed": 1.0, "swap_sticks": False,
    "auto_scan": True, "scan_interval": 5.0, "available_controllers": ["Scanning..."], 
    "selected_controller_idx": 0, "rescan_requested": False, "toggle_button": 7,              
    "mappings": {
        0: "Mouse: Left", 1: "Key: enter", 2: "Mouse: Right", 3: "None", 4: "None", 5: "None",            
        6: "Key: f5", 7: "Key: cmd", 8: "Mouse: Middle", 9: "Key: f2",         
        10: "Key: up", 11: "Key: down", 12: "Key: left", 13: "Key: right"      
    }
}

BTN_NAMES = {
    0: "A", 1: "B", 2: "X", 3: "Y", 4: "LB", 5: "RB", 6: "Back", 7: "Start", 
    8: "L3", 9: "R3", 10: "D-Up", 11: "D-Down", 12: "D-Left", 13: "D-Right"
}

def load_config():
    global APP_STATE
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f: saved_data = json.load(f)
            if "mappings" in saved_data: saved_data["mappings"] = {int(k): v for k, v in saved_data["mappings"].items()}
            APP_STATE.update(saved_data)
        except Exception: pass

def save_config():
    try:
        save_data = APP_STATE.copy()
        save_data.pop("available_controllers", None)
        save_data.pop("rescan_requested", None)
        with open(CONFIG_FILE, "w") as f: json.dump(save_data, f, indent=4)
    except Exception: pass

def set_autostart(enable=True):
    app_name = "JeetPad"
    script_path = os.path.abspath(sys.argv[0])
    icon_path = resource_path("icon.png") 
    
    if getattr(sys, 'frozen', False): exec_cmd = f'"{script_path}"' if platform.system() == "Windows" else script_path
    else: exec_cmd = f'"{sys.executable}" "{script_path}"' if platform.system() == "Windows" else f"python3 {script_path}"

    if platform.system() == "Windows":
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            if enable: winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exec_cmd)
            else: winreg.DeleteValue(key, app_name)
            winreg.CloseKey(key)
        except Exception: pass
    elif platform.system() == "Linux":
        autostart_dir = Path.home() / ".config" / "autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)
        desktop_file = autostart_dir / f"{app_name}.desktop"
        if enable:
            with open(desktop_file, "w") as f: 
                f.write(f"[Desktop Entry]\nType=Application\nExec={exec_cmd}\nIcon={icon_path}\nHidden=false\nNoDisplay=false\nX-GNOME-Autostart-enabled=true\nName={app_name}\n")
        else:
            if desktop_file.exists(): desktop_file.unlink()

def execute_action(action_str, mouse, keyboard, is_press=True):
    if not action_str or action_str == "None": return
    try:
        if action_str.startswith("Mouse: "):
            action = action_str.split(": ")[1]
            if action == "Left": btn = MouseButton.left
            elif action == "Right": btn = MouseButton.right
            elif action == "Middle": btn = MouseButton.middle
            elif action == "Scroll Up":
                if is_press: mouse.scroll(0, 1)
                return
            elif action == "Scroll Down":
                if is_press: mouse.scroll(0, -1)
                return
            else: return
            mouse.press(btn) if is_press else mouse.release(btn)
            
        elif action_str.startswith("Key: "):
            key_str = action_str.split(": ")[1]
            if hasattr(Key, key_str):
                key_obj = getattr(Key, key_str)
                keyboard.press(key_obj) if is_press else keyboard.release(key_obj)
            else:
                keyboard.press(key_str) if is_press else keyboard.release(key_str)
    except Exception: pass

# --- CONTROLLER BACKEND THREAD ---
def controller_worker():
    pygame.init()
    joysticks = {}
    
    def perform_scan():
        pygame.joystick.quit()
        pygame.joystick.init()
        joysticks.clear()
        names = []
        count = pygame.joystick.get_count()
        for i in range(count):
            j = pygame.joystick.Joystick(i)
            joysticks[i] = j
            names.append(f"[{i}] {j.get_name()}")
        if not names:
            names = ["No Controller Detected"]
            APP_STATE["selected_controller_idx"] = 0
        APP_STATE["available_controllers"] = names
        if APP_STATE["selected_controller_idx"] >= len(joysticks) and len(joysticks) > 0:
            APP_STATE["selected_controller_idx"] = 0

    perform_scan()
    mouse, keyboard = MouseController(), KeyboardController()
    DEADZONE, HOLD_DURATION = 0.15, 3.0
    
    toggle_held, toggle_press_time, toggle_executed = False, 0, False
    last_scan_time = time.time()
    last_hat_x, last_hat_y = 0, 0
    
    # NEW: Accumulates scroll fractions so Linux can process them
    scroll_accumulator = 0.0 

    def handle_press(btn_id, current_time):
        nonlocal toggle_held, toggle_press_time, toggle_executed
        if btn_id == APP_STATE["toggle_button"]:
            toggle_held, toggle_press_time, toggle_executed = True, current_time, False
        elif APP_STATE["enabled"] and btn_id in APP_STATE["mappings"]:
            execute_action(APP_STATE["mappings"][btn_id], mouse, keyboard, True)

    def handle_release(btn_id):
        nonlocal toggle_held, toggle_executed
        if btn_id == APP_STATE["toggle_button"]:
            toggle_held = False
            if not toggle_executed and APP_STATE["enabled"] and btn_id in APP_STATE["mappings"]:
                execute_action(APP_STATE["mappings"][btn_id], mouse, keyboard, True)
                execute_action(APP_STATE["mappings"][btn_id], mouse, keyboard, False)
        elif APP_STATE["enabled"] and btn_id in APP_STATE["mappings"]:
            execute_action(APP_STATE["mappings"][btn_id], mouse, keyboard, False)

    while True:
        current_time = time.time()
        if APP_STATE["auto_scan"] and (current_time - last_scan_time >= APP_STATE["scan_interval"]):
            perform_scan()
            last_scan_time = current_time

        if APP_STATE["rescan_requested"]:
            perform_scan()
            APP_STATE["rescan_requested"] = False
            last_scan_time = current_time

        pygame.event.pump()
        idx = APP_STATE["selected_controller_idx"]
        active_joystick = joysticks.get(idx)

        if active_joystick:
            active_id = active_joystick.get_instance_id()
            num_axes = active_joystick.get_numaxes()
            
            if toggle_held and not toggle_executed and (current_time - toggle_press_time >= HOLD_DURATION):
                APP_STATE["enabled"] = not APP_STATE["enabled"]
                active_joystick.rumble(1.0, 1.0, 400) 
                toggle_executed = True 
                save_config() 

            if APP_STATE["enabled"]:
                # --- OS SPECIFIC AXIS MAPPING ---
                if platform.system() == "Linux":
                    rx_axis = 3 if num_axes > 3 else 2
                    ry_axis = 4 if num_axes > 4 else 3
                else:
                    rx_axis = 2
                    ry_axis = 3

                # Fallback safety
                if rx_axis >= num_axes: rx_axis = max(0, num_axes - 1)
                if ry_axis >= num_axes: ry_axis = max(0, num_axes - 1)

                if APP_STATE["swap_sticks"]:
                    mouse_x, mouse_y, scroll_y = active_joystick.get_axis(rx_axis), active_joystick.get_axis(ry_axis), active_joystick.get_axis(1)
                else:
                    mouse_x, mouse_y, scroll_y = active_joystick.get_axis(0), active_joystick.get_axis(1), active_joystick.get_axis(ry_axis)

                # Mouse Movement
                if abs(mouse_x) > DEADZONE or abs(mouse_y) > DEADZONE: 
                    mouse.move(mouse_x * APP_STATE["mouse_speed"], mouse_y * APP_STATE["mouse_speed"])
                
                # --- LINUX SAFE SCROLL ACCUMULATOR ---
                if abs(scroll_y) > DEADZONE: 
                    # Multiply stick value by sensitivity and add to accumulator
                    scroll_accumulator += (-scroll_y * APP_STATE["scroll_speed"] * 0.2) 
                    
                    # Only scroll when accumulator reaches a whole integer (1.0 or -1.0)
                    if abs(scroll_accumulator) >= 1.0:
                        steps = int(scroll_accumulator)
                        mouse.scroll(0, steps)
                        scroll_accumulator -= steps # Keep remainder for smooth scrolling
                else:
                    scroll_accumulator = 0.0 # Reset when thumbstick is let go

            for event in pygame.event.get():
                if hasattr(event, "instance_id") and event.instance_id != active_id: continue
                if event.type == pygame.JOYBUTTONDOWN: handle_press(event.button, current_time)
                elif event.type == pygame.JOYBUTTONUP: handle_release(event.button)
                elif event.type == pygame.JOYHATMOTION and event.hat == 0:
                    hx, hy = event.value
                    if hy == 1 and last_hat_y != 1: handle_press(10, current_time)       
                    elif last_hat_y == 1 and hy != 1: handle_release(10)                 
                    if hy == -1 and last_hat_y != -1: handle_press(11, current_time)     
                    elif last_hat_y == -1 and hy != -1: handle_release(11)               
                    if hx == -1 and last_hat_x != -1: handle_press(12, current_time)     
                    elif last_hat_x == -1 and hx != -1: handle_release(12)               
                    if hx == 1 and last_hat_x != 1: handle_press(13, current_time)       
                    elif last_hat_x == 1 and hx != 1: handle_release(13)                 
                    last_hat_x, last_hat_y = hx, hy
        else:
            pygame.event.clear()
        time.sleep(0.01)

class VisualPicker(ctk.CTkToplevel):
    def __init__(self, parent, btn_id, callback):
        super().__init__(parent)
        self.title(f"Map: {BTN_NAMES[btn_id]}")
        self.geometry("1100x420")
         
        self.grab_set() 
        self.callback = callback
        self.btn_id = btn_id
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)
        self.tabs.add("Keyboard")
        self.tabs.add("Mouse")
        self.build_keyboard_tab()
        self.build_mouse_tab()

    def select_action(self, action):
        self.callback(self.btn_id, action)
        self.destroy()

    def build_mouse_tab(self):
        tab = self.tabs.tab("Mouse")
        mouse_body = ctk.CTkFrame(tab, width=280, height=320, corner_radius=60, fg_color="#2b2b2b")
        mouse_body.pack(pady=10)
        mouse_body.pack_propagate(False)
        mouse_body.grid_columnconfigure(0, weight=1)
        mouse_body.grid_columnconfigure(1, weight=0)
        mouse_body.grid_columnconfigure(2, weight=1)
        mouse_body.grid_rowconfigure(0, weight=1)

        ctk.CTkButton(mouse_body, text="L-Click", font=("Arial", 16, "bold"), corner_radius=20, command=lambda: self.select_action("Mouse: Left")).grid(row=0, column=0, rowspan=3, sticky="nsew", padx=(15, 5), pady=15)
        ctk.CTkButton(mouse_body, text="▲\nUp", width=50, height=60, fg_color="#3a6b8c", command=lambda: self.select_action("Mouse: Scroll Up")).grid(row=0, column=1, sticky="s", pady=(20, 5))
        ctk.CTkButton(mouse_body, text="MID", width=50, height=70, corner_radius=25, fg_color="gray", command=lambda: self.select_action("Mouse: Middle")).grid(row=1, column=1, pady=5)
        ctk.CTkButton(mouse_body, text="▼\nDn", width=50, height=60, fg_color="#3a6b8c", command=lambda: self.select_action("Mouse: Scroll Down")).grid(row=2, column=1, sticky="n", pady=(5, 20))
        ctk.CTkButton(mouse_body, text="R-Click", font=("Arial", 16, "bold"), corner_radius=20, command=lambda: self.select_action("Mouse: Right")).grid(row=0, column=2, rowspan=3, sticky="nsew", padx=(5, 15), pady=15)

    def build_keyboard_tab(self):
        tab = self.tabs.tab("Keyboard")
        main_kb = ctk.CTkFrame(tab, fg_color="transparent")
        main_kb.pack(side="left", padx=10, pady=10)
        nav_kb = ctk.CTkFrame(tab, fg_color="transparent")
        nav_kb.pack(side="left", padx=10, pady=10, fill="y")
        numpad_kb = ctk.CTkFrame(tab, fg_color="transparent")
        numpad_kb.pack(side="left", padx=10, pady=10, fill="y")

        main_rows = [
            [("esc", "esc"), ("f1", "f1"), ("f2", "f2"), ("f3", "f3"), ("f4", "f4"), ("f5", "f5"), ("f6", "f6"), ("f7", "f7"), ("f8", "f8"), ("f9", "f9"), ("f10", "f10"), ("f11", "f11"), ("f12", "f12")],
            [("`", "`"), ("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5"), ("6", "6"), ("7", "7"), ("8", "8"), ("9", "9"), ("0", "0"), ("-", "-"), ("=", "="), ("backspace", "backspace", 70)],
            [("tab", "tab", 50), ("q", "q"), ("w", "w"), ("e", "e"), ("r", "r"), ("t", "t"), ("y", "y"), ("u", "u"), ("i", "i"), ("o", "o"), ("p", "p"), ("[", "["), ("]", "]"), ("\\", "\\", 50)],
            [("caps", "caps_lock", 65), ("a", "a"), ("s", "s"), ("d", "d"), ("f", "f"), ("g", "g"), ("h", "h"), ("j", "j"), ("k", "k"), ("l", "l"), (";", ";"), ("'", "'"), ("enter", "enter", 70)],
            [("shift", "shift", 85), ("z", "z"), ("x", "x"), ("c", "c"), ("v", "v"), ("b", "b"), ("n", "n"), ("m", "m"), (",", ","), (".", "."), ("/", "/"), ("shift", "shift", 85)],
            [("ctrl", "ctrl", 50), ("win", "cmd", 40), ("alt", "alt", 40), ("space", "space", 220), ("alt", "alt", 40), ("win", "cmd", 40), ("ctrl", "ctrl", 50)]
        ]
        for row in main_rows:
            r_frame = ctk.CTkFrame(main_kb, fg_color="transparent")
            r_frame.pack(pady=2)
            for key in row:
                w = key[2] if len(key) == 3 else 35
                c = "#24445c" if len(key[0]) > 1 and key[0] not in ["-","=","[","]","\\",";","'",",",".","/","`"] else None 
                ctk.CTkButton(r_frame, text=key[0].upper(), width=w, height=35, fg_color=c, command=lambda a=f"Key: {key[1]}": self.select_action(a)).pack(side="left", padx=2)

        nav_rows = [ [("prt", "print_screen"), ("scr", "scroll_lock"), ("paus", "pause")], [("ins", "insert"), ("home", "home"), ("pgup", "page_up")], [("del", "delete"), ("end", "end"), ("pgdn", "page_down")] ]
        for row in nav_rows:
            r_frame = ctk.CTkFrame(nav_kb, fg_color="transparent")
            r_frame.pack(pady=2)
            for key in row: ctk.CTkButton(r_frame, text=key[0].upper(), width=35, height=35, fg_color="#24445c", command=lambda a=f"Key: {key[1]}": self.select_action(a)).pack(side="left", padx=2)
        
        arrow_frame = ctk.CTkFrame(nav_kb, fg_color="transparent")
        arrow_frame.pack(side="bottom", pady=2)
        ctk.CTkButton(arrow_frame, text="▲", width=35, height=35, command=lambda: self.select_action("Key: up")).grid(row=0, column=1, padx=2, pady=2)
        ctk.CTkButton(arrow_frame, text="◄", width=35, height=35, command=lambda: self.select_action("Key: left")).grid(row=1, column=0, padx=2, pady=2)
        ctk.CTkButton(arrow_frame, text="▼", width=35, height=35, command=lambda: self.select_action("Key: down")).grid(row=1, column=1, padx=2, pady=2)
        ctk.CTkButton(arrow_frame, text="►", width=35, height=35, command=lambda: self.select_action("Key: right")).grid(row=1, column=2, padx=2, pady=2)

        num_rows = [ [("num", "num_lock"), ("/", "/"), ("*", "*"), ("-", "-")], [("7", "7"), ("8", "8"), ("9", "9"), ("+", "+")], [("4", "4"), ("5", "5"), ("6", "6"), ("ent", "enter")], [("1", "1"), ("2", "2"), ("3", "3"), (".", ".")], [("0", "0", 74)] ]
        for r_idx, row in enumerate(num_rows):
            r_frame = ctk.CTkFrame(numpad_kb, fg_color="transparent")
            r_frame.pack(pady=2, anchor="w")
            for key in row:
                w = key[2] if len(key) == 3 else 35
                c = "#24445c" if len(key[0]) > 1 else None
                ctk.CTkButton(r_frame, text=key[0].upper(), width=w, height=35, fg_color=c, command=lambda a=f"Key: {key[1]}": self.select_action(a)).pack(side="left", padx=2)

class ModernControllerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("JeetPad")
        self.geometry("450x700") 
        self.protocol("WM_DELETE_WINDOW", self.force_quit)

        try:
            if platform.system() == "Windows": self.iconbitmap(resource_path("icon.ico"))
            else:
                icon_img = tk.PhotoImage(file=resource_path("icon.png"))
                self.wm_iconphoto(True, icon_img)
        except Exception: pass

        load_config()

        self.status_frame = ctk.CTkFrame(self, fg_color="#1e1e1e", corner_radius=10)
        self.status_frame.pack(pady=(15, 5), padx=20, fill="x")
        
        top_status = ctk.CTkFrame(self.status_frame, fg_color="transparent")
        top_status.pack(fill="x", pady=(10, 5), padx=10)
        ctk.CTkLabel(top_status, text="Active Controller:").pack(side="left")
        
        self.opt_controller = ctk.CTkOptionMenu(top_status, values=["Detecting..."], command=self.change_priority)
        self.opt_controller.pack(side="left", padx=10, fill="x", expand=True)
        self.btn_refresh = ctk.CTkButton(top_status, text="Force Scan", width=70, command=self.request_rescan)
        self.btn_refresh.pack(side="right")

        bot_status = ctk.CTkFrame(self.status_frame, fg_color="transparent")
        bot_status.pack(fill="x", pady=(0, 10), padx=10)
        self.chk_autoscan = ctk.CTkSwitch(bot_status, text="Auto-Scan", command=self.toggle_autoscan)
        if APP_STATE["auto_scan"]: self.chk_autoscan.select()
        else: self.chk_autoscan.deselect()
        self.chk_autoscan.pack(side="left")
        ctk.CTkLabel(bot_status, text="Interval (sec):").pack(side="left", padx=(20, 5))
        self.ent_interval = ctk.CTkEntry(bot_status, width=50)
        self.ent_interval.insert(0, str(int(APP_STATE["scan_interval"])))
        self.ent_interval.bind("<KeyRelease>", self.update_interval)
        self.ent_interval.pack(side="left")

        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(10, 5), fill="x", padx=20)
        self.lbl_title = ctk.CTkLabel(self.header_frame, text="Controller Active", font=("Arial", 20, "bold"))
        self.lbl_title.pack(side="left")
        self.switch_master = ctk.CTkSwitch(self.header_frame, text="", command=self.toggle_master)
        if APP_STATE["enabled"]: self.switch_master.select()
        else: self.switch_master.deselect()
        self.switch_master.pack(side="right")
        
        self.lbl_hold_hint = ctk.CTkLabel(self, text=f"(Hold {BTN_NAMES[APP_STATE['toggle_button']].upper()} for 3 sec to toggle)", text_color="gray")
        self.lbl_hold_hint.pack()

        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(self.settings_frame, text="Mouse Sensitivity").pack(pady=(10, 0))
        self.mouse_slider = ctk.CTkSlider(self.settings_frame, from_=1, to=40, command=self.update_mouse)
        self.mouse_slider.set(APP_STATE["mouse_speed"])
        self.mouse_slider.pack(pady=(5, 10), padx=20)

        ctk.CTkLabel(self.settings_frame, text="Scroll Sensitivity").pack(pady=(0, 0))
        self.scroll_slider = ctk.CTkSlider(self.settings_frame, from_=0.1, to=5.0, command=self.update_scroll)
        self.scroll_slider.set(APP_STATE["scroll_speed"])
        self.scroll_slider.pack(pady=(5, 10), padx=20)

        toggle_btn_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        toggle_btn_frame.pack(pady=(5, 10), padx=20, fill="x")
        ctk.CTkLabel(toggle_btn_frame, text="Hold to Toggle App:").pack(side="left")
        self.opt_toggle_btn = ctk.CTkOptionMenu(toggle_btn_frame, values=list(BTN_NAMES.values()), command=self.change_toggle_btn, width=90)
        self.opt_toggle_btn.set(BTN_NAMES[APP_STATE["toggle_button"]])
        self.opt_toggle_btn.pack(side="right")

        self.chk_swap = ctk.CTkSwitch(self, text="Swap Left & Right Sticks", command=self.toggle_swap)
        if APP_STATE["swap_sticks"]: self.chk_swap.select()
        self.chk_swap.pack(pady=5, padx=40, anchor="w")

        self.chk_startup = ctk.CTkSwitch(self, text="Start with OS", command=self.toggle_autostart)
        
        if platform.system() == "Windows":
            import winreg
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
                winreg.QueryValueEx(key, "JeetPad")
                self.chk_startup.select()
                winreg.CloseKey(key)
            except WindowsError: pass

        self.chk_startup.pack(pady=5, padx=40, anchor="w")

        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.pack(pady=20, fill="x", padx=40)

        self.btn_remap = ctk.CTkButton(self.action_frame, text="Open Remap Menu", command=self.open_remap_menu, height=40)
        self.btn_remap.pack(side="left", expand=True, padx=(0, 5))

        self.btn_minimize = ctk.CTkButton(self.action_frame, text="Minimize to Tray", command=self.hide_window, height=40, fg_color="#4a4a4a")
        self.btn_minimize.pack(side="right", expand=True, padx=(5, 0))
        
        self.update_ui_loop()

    def request_rescan(self): APP_STATE["rescan_requested"] = True
    def toggle_autoscan(self): APP_STATE["auto_scan"] = bool(self.chk_autoscan.get()); save_config()

    def update_interval(self, event):
        try:
            val = float(self.ent_interval.get())
            if val > 0: 
                APP_STATE["scan_interval"] = val
                save_config()
        except ValueError: pass 

    def change_priority(self, choice):
        if choice == "No Controller Detected": return
        try: 
            APP_STATE["selected_controller_idx"] = int(choice.split("]")[0].replace("[", ""))
            save_config()
        except ValueError: pass

    def change_toggle_btn(self, choice):
        for btn_id, name in BTN_NAMES.items():
            if name == choice:
                APP_STATE["toggle_button"] = btn_id
                self.lbl_hold_hint.configure(text=f"(Hold {name.upper()} for 3 sec to toggle)")
                save_config()
                break

    def toggle_master(self):
        APP_STATE["enabled"] = bool(self.switch_master.get())
        self.lbl_title.configure(text="Controller Active" if APP_STATE["enabled"] else "Controller Paused")
        save_config()

    def toggle_swap(self): APP_STATE["swap_sticks"] = bool(self.chk_swap.get()); save_config()
    def toggle_autostart(self): set_autostart(bool(self.chk_startup.get()))
    def update_mouse(self, val): APP_STATE["mouse_speed"] = float(val); save_config()
    def update_scroll(self, val): APP_STATE["scroll_speed"] = float(val); save_config()

    def update_ui_loop(self):
        current_list = APP_STATE["available_controllers"]
        if self.opt_controller.cget("values") != current_list:
            self.opt_controller.configure(values=current_list)
            idx = APP_STATE["selected_controller_idx"]
            if idx < len(current_list): self.opt_controller.set(current_list[idx])
            else: self.opt_controller.set(current_list[0])

        if APP_STATE["enabled"] and not self.switch_master.get():
            self.switch_master.select()
            self.lbl_title.configure(text="Controller Active")
        elif not APP_STATE["enabled"] and self.switch_master.get():
            self.switch_master.deselect()
            self.lbl_title.configure(text="Controller Paused")
            
        self.after(500, self.update_ui_loop)

    def open_remap_menu(self):
        self.remap_win = ctk.CTkToplevel(self)
        self.remap_win.title("Active Mappings")
        self.remap_win.geometry("350x500")
        self.remap_win.wait_visibility()
        self.remap_win.grab_set()

        scroll_frame = ctk.CTkScrollableFrame(self.remap_win, width=300, height=450)
        scroll_frame.pack(pady=10, padx=10, fill="both", expand=True)
        self.mapping_labels = {}

        for btn_id, btn_name in BTN_NAMES.items():
            row_frame = ctk.CTkFrame(scroll_frame)
            row_frame.pack(fill="x", pady=5, padx=5)
            ctk.CTkLabel(row_frame, text=f"{btn_name}:", width=65, font=("Arial", 14, "bold")).pack(side="left", padx=(10, 0), pady=10)
            
            lbl_map = ctk.CTkLabel(row_frame, text=APP_STATE["mappings"].get(btn_id, "None"), text_color="gray")
            lbl_map.pack(side="left", padx=5)
            self.mapping_labels[btn_id] = lbl_map
            
            ctk.CTkButton(row_frame, text="Change", width=60, command=lambda b_id=btn_id: VisualPicker(self.remap_win, b_id, self.update_mapping)).pack(side="right", padx=10)

    def update_mapping(self, btn_id, new_action):
        APP_STATE["mappings"][btn_id] = new_action
        if btn_id in self.mapping_labels: self.mapping_labels[btn_id].configure(text=new_action)
        save_config() 

    def hide_window(self):
        self.withdraw()
        try:
            image = Image.open(resource_path("icon.png"))
        except Exception:
            image = Image.new('RGB', (64, 64), color=(41, 128, 185))
            
        menu = pystray.Menu(
            # default=True enables Left Double-Click on Windows and Left-Click on Linux
            pystray.MenuItem('Show Settings', self.show_window, default=True), 
            pystray.MenuItem('Quit', self.quit_app)
        )
        self.icon = pystray.Icon("JeetPad", image, "JeetPad", menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def show_window(self, icon, item):
        icon.stop()
        # .after(0) safely tells the main UI thread to restore the window, preventing Linux freezes
        self.after(0, self.deiconify)

    def quit_app(self, icon, item):
        icon.stop()
        # Safely shut down the UI thread before killing the python script
        self.after(0, self.destroy)
        self.after(100, sys.exit)
    def force_quit(self):
        self.destroy()
        os._exit(0)

if __name__ == "__main__":
    threading.Thread(target=controller_worker, daemon=True).start()
    app = ModernControllerApp()
    app.mainloop()
