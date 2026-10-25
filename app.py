import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import threading
import pygame
from pynput.mouse import Controller as MouseController, Button as MouseButton
from pynput.keyboard import Controller as KeyboardController, Key
import pystray
from PIL import Image, ImageDraw
import sys
import os
import re
import time
import math
import platform
import json
import webbrowser
import urllib.request
import urllib.error
from pathlib import Path
import subprocess
import ctypes
from ctypes import wintypes

try:
    import winsound
except ImportError:
    winsound = None

# --- APP VERSION & UPDATE REPOSITORY ---
APP_VERSION = "1.2"
DEFAULT_GITHUB_REPO = "manjeetdeswal/JeetPad"  # Auto-detected from .git/config if available

# --- THEME & SCALING ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
if platform.system() == "Linux":
    ctk.set_widget_scaling(1.25)
    ctk.set_window_scaling(1.25)

# --- MULTI-THEME COLOR PALETTES ---
THEME_PRESETS = {
    "Ocean Blue": {
        "bg_dark": "#0f111a",
        "card_bg": "#181b26",
        "card_border": "#262b3d",
        "row_idle": "#121520",
        "row_active": "#1e3a5f",
        "accent": "#3b82f6",
        "accent_hover": "#2563eb",
        "key_special": "#252f42",
        "key_std": "#1f2433"
    },
    "Cyber Purple": {
        "bg_dark": "#0d0b14",
        "card_bg": "#161224",
        "card_border": "#2d2346",
        "row_idle": "#120e1c",
        "row_active": "#352060",
        "accent": "#8b5cf6",
        "accent_hover": "#7c3aed",
        "key_special": "#271e40",
        "key_std": "#1c162e"
    },
    "Emerald Matrix": {
        "bg_dark": "#091310",
        "card_bg": "#11201b",
        "card_border": "#1e3a31",
        "row_idle": "#0d1814",
        "row_active": "#134e3a",
        "accent": "#10b981",
        "accent_hover": "#059669",
        "key_special": "#19332a",
        "key_std": "#132620"
    },
    "Crimson Red": {
        "bg_dark": "#140b0d",
        "card_bg": "#211215",
        "card_border": "#3d2026",
        "row_idle": "#1a0e10",
        "row_active": "#541b24",
        "accent": "#ef4444",
        "accent_hover": "#dc2626",
        "key_special": "#381a20",
        "key_std": "#291418"
    },
    "Amber Gold": {
        "bg_dark": "#13100a",
        "card_bg": "#1f1a11",
        "card_border": "#3b301e",
        "row_idle": "#17130c",
        "row_active": "#4f3914",
        "accent": "#f59e0b",
        "accent_hover": "#d97706",
        "key_special": "#362b19",
        "key_std": "#261f13"
    },
    "Rose Neon": {
        "bg_dark": "#130b12",
        "card_bg": "#21121e",
        "card_border": "#3d2037",
        "row_idle": "#180d16",
        "row_active": "#521946",
        "accent": "#ec4899",
        "accent_hover": "#db2777",
        "key_special": "#361930",
        "key_std": "#261322"
    }
}

COLORS = {
    "bg_dark": "#0f111a",
    "card_bg": "#181b26",
    "card_border": "#262b3d",
    "row_idle": "#121520",
    "row_active": "#1e3a5f",
    "accent": "#3b82f6",
    "accent_hover": "#2563eb",
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "purple": "#8b5cf6",
    "cyan": "#06b6d4",
    "text_main": "#f3f4f6",
    "text_muted": "#9ca3af",
    "key_special": "#252f42",
    "key_std": "#1f2433"
}

def apply_theme_palette(theme_name):
    palette = THEME_PRESETS.get(theme_name, THEME_PRESETS["Ocean Blue"])
    COLORS.update(palette)

def hex_to_rgb_tuple(hex_str):
    h = hex_str.lstrip("#")
    if len(h) == 6:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)
    return (59, 130, 246, 255)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def detect_github_repo():
    """Attempts to auto-detect owner/repo from local .git/config, falling back to DEFAULT_GITHUB_REPO."""
    try:
        git_cfg = Path(os.path.abspath(".")) / ".git" / "config"
        if git_cfg.exists():
            text = git_cfg.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"github\.com[:/]([^/\s]+/[^/\s\.]+?)(?:\.git)?\s*$", text, re.MULTILINE)
            if m:
                return m.group(1).strip()
    except Exception:
        pass
    return DEFAULT_GITHUB_REPO

if platform.system() == "Windows":
    CONFIG_DIR = Path(os.getenv('APPDATA', Path.home())) / "JeetPad"
else:
    CONFIG_DIR = Path.home() / ".config" / "JeetPad"

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = CONFIG_DIR / "config.json"

BTN_NAMES = {
    0: "A (Cross)", 1: "B (Circle)", 2: "X (Square)", 3: "Y (Triangle)",
    4: "LB (L1)", 5: "RB (R1)", 6: "Back / Select", 7: "Start / Menu",
    8: "L3 (Left Stick)", 9: "R3 (Right Stick)",
    10: "Btn 10 (Guide)", 11: "Btn 11 (Share)", 12: "Btn 12",
    100: "D-Pad Up", 101: "D-Pad Down", 102: "D-Pad Left", 103: "D-Pad Right",
    104: "R-Stick Left", 105: "R-Stick Right",
    106: "LT (L2 Trigger)", 107: "RT (R2 Trigger)"
}

BTN_CATEGORIES = {
    "Face Buttons": [0, 1, 2, 3],
    "Shoulders & Triggers": [4, 5, 106, 107],
    "D-Pad": [100, 101, 102, 103],
    "Sticks & Clicks": [8, 9, 104, 105],
    "System & Extra": [6, 7, 10, 11, 12]
}

MODIFIER_BTN_MAP = {"LB": 4, "RB": 5, "LT": 106, "RT": 107}

# --- DEFAULT PROFILES ---
BASE_DESKTOP_MAP = {
    0: "Mouse: Left", 1: "Key: enter", 2: "Mouse: Right", 3: "OSK: TabTip",
    4: "Combo: alt+tab", 5: "Key: backspace", 6: "Key: f5", 7: "Key: cmd",
    8: "Mouse: Middle", 9: "Key: f2", 10: "None", 11: "None", 12: "None",
    100: "Key: up", 101: "Key: down", 102: "Key: left", 103: "Key: right",
    104: "Mouse: Scroll Left", 105: "Mouse: Scroll Right", 106: "None", 107: "None"
}

MEDIA_MAP = {
    0: "Media: Play/Pause", 1: "Key: esc", 2: "Media: Mute", 3: "Key: f",
    4: "Media: Prev Track", 5: "Media: Next Track", 6: "Combo: alt+tab", 7: "Key: space",
    8: "Mouse: Left", 9: "Mouse: Right", 10: "None", 11: "None", 12: "None",
    100: "Media: Vol Up", 101: "Media: Vol Down", 102: "Key: left", 103: "Key: right",
    104: "None", 105: "None", 106: "None", 107: "None"
}

BROWSER_MAP = {
    0: "Mouse: Left", 1: "Combo: alt+left", 2: "Mouse: Right", 3: "Combo: ctrl+t",
    4: "Combo: ctrl+shift+tab", 5: "Combo: ctrl+tab", 6: "Key: f5", 7: "Combo: ctrl+w",
    8: "Mouse: Middle", 9: "Combo: ctrl+shift+t", 10: "None", 11: "None", 12: "None",
    100: "Mouse: Scroll Up", 101: "Mouse: Scroll Down", 102: "Key: left", 103: "Key: right",
    104: "Mouse: Scroll Left", 105: "Mouse: Scroll Right", 106: "None", 107: "None"
}

DEFAULT_RADIAL_SLOTS = [
    {"label": "Play/Pause", "action": "Media: Play/Pause"},
    {"label": "Mute Audio", "action": "Media: Mute"},
    {"label": "Screenshot", "action": "System: Screenshot"},
    {"label": "Win Touch KB", "action": "OSK: TabTip"},
    {"label": "Show Desktop", "action": "Combo: cmd+d"},
    {"label": "Task View", "action": "Combo: cmd+tab"},
    {"label": "Center Mouse", "action": "System: Center Cursor"},
    {"label": "Next Monitor", "action": "System: Next Monitor"}
]

DAISYWHEEL_PETALS = [
    ("N — Up",    {"X": "a", "Y": "b", "B": "c", "A": "d"}),
    ("NE — Up-R", {"X": "e", "Y": "f", "B": "g", "A": "h"}),
    ("E — Right", {"X": "i", "Y": "j", "B": "k", "A": "l"}),
    ("SE — Dn-R", {"X": "m", "Y": "n", "B": "o", "A": "p"}),
    ("S — Down",  {"X": "q", "Y": "r", "B": "s", "A": "t"}),
    ("SW — Dn-L", {"X": "u", "Y": "v", "B": "w", "A": "x"}),
    ("W — Left",  {"X": "y", "Y": "z", "B": "0", "A": "1"}),
    ("NW — Up-L", {"X": ".", "Y": ",", "B": "?", "A": "-"})
]

def make_profile(std_map, app_rules=""):
    return {
        "mappings": std_map.copy(),
        "combo_mappings": {k: "None" for k in BTN_NAMES},
        "btn_modes": {k: "Normal" for k in BTN_NAMES},
        "app_rules": app_rules
    }

DEFAULT_PROFILES = {
    "Desktop": make_profile(BASE_DESKTOP_MAP, ""),
    "Media": make_profile(MEDIA_MAP, "vlc, mpv, potplayer, spotify, kodi"),
    "Browser": make_profile(BROWSER_MAP, "chrome, msedge, firefox, brave, opera"),
    "Custom 1": make_profile(BASE_DESKTOP_MAP, "photoshop, blender, code, devenv")
}

# --- APPLICATION STATE ---
APP_STATE = {
    "enabled": True,
    "auto_paused_by_game": False,
    "color_theme": "Ocean Blue",      # Persisted across app restarts
    "mouse_speed": 14.0,
    "scroll_speed": 1.5,
    "deadzone": 0.14,
    "swap_sticks": False,
    "trigger_Precision": True,
    "turbo_rate": 12.0,
    "hud_enabled": False,
    "auto_switch_profiles": True,
    "auto_pause_fullscreen": True,
    "check_updates_on_startup": True,
    "github_repo": detect_github_repo(),
    # --- 6 OPTIONAL EXTENSIONS (ALL DISABLED BY DEFAULT) ---
    "radial_wheel_enabled": False,
    "daisywheel_enabled": False,
    "edge_wrap_enabled": False,
    "idle_sleep_enabled": False,
    "idle_timeout_min": 15.0,
    "audio_beeps_enabled": False,
    "laser_ring_enabled": False,
    "radial_slots": json.loads(json.dumps(DEFAULT_RADIAL_SLOTS)),
    # --- SCANNING & PROFILES ---
    "auto_scan": True,
    "scan_interval": 5.0,
    "available_controllers": ["Scanning..."],
    "selected_controller_idx": 0,
    "rescan_requested": False,
    "toggle_button": 7,
    "combo_modifier": "LB",
    "active_profile": "Desktop",
    "profiles": json.loads(json.dumps(DEFAULT_PROFILES)),
    # --- RUNTIME-ONLY TELEMETRY ---
    "mod_currently_held": False,
    "hud_visible": False,
    "radial_active": False,
    "radial_selected_idx": -1,
    "daisywheel_active": False,
    "daisywheel_petal_idx": -1,
    "daisywheel_caps": False,
    "laser_ring_active": False,
    "magnifier_active": False,
    "pressed_buttons": set(),
    "toggled_buttons": set(),
    "stick_telemetry": (0.0, 0.0, 0.0, 0.0),
    "speed_multiplier": 1.0,
    "detected_window": "Desktop"
}

STATE_LOCK = threading.Lock()

# --- UPDATE CHECKER ENGINE ---
def parse_semver(ver_str):
    """Extracts a comparable integer tuple from version strings like 'v1.2' or '1.2.1'."""
    nums = [int(x) for x in re.findall(r"\d+", str(ver_str))[:4]]
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums)

def fetch_latest_github_release(repo_slug):
    """
    Queries GitHub API for the latest release or tag.
    Returns dict: {"status": "update_available"|"up_to_date"|"error", "latest_ver": str, "url": str, "notes": str, "msg": str}
    """
    headers = {
        "User-Agent": f"JeetPad-Updater/{APP_VERSION}",
        "Accept": "application/vnd.github.v3+json"
    }
    release_api = f"https://api.github.com/repos/{repo_slug}/releases/latest"
    tags_api = f"https://api.github.com/repos/{repo_slug}/tags"
    html_fallback = f"https://github.com/{repo_slug}/releases"

    try:
        req = urllib.request.Request(release_api, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            tag_name = data.get("tag_name", "")
            html_url = data.get("html_url", html_fallback)
            body = data.get("body", "No release notes provided.")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            try:
                req2 = urllib.request.Request(tags_api, headers=headers)
                with urllib.request.urlopen(req2, timeout=6) as resp2:
                    tags_data = json.loads(resp2.read().decode("utf-8"))
                    if tags_data and isinstance(tags_data, list):
                        tag_name = tags_data[0].get("name", "")
                        html_url = html_fallback
                        body = "New tagged version available on GitHub."
                    else:
                        return {
                            "status": "up_to_date",
                            "latest_ver": APP_VERSION,
                            "url": html_fallback,
                            "notes": "",
                            "msg": f"You are running the latest version (v{APP_VERSION})."
                        }
            except Exception as ex:
                return {"status": "error", "latest_ver": APP_VERSION, "url": html_fallback, "notes": "", "msg": f"Could not reach repository ({repo_slug}): {ex}"}
        else:
            return {"status": "error", "latest_ver": APP_VERSION, "url": html_fallback, "notes": "", "msg": f"GitHub API HTTP {e.code}"}
    except Exception as e:
        return {"status": "error", "latest_ver": APP_VERSION, "url": html_fallback, "notes": "", "msg": f"Network error while checking updates: {e}"}

    cur_tuple = parse_semver(APP_VERSION)
    lat_tuple = parse_semver(tag_name)
    clean_latest = tag_name.lstrip("vV") or APP_VERSION

    if lat_tuple > cur_tuple:
        return {
            "status": "update_available",
            "latest_ver": clean_latest,
            "url": html_url,
            "notes": body or "Bug fixes and performance improvements.",
            "msg": f"A new version (v{clean_latest}) is available!"
        }
    return {
        "status": "up_to_date",
        "latest_ver": clean_latest,
        "url": html_url,
        "notes": body,
        "msg": f"JeetPad v{APP_VERSION} is up to date."
    }

def get_current_profile():
    prof_name = APP_STATE.get("active_profile", "Desktop")
    profs = APP_STATE.get("profiles", DEFAULT_PROFILES)
    if prof_name not in profs:
        prof_name = list(profs.keys())[0]
        APP_STATE["active_profile"] = prof_name
    return profs[prof_name]

def sanitize_profile_dict(prof):
    base = make_profile(BASE_DESKTOP_MAP)
    if "mappings" in prof:
        base["mappings"].update({int(k): v for k, v in prof["mappings"].items()})
    if "combo_mappings" in prof:
        base["combo_mappings"].update({int(k): v for k, v in prof["combo_mappings"].items()})
    if "btn_modes" in prof:
        base["btn_modes"].update({int(k): v for k, v in prof["btn_modes"].items()})
    base["app_rules"] = str(prof.get("app_rules", ""))
    return base

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            with STATE_LOCK:
                if "profiles" in saved:
                    cleaned_profiles = {}
                    for p_name, p_data in saved["profiles"].items():
                        cleaned_profiles[p_name] = sanitize_profile_dict(p_data)
                    APP_STATE["profiles"] = cleaned_profiles
                elif "mappings" in saved:
                    APP_STATE["profiles"]["Desktop"] = sanitize_profile_dict(saved)

                exclude = {
                    "profiles", "available_controllers", "rescan_requested",
                    "pressed_buttons", "toggled_buttons", "mod_currently_held",
                    "hud_visible", "radial_active", "radial_selected_idx",
                    "daisywheel_active", "daisywheel_petal_idx", "daisywheel_caps",
                    "laser_ring_active", "magnifier_active", "stick_telemetry",
                    "speed_multiplier", "detected_window", "auto_paused_by_game",
                    "github_repo"
                }
                for k, v in saved.items():
                    if k not in exclude and k in APP_STATE:
                        APP_STATE[k] = v

                # Ensure repo stays synced to current DEFAULT_GITHUB_REPO / .git
                APP_STATE["github_repo"] = detect_github_repo()

                if "radial_wheel_enabled" not in saved:
                    APP_STATE["hud_enabled"] = False

                if APP_STATE.get("color_theme") not in THEME_PRESETS:
                    APP_STATE["color_theme"] = "Ocean Blue"
                apply_theme_palette(APP_STATE["color_theme"])
        except Exception:
            apply_theme_palette("Ocean Blue")
    else:
        apply_theme_palette(APP_STATE["color_theme"])

def save_config():
    try:
        with STATE_LOCK:
            exclude = {
                "available_controllers", "rescan_requested", "pressed_buttons",
                "toggled_buttons", "mod_currently_held", "hud_visible",
                "radial_active", "radial_selected_idx", "daisywheel_active",
                "daisywheel_petal_idx", "daisywheel_caps", "laser_ring_active",
                "magnifier_active", "stick_telemetry", "speed_multiplier",
                "detected_window", "auto_paused_by_game"
            }
            save_data = {k: v for k, v in APP_STATE.items() if k not in exclude}
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=4)
    except Exception:
        pass

# --- SYNTHESIZED AUDIO BEEPS ---
def play_audio_cue(cue_type):
    if not APP_STATE.get("audio_beeps_enabled", False) or winsound is None:
        return
    def _beep():
        try:
            if cue_type == "enable":
                winsound.Beep(587, 70)
                winsound.Beep(880, 90)
            elif cue_type == "pause":
                winsound.Beep(659, 70)
                winsound.Beep(440, 110)
            elif cue_type == "profile":
                winsound.Beep(740, 45)
            elif cue_type == "pin":
                winsound.Beep(987, 60)
        except Exception:
            pass
    threading.Thread(target=_beep, daemon=True).start()

# --- INACTIVITY SCREEN OFF ---
def trigger_idle_screen_off():
    if platform.system() == "Windows":
        try:
            HWND_BROADCAST = 0xFFFF
            WM_SYSCOMMAND = 0x0112
            SC_MONITORPOWER = 0xF170
            ctypes.windll.user32.SendMessageW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, 2)
        except Exception:
            pass
    elif platform.system() == "Linux":
        subprocess.Popen(["xset", "dpms", "force", "off"])

# --- MULTI-MONITOR TELEPORT, EDGE WRAP & WINDOW MANAGEMENT ---
def get_monitors_win32():
    monitors = []
    if platform.system() == "Windows":
        try:
            MonitorEnumProc = ctypes.WINFUNCTYPE(
                ctypes.c_int, wintypes.HMONITOR, wintypes.HDC,
                ctypes.POINTER(wintypes.RECT), wintypes.LPARAM
            )
            def _callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
                r = lprcMonitor.contents
                monitors.append((r.left, r.top, r.right, r.bottom))
                return 1
            ctypes.windll.user32.EnumDisplayMonitors(None, None, MonitorEnumProc(_callback), 0)
        except Exception:
            pass
    if not monitors:
        if platform.system() == "Windows":
            u32 = ctypes.windll.user32
            monitors.append((0, 0, u32.GetSystemMetrics(0), u32.GetSystemMetrics(1)))
        else:
            monitors.append((0, 0, 1920, 1080))
    return monitors

def get_virtual_screen_bounds():
    if platform.system() == "Windows":
        u32 = ctypes.windll.user32
        vx = u32.GetSystemMetrics(76)
        vy = u32.GetSystemMetrics(77)
        vw = u32.GetSystemMetrics(78)
        vh = u32.GetSystemMetrics(79)
        if vw > 0 and vh > 0:
            return vx, vy, vx + vw, vy + vh
        return 0, 0, u32.GetSystemMetrics(0), u32.GetSystemMetrics(1)
    return 0, 0, 1920, 1080

def teleport_cursor_center(mouse):
    if platform.system() == "Windows":
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if hwnd:
            rect = wintypes.RECT()
            if ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                cx = (rect.left + rect.right) // 2
                cy = (rect.top + rect.bottom) // 2
                mouse.position = (cx, cy)
                return
    l, t, r, b = get_virtual_screen_bounds()
    mouse.position = ((l + r) // 2, (t + b) // 2)

def teleport_next_monitor(mouse):
    monitors = get_monitors_win32()
    if len(monitors) <= 1:
        l, t, r, b = monitors[0]
        mouse.position = ((l + r) // 2, (t + b) // 2)
        return
    mx, my = mouse.position
    cur_idx = 0
    for i, (l, t, r, b) in enumerate(monitors):
        if l <= mx <= r and t <= my <= b:
            cur_idx = i
            break
    nxt_idx = (cur_idx + 1) % len(monitors)
    nl, nt, nr, nb = monitors[nxt_idx]
    mouse.position = ((nl + nr) // 2, (nt + nb) // 2)

def toggle_always_on_top():
    if platform.system() == "Windows":
        try:
            u32 = ctypes.windll.user32
            hwnd = u32.GetForegroundWindow()
            if not hwnd:
                return
            GWL_EXSTYLE = -20
            WS_EX_TOPMOST = 0x00000008
            HWND_TOPMOST = -1
            HWND_NOTOPMOST = -2
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            ex_style = u32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            is_top = bool(ex_style & WS_EX_TOPMOST)
            target_flag = HWND_NOTOPMOST if is_top else HWND_TOPMOST
            u32.SetWindowPos(hwnd, target_flag, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
            play_audio_cue("pin")
        except Exception:
            pass

def apply_edge_wrapping(mouse):
    try:
        vx1, vy1, vx2, vy2 = get_virtual_screen_bounds()
        mx, my = mouse.position
        new_x, new_y = mx, my
        margin = 2
        if mx >= vx2 - margin:
            new_x = vx1 + margin + 1
        elif mx <= vx1 + margin:
            new_x = vx2 - margin - 1
        if my >= vy2 - margin:
            new_y = vy1 + margin + 1
        elif my <= vy1 + margin:
            new_y = vy2 - margin - 1
        if (new_x, new_y) != (mx, my):
            mouse.position = (new_x, new_y)
    except Exception:
        pass

# --- OS WINDOW & FULLSCREEN DETECTION ---
def get_active_window_info():
    if platform.system() == "Windows":
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return "", False

            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value.lower()

            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            exe_name = ""
            h_proc = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid.value)
            if h_proc:
                exe_buf = ctypes.create_unicode_buffer(260)
                size = wintypes.DWORD(260)
                if ctypes.windll.kernel32.QueryFullProcessImageNameW(h_proc, 0, exe_buf, ctypes.byref(size)):
                    exe_name = os.path.basename(exe_buf.value).lower()
                ctypes.windll.kernel32.CloseHandle(h_proc)

            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            scr_w = user32.GetSystemMetrics(0)
            scr_h = user32.GetSystemMetrics(1)
            win_w = rect.right - rect.left
            win_h = rect.bottom - rect.top

            shell_ignores = {"explorer.exe", "python.exe", "pythonw.exe", "jeetpad.exe", "applicationframehost.exe", "searchhost.exe"}
            is_fs = (win_w >= scr_w and win_h >= scr_h and rect.left <= 0 and rect.top <= 0)
            if exe_name in shell_ignores or "jeetpad" in title:
                is_fs = False

            return f"{exe_name} {title}".strip(), is_fs
        except Exception:
            return "", False
    elif platform.system() == "Linux":
        try:
            win_id = subprocess.check_output(["xdotool", "getactivewindow"], stderr=subprocess.DEVNULL).decode().strip()
            win_name = subprocess.check_output(["xdotool", "getwindowname", win_id], stderr=subprocess.DEVNULL).decode().strip().lower()
            return win_name, False
        except Exception:
            return "", False
    return "", False

def is_autostart_enabled():
    app_name = "JeetPad"
    if platform.system() == "Windows":
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, app_name)
            winreg.CloseKey(key)
            return True
        except OSError:
            return False
    elif platform.system() == "Linux":
        return (Path.home() / ".config" / "autostart" / f"{app_name}.desktop").exists()
    return False

def set_autostart(enable=True):
    app_name = "JeetPad"
    script_path = os.path.abspath(sys.argv[0])
    icon_path = resource_path("icon.png")
    exec_cmd = f'"{script_path}"' if getattr(sys, 'frozen', False) else f'"{sys.executable}" "{script_path}"'

    if platform.system() == "Windows":
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            if enable:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exec_cmd)
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except OSError:
                    pass
            winreg.CloseKey(key)
        except Exception:
            pass
    elif platform.system() == "Linux":
        autostart_dir = Path.home() / ".config" / "autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)
        desktop_file = autostart_dir / f"{app_name}.desktop"
        if enable:
            content = (
                "[Desktop Entry]\nType=Application\n"
                f"Exec={exec_cmd}\nIcon={icon_path}\n"
                "Hidden=false\nNoDisplay=false\nX-GNOME-Autostart-enabled=true\n"
                f"Name={app_name}\n"
            )
            with open(desktop_file, "w", encoding="utf-8") as f:
                f.write(content)
        elif desktop_file.exists():
            desktop_file.unlink()

def trigger_haptic_cue(joystick, enabled_state):
    play_audio_cue("enable" if enabled_state else "pause")
    if not joystick:
        return
    def _rumble_worker():
        try:
            if enabled_state:
                joystick.rumble(0.4, 0.8, 150)
            else:
                joystick.rumble(0.9, 0.2, 130)
                time.sleep(0.20)
                joystick.rumble(0.9, 0.2, 160)
        except Exception:
            pass
    threading.Thread(target=_rumble_worker, daemon=True).start()

# --- ACTION & TIMED MACRO EXECUTION ENGINE ---
def resolve_key(k_str):
    k_str = k_str.strip()
    if hasattr(Key, k_str):
        return getattr(Key, k_str)
    return k_str

def launch_touch_keyboard(keyboard):
    if platform.system() == "Windows":
        tabtip_paths = [
            r"C:\Program Files\Common Files\microsoft shared\ink\TabTip.exe",
            r"C:\Program Files (x86)\Common Files\microsoft shared\ink\TabTip.exe"
        ]
        for p in tabtip_paths:
            if os.path.exists(p):
                try:
                    os.startfile(p)
                    return
                except Exception:
                    pass
        keyboard.press(Key.cmd)
        keyboard.press(Key.ctrl)
        keyboard.press('o')
        keyboard.release('o')
        keyboard.release(Key.ctrl)
        keyboard.release(Key.cmd)
    elif platform.system() == "Linux":
        subprocess.Popen(["onboard"])

def change_brightness(delta):
    if platform.system() == "Windows":
        cmd = (
            f"$m = Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods; "
            f"$b = (Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness).CurrentBrightness; "
            f"$n = [math]::Max(0, [math]::Min(100, $b + ({delta}))); "
            f"$m.WmiSetBrightness(1, $n)"
        )
        subprocess.Popen(["powershell", "-WindowStyle", "Hidden", "-NoProfile", "-Command", cmd], creationflags=0x08000000)
    elif platform.system() == "Linux":
        sign = "+" if delta > 0 else "-"
        subprocess.Popen(["brightnessctl", "set", f"{abs(delta)}%{sign}"])

def run_macro_sequence(seq_str, mouse, keyboard):
    def _runner():
        steps = [s.strip() for s in seq_str.split("->") if s.strip()]
        for step in steps:
            if step.lower().startswith("wait:"):
                try:
                    ms = float(step.split(":", 1)[1].strip().replace("ms", ""))
                    time.sleep(max(0.0, ms / 1000.0))
                except Exception:
                    time.sleep(0.1)
            else:
                execute_action(step, mouse, keyboard, True)
                time.sleep(0.025)
                execute_action(step, mouse, keyboard, False)
    threading.Thread(target=_runner, daemon=True).start()

def execute_action(action_str, mouse, keyboard, is_press=True):
    if not action_str or action_str == "None":
        return
    try:
        if action_str == "System: Radial Wheel":
            if not APP_STATE.get("radial_wheel_enabled", False):
                return
            if is_press:
                APP_STATE["radial_selected_idx"] = -1
                APP_STATE["radial_active"] = True
            else:
                if APP_STATE.get("radial_active", False):
                    sel = APP_STATE.get("radial_selected_idx", -1)
                    APP_STATE["radial_active"] = False
                    slots = APP_STATE.get("radial_slots", DEFAULT_RADIAL_SLOTS)
                    if 0 <= sel < len(slots):
                        target_act = slots[sel].get("action", "None")
                        if target_act and target_act != "None" and target_act != "System: Radial Wheel":
                            execute_action(target_act, mouse, keyboard, True)
                            execute_action(target_act, mouse, keyboard, False)
            return

        elif action_str == "System: Daisywheel":
            if is_press and APP_STATE.get("daisywheel_enabled", False):
                APP_STATE["daisywheel_active"] = not APP_STATE.get("daisywheel_active", False)
            return

        elif action_str == "System: Laser Ring":
            if APP_STATE.get("laser_ring_enabled", False):
                APP_STATE["laser_ring_active"] = bool(is_press)
            return

        elif action_str.startswith("MacroSeq: "):
            if is_press:
                run_macro_sequence(action_str.split(": ", 1)[1], mouse, keyboard)
            return

        elif action_str.startswith("Text: "):
            if is_press:
                snippet = action_str.split(": ", 1)[1]
                threading.Thread(target=keyboard.type, args=(snippet,), daemon=True).start()
            return

        elif action_str in ("Virtual Keyboard", "OSK: TabTip"):
            if is_press:
                launch_touch_keyboard(keyboard)
            return
        elif action_str == "OSK: Legacy":
            if is_press:
                if platform.system() == "Windows":
                    subprocess.Popen(["osk"], shell=True)
                elif platform.system() == "Linux":
                    subprocess.Popen(["onboard"])
            return

        elif action_str == "System: HUD":
            if APP_STATE.get("hud_enabled", False):
                APP_STATE["hud_visible"] = bool(is_press)
            return

        elif action_str.startswith("Media: "):
            m_act = action_str.split(": ", 1)[1]
            media_map = {
                "Vol Up": Key.media_volume_up,
                "Vol Down": Key.media_volume_down,
                "Mute": Key.media_volume_mute,
                "Play/Pause": Key.media_play_pause,
                "Next Track": Key.media_next,
                "Prev Track": Key.media_previous
            }
            if m_act in media_map:
                k_obj = media_map[m_act]
                if is_press:
                    keyboard.press(k_obj)
                else:
                    keyboard.release(k_obj)
            return

        elif action_str.startswith("System: "):
            s_act = action_str.split(": ", 1)[1]
            if not is_press:
                return
            if s_act == "Screenshot":
                execute_action("Combo: cmd+shift+s", mouse, keyboard, True)
                execute_action("Combo: cmd+shift+s", mouse, keyboard, False)
            elif s_act == "Lock PC":
                if platform.system() == "Windows":
                    ctypes.windll.user32.LockWorkStation()
                elif platform.system() == "Linux":
                    subprocess.Popen(["xdg-screensaver", "lock"])
            elif s_act == "Brightness Up":
                threading.Thread(target=change_brightness, args=(10,), daemon=True).start()
            elif s_act == "Brightness Down":
                threading.Thread(target=change_brightness, args=(-10,), daemon=True).start()
            elif s_act == "Center Cursor":
                teleport_cursor_center(mouse)
            elif s_act == "Next Monitor":
                teleport_next_monitor(mouse)
            elif s_act == "Snap Left":
                execute_action("Combo: cmd+left", mouse, keyboard, True)
                execute_action("Combo: cmd+left", mouse, keyboard, False)
            elif s_act == "Snap Right":
                execute_action("Combo: cmd+right", mouse, keyboard, True)
                execute_action("Combo: cmd+right", mouse, keyboard, False)
            elif s_act == "Maximize Window":
                execute_action("Combo: cmd+up", mouse, keyboard, True)
                execute_action("Combo: cmd+up", mouse, keyboard, False)
            elif s_act == "Minimize Window":
                execute_action("Combo: cmd+down", mouse, keyboard, True)
                execute_action("Combo: cmd+down", mouse, keyboard, False)
            elif s_act == "Next Desktop":
                execute_action("Combo: ctrl+cmd+right", mouse, keyboard, True)
                execute_action("Combo: ctrl+cmd+right", mouse, keyboard, False)
            elif s_act == "Prev Desktop":
                execute_action("Combo: ctrl+cmd+left", mouse, keyboard, True)
                execute_action("Combo: ctrl+cmd+left", mouse, keyboard, False)
            elif s_act == "Pin Always on Top":
                toggle_always_on_top()
            elif s_act == "Magnifier Toggle":
                if not APP_STATE.get("magnifier_active", False):
                    APP_STATE["magnifier_active"] = True
                    execute_action("Combo: cmd+=", mouse, keyboard, True)
                    execute_action("Combo: cmd+=", mouse, keyboard, False)
                else:
                    APP_STATE["magnifier_active"] = False
                    execute_action("Combo: cmd+esc", mouse, keyboard, True)
                    execute_action("Combo: cmd+esc", mouse, keyboard, False)
            elif s_act == "Magnifier Zoom In":
                APP_STATE["magnifier_active"] = True
                execute_action("Combo: cmd+=", mouse, keyboard, True)
                execute_action("Combo: cmd+=", mouse, keyboard, False)
            elif s_act == "Magnifier Zoom Out":
                execute_action("Combo: cmd+-", mouse, keyboard, True)
                execute_action("Combo: cmd+-", mouse, keyboard, False)
            return

        elif action_str.startswith("Launch: "):
            if is_press:
                target = action_str.split(": ", 1)[1].strip()
                if os.path.exists(target) and platform.system() == "Windows":
                    os.startfile(target)
                else:
                    subprocess.Popen(target, shell=True)
            return

        elif action_str.startswith("Mouse: "):
            action = action_str.split(": ", 1)[1]
            if action == "Left": btn = MouseButton.left
            elif action == "Right": btn = MouseButton.right
            elif action == "Middle": btn = MouseButton.middle
            elif action == "Scroll Up":
                if is_press: mouse.scroll(0, 1)
                return
            elif action == "Scroll Down":
                if is_press: mouse.scroll(0, -1)
                return
            elif action == "Scroll Left":
                if is_press: mouse.scroll(-1, 0)
                return
            elif action == "Scroll Right":
                if is_press: mouse.scroll(1, 0)
                return
            else:
                return
            if is_press:
                mouse.press(btn)
            else:
                mouse.release(btn)

        elif action_str.startswith("Key: "):
            key_obj = resolve_key(action_str.split(": ", 1)[1])
            if is_press:
                keyboard.press(key_obj)
            else:
                keyboard.release(key_obj)

        elif action_str.startswith("Combo: "):
            keys = action_str.split(": ", 1)[1].split("+")
            if is_press:
                for k in keys:
                    keyboard.press(resolve_key(k))
            else:
                for k in reversed(keys):
                    keyboard.release(resolve_key(k))
    except Exception:
        pass

def apply_deadzone(val, deadzone):
    if abs(val) < deadzone:
        return 0.0
    sign = 1.0 if val > 0 else -1.0
    normalized = (abs(val) - deadzone) / max(0.01, (1.0 - deadzone))
    return sign * (0.4 * normalized + 0.6 * (normalized ** 2))

def compute_8way_sector(x, y, threshold=0.38):
    mag = math.hypot(x, y)
    if mag < threshold:
        return -1
    angle = (math.degrees(math.atan2(x, -y)) + 360.0) % 360.0
    return int(((angle + 22.5) % 360.0) // 45.0)

# --- BACKGROUND CONTROLLER & TELEMETRY WORKER ---
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
            try:
                j = pygame.joystick.Joystick(i)
                j.init()
                joysticks[i] = j
                names.append(f"[{i}] {j.get_name()}")
            except Exception:
                pass
        with STATE_LOCK:
            if not names:
                names = ["No Controller Detected"]
                APP_STATE["selected_controller_idx"] = 0
            APP_STATE["available_controllers"] = names
            if APP_STATE["selected_controller_idx"] >= len(joysticks) and len(joysticks) > 0:
                APP_STATE["selected_controller_idx"] = 0

    perform_scan()
    mouse, keyboard = MouseController(), KeyboardController()
    HOLD_DURATION = 3.0

    toggle_held, toggle_press_time, toggle_executed = False, 0.0, False
    last_scan_time = time.time()
    last_win_check = time.time()
    last_activity_time = time.time()
    idle_sleep_triggered = False

    last_hat_x, last_hat_y = 0, 0
    last_sec_x = 0.0
    last_lt, last_rt = -1.0, -1.0
    scroll_accumulator = 0.0

    active_presses = {}
    turbo_held = {}
    toggle_latched = {}

    def release_all_active():
        for btn_id, act in list(active_presses.items()):
            execute_action(act, mouse, keyboard, False)
        for btn_id, act in list(toggle_latched.items()):
            execute_action(act, mouse, keyboard, False)
        active_presses.clear()
        turbo_held.clear()
        toggle_latched.clear()
        APP_STATE["pressed_buttons"].clear()
        APP_STATE["toggled_buttons"].clear()
        APP_STATE["radial_active"] = False
        APP_STATE["laser_ring_active"] = False

    def is_modifier_held(joystick, lt_axis, rt_axis):
        mod = APP_STATE["combo_modifier"]
        if mod == "None":
            return False
        try:
            if mod == "LT" and lt_axis != -1: return joystick.get_axis(lt_axis) > 0.1
            if mod == "RT" and rt_axis != -1: return joystick.get_axis(rt_axis) > 0.1
            if mod == "LB" and joystick.get_numbuttons() > 4: return bool(joystick.get_button(4))
            if mod == "RB" and joystick.get_numbuttons() > 5: return bool(joystick.get_button(5))
        except Exception:
            pass
        return False

    def resolve_mapping_action(btn_id, is_combo):
        prof = get_current_profile()
        if is_combo:
            combo_act = prof["combo_mappings"].get(btn_id, "None")
            if combo_act and combo_act != "None":
                return combo_act
        return prof["mappings"].get(btn_id, "None")

    def handle_daisywheel_button(btn_id):
        petal_idx = APP_STATE.get("daisywheel_petal_idx", -1)
        caps = APP_STATE.get("daisywheel_caps", False)
        btn_key_map = {0: "A", 1: "B", 2: "X", 3: "Y"}
        if btn_id in btn_key_map:
            if 0 <= petal_idx < len(DAISYWHEEL_PETALS):
                ch = DAISYWHEEL_PETALS[petal_idx][1].get(btn_key_map[btn_id], "")
                if ch:
                    out = ch.upper() if caps else ch
                    keyboard.type(out)
            return True
        elif btn_id == 4:
            keyboard.press(Key.backspace)
            keyboard.release(Key.backspace)
            return True
        elif btn_id == 5:
            keyboard.press(Key.space)
            keyboard.release(Key.space)
            return True
        elif btn_id == 8:
            APP_STATE["daisywheel_caps"] = not caps
            return True
        elif btn_id == 7:
            keyboard.press(Key.enter)
            keyboard.release(Key.enter)
            return True
        elif btn_id == 6:
            APP_STATE["daisywheel_active"] = False
            return True
        return False

    def handle_press(btn_id, current_time, is_combo):
        nonlocal toggle_held, toggle_press_time, toggle_executed, last_activity_time, idle_sleep_triggered
        last_activity_time = current_time
        idle_sleep_triggered = False
        APP_STATE["pressed_buttons"].add(btn_id)

        mod_btn_id = MODIFIER_BTN_MAP.get(APP_STATE["combo_modifier"])
        if btn_id == mod_btn_id:
            return

        if APP_STATE.get("daisywheel_enabled", False) and APP_STATE.get("daisywheel_active", False):
            act_check = resolve_mapping_action(btn_id, is_combo)
            if act_check == "System: Daisywheel":
                APP_STATE["daisywheel_active"] = False
                return
            if handle_daisywheel_button(btn_id):
                return

        if APP_STATE["trigger_Precision"] and btn_id in (106, 107):
            act_check = resolve_mapping_action(btn_id, is_combo)
            if not act_check or act_check == "None":
                return

        if btn_id == APP_STATE["toggle_button"]:
            toggle_held, toggle_press_time, toggle_executed = True, current_time, False
        elif APP_STATE["enabled"] and not APP_STATE["auto_paused_by_game"]:
            prof = get_current_profile()
            mode = prof["btn_modes"].get(btn_id, "Normal")
            action = resolve_mapping_action(btn_id, is_combo)
            if not action or action == "None":
                return

            if mode == "Toggle":
                if btn_id in toggle_latched:
                    old_act = toggle_latched.pop(btn_id)
                    APP_STATE["toggled_buttons"].discard(btn_id)
                    execute_action(old_act, mouse, keyboard, False)
                else:
                    toggle_latched[btn_id] = action
                    APP_STATE["toggled_buttons"].add(btn_id)
                    execute_action(action, mouse, keyboard, True)
            elif mode == "Turbo":
                execute_action(action, mouse, keyboard, True)
                execute_action(action, mouse, keyboard, False)
                turbo_held[btn_id] = (action, current_time)
            else:
                if btn_id in active_presses:
                    execute_action(active_presses.pop(btn_id), mouse, keyboard, False)
                active_presses[btn_id] = action
                execute_action(action, mouse, keyboard, True)

    def handle_release(btn_id, is_combo):
        nonlocal toggle_held, toggle_executed
        APP_STATE["pressed_buttons"].discard(btn_id)

        mod_btn_id = MODIFIER_BTN_MAP.get(APP_STATE["combo_modifier"])
        if btn_id == mod_btn_id:
            return

        if btn_id == APP_STATE["toggle_button"]:
            toggle_held = False
            if not toggle_executed and APP_STATE["enabled"] and not APP_STATE["auto_paused_by_game"]:
                action = resolve_mapping_action(btn_id, is_combo)
                if action and action != "None":
                    execute_action(action, mouse, keyboard, True)
                    execute_action(action, mouse, keyboard, False)
        else:
            turbo_held.pop(btn_id, None)
            action = active_presses.pop(btn_id, None)
            if action:
                execute_action(action, mouse, keyboard, False)

    while True:
        current_time = time.time()

        if APP_STATE.get("idle_sleep_enabled", False) and not idle_sleep_triggered:
            timeout_sec = max(1.0, float(APP_STATE.get("idle_timeout_min", 15.0))) * 60.0
            if current_time - last_activity_time >= timeout_sec:
                idle_sleep_triggered = True
                trigger_idle_screen_off()

        if current_time - last_win_check >= 1.0:
            last_win_check = current_time
            win_str, is_fs = get_active_window_info()
            if win_str:
                APP_STATE["detected_window"] = win_str[:38]

            if APP_STATE["auto_pause_fullscreen"]:
                if is_fs and not APP_STATE["auto_paused_by_game"]:
                    APP_STATE["auto_paused_by_game"] = True
                    release_all_active()
                elif not is_fs and APP_STATE["auto_paused_by_game"]:
                    APP_STATE["auto_paused_by_game"] = False
            else:
                APP_STATE["auto_paused_by_game"] = False

            if APP_STATE["auto_switch_profiles"] and win_str:
                with STATE_LOCK:
                    for p_name, p_data in APP_STATE["profiles"].items():
                        rules = [r.strip().lower() for r in p_data.get("app_rules", "").split(",") if r.strip()]
                        if any(r in win_str for r in rules):
                            if APP_STATE["active_profile"] != p_name:
                                APP_STATE["active_profile"] = p_name
                                play_audio_cue("profile")
                            break

        if APP_STATE["auto_scan"] and (current_time - last_scan_time >= APP_STATE["scan_interval"]):
            perform_scan()
            last_scan_time = current_time

        if APP_STATE["rescan_requested"]:
            perform_scan()
            APP_STATE["rescan_requested"] = False
            last_scan_time = current_time

        try:
            pygame.event.pump()
        except Exception:
            time.sleep(0.05)
            continue

        if turbo_held and APP_STATE["enabled"] and not APP_STATE["auto_paused_by_game"]:
            interval = 1.0 / max(1.0, float(APP_STATE.get("turbo_rate", 12.0)))
            for b_id, (act_str, last_fire) in list(turbo_held.items()):
                if current_time - last_fire >= interval:
                    execute_action(act_str, mouse, keyboard, True)
                    execute_action(act_str, mouse, keyboard, False)
                    turbo_held[b_id] = (act_str, current_time)

        idx = APP_STATE["selected_controller_idx"]
        active_joystick = joysticks.get(idx)

        if active_joystick:
            try:
                active_id = active_joystick.get_instance_id()
                num_axes = active_joystick.get_numaxes()
            except Exception:
                perform_scan()
                continue

            if platform.system() == "Linux":
                rx_axis = 3 if num_axes > 3 else 2
                ry_axis = 4 if num_axes > 4 else 3
                lt_axis, rt_axis = 2, 5
            else:
                rx_axis, ry_axis = 2, 3
                lt_axis, rt_axis = 4, 5

            if rx_axis >= num_axes: rx_axis = max(0, num_axes - 1)
            if ry_axis >= num_axes: ry_axis = max(0, num_axes - 1)
            if lt_axis >= num_axes: lt_axis = -1
            if rt_axis >= num_axes: rt_axis = -1

            mod_active = is_modifier_held(active_joystick, lt_axis, rt_axis)
            APP_STATE["mod_currently_held"] = mod_active
            if APP_STATE.get("hud_enabled", False):
                APP_STATE["hud_visible"] = mod_active
            else:
                APP_STATE["hud_visible"] = False

            if toggle_held and not toggle_executed and (current_time - toggle_press_time >= HOLD_DURATION):
                APP_STATE["enabled"] = not APP_STATE["enabled"]
                if not APP_STATE["enabled"]:
                    release_all_active()
                trigger_haptic_cue(active_joystick, APP_STATE["enabled"])
                toggle_executed = True
                save_config()

            if num_axes >= 2:
                lx, ly = active_joystick.get_axis(0), active_joystick.get_axis(1)
                rx, ry = active_joystick.get_axis(rx_axis), active_joystick.get_axis(ry_axis)

                if APP_STATE["swap_sticks"]:
                    raw_mx, raw_my = rx, ry
                    raw_sy, sec_stick_x = ly, lx
                else:
                    raw_mx, raw_my = lx, ly
                    raw_sy, sec_stick_x = ry, rx

                lt_norm = (active_joystick.get_axis(lt_axis) + 1.0) / 2.0 if lt_axis != -1 else 0.0
                rt_norm = (active_joystick.get_axis(rt_axis) + 1.0) / 2.0 if rt_axis != -1 else 0.0
                APP_STATE["stick_telemetry"] = (raw_mx, raw_my, lt_norm, rt_norm)

                dz = float(APP_STATE.get("deadzone", 0.14))
                if abs(lx) > dz or abs(ly) > dz or abs(rx) > dz or abs(ry) > dz or lt_norm > 0.15 or rt_norm > 0.15:
                    last_activity_time = current_time
                    idle_sleep_triggered = False

                speed_mult = 1.0
                if APP_STATE["trigger_Precision"]:
                    if lt_norm > 0.08 and APP_STATE["combo_modifier"] != "LT":
                        speed_mult *= (1.0 - 0.70 * lt_norm)
                    if rt_norm > 0.08 and APP_STATE["combo_modifier"] != "RT":
                        speed_mult *= (1.0 + 1.00 * rt_norm)
                APP_STATE["speed_multiplier"] = speed_mult

                if APP_STATE["enabled"] and not APP_STATE["auto_paused_by_game"]:
                    if APP_STATE.get("radial_wheel_enabled", False) and APP_STATE.get("radial_active", False):
                        use_x, use_y = (rx, ry) if math.hypot(rx, ry) > math.hypot(lx, ly) else (lx, ly)
                        APP_STATE["radial_selected_idx"] = compute_8way_sector(use_x, use_y, 0.35)
                    elif APP_STATE.get("daisywheel_enabled", False) and APP_STATE.get("daisywheel_active", False):
                        APP_STATE["daisywheel_petal_idx"] = compute_8way_sector(lx, ly, 0.32)
                    else:
                        mx = apply_deadzone(raw_mx, dz)
                        my = apply_deadzone(raw_my, dz)
                        if mx != 0.0 or my != 0.0:
                            eff_speed = APP_STATE["mouse_speed"] * speed_mult
                            mouse.move(mx * eff_speed, my * eff_speed)
                            if APP_STATE.get("edge_wrap_enabled", False):
                                apply_edge_wrapping(mouse)

                        sy = apply_deadzone(raw_sy, dz)
                        if sy != 0.0:
                            scroll_accumulator += (-sy * APP_STATE["scroll_speed"] * 0.25)
                            if abs(scroll_accumulator) >= 1.0:
                                steps = int(scroll_accumulator)
                                mouse.scroll(0, steps)
                                scroll_accumulator -= steps
                        else:
                            scroll_accumulator = 0.0

                        current_sec_x = sec_stick_x
                        if current_sec_x < -0.5 and last_sec_x >= -0.5: handle_press(104, current_time, mod_active)
                        elif last_sec_x < -0.5 and current_sec_x >= -0.5: handle_release(104, mod_active)

                        if current_sec_x > 0.5 and last_sec_x <= 0.5: handle_press(105, current_time, mod_active)
                        elif last_sec_x > 0.5 and current_sec_x <= 0.5: handle_release(105, mod_active)
                        last_sec_x = current_sec_x

                    if lt_axis != -1:
                        current_lt = active_joystick.get_axis(lt_axis)
                        if current_lt > 0.1 and last_lt <= 0.1: handle_press(106, current_time, mod_active)
                        elif last_lt > 0.1 and current_lt <= 0.1: handle_release(106, mod_active)
                        last_lt = current_lt

                    if rt_axis != -1:
                        current_rt = active_joystick.get_axis(rt_axis)
                        if current_rt > 0.1 and last_rt <= 0.1: handle_press(107, current_time, mod_active)
                        elif last_rt > 0.1 and current_rt <= 0.1: handle_release(107, mod_active)
                        last_rt = current_rt

            for event in pygame.event.get():
                if hasattr(event, "instance_id") and event.instance_id != active_id:
                    continue
                if event.type == pygame.JOYBUTTONDOWN:
                    handle_press(event.button, current_time, mod_active)
                elif event.type == pygame.JOYBUTTONUP:
                    handle_release(event.button, mod_active)
                elif event.type == pygame.JOYHATMOTION and event.hat == 0:
                    hx, hy = event.value
                    if hy == 1 and last_hat_y != 1: handle_press(100, current_time, mod_active)
                    elif last_hat_y == 1 and hy != 1: handle_release(100, mod_active)
                    if hy == -1 and last_hat_y != -1: handle_press(101, current_time, mod_active)
                    elif last_hat_y == -1 and hy != -1: handle_release(101, mod_active)
                    if hx == -1 and last_hat_x != -1: handle_press(102, current_time, mod_active)
                    elif last_hat_x == -1 and hx != -1: handle_release(102, mod_active)
                    if hx == 1 and last_hat_x != 1: handle_press(103, current_time, mod_active)
                    elif last_hat_x == 1 and hx != 1: handle_release(103, mod_active)
                    last_hat_x, last_hat_y = hx, hy
        else:
            APP_STATE["mod_currently_held"] = False
            APP_STATE["hud_visible"] = False
            APP_STATE["radial_active"] = False
            APP_STATE["laser_ring_active"] = False
            APP_STATE["pressed_buttons"].clear()
            pygame.event.clear()
        time.sleep(0.008)


# --- UPDATE NOTIFICATION DIALOG ---
class UpdateDialog(ctk.CTkToplevel):
    def __init__(self, parent, result_dict):
        super().__init__(parent)
        status = result_dict.get("status", "up_to_date")
        latest_ver = result_dict.get("latest_ver", APP_VERSION)
        url = result_dict.get("url", f"https://github.com/{APP_STATE['github_repo']}/releases")
        notes = result_dict.get("notes", "")
        msg = result_dict.get("msg", "")

        self.title("JeetPad — Software Update")
        self.geometry("500x360")
        self.configure(fg_color=COLORS["bg_dark"])
        self.resizable(False, False)
        self.after(50, self.grab_set)
        self.focus_force()

        card = ctk.CTkFrame(self, fg_color=COLORS["card_bg"], corner_radius=12, border_width=1, border_color=COLORS["card_border"])
        card.pack(fill="both", expand=True, padx=16, pady=16)

        if status == "update_available":
            badge_col = COLORS["success"]
            headline = f"🎉 Update Available: v{latest_ver}"
        elif status == "up_to_date":
            badge_col = COLORS["accent"]
            headline = f"✓ Up to Date (v{APP_VERSION})"
        else:
            badge_col = COLORS["warning"]
            headline = "⚠ Update Check Status"

        ctk.CTkLabel(card, text=headline, font=ctk.CTkFont(size=17, weight="bold"), text_color=badge_col).pack(anchor="w", padx=18, pady=(14, 4))
        ctk.CTkLabel(card, text=f"Installed Version: v{APP_VERSION}   •   Repo: {APP_STATE.get('github_repo')}", font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(anchor="w", padx=18, pady=(0, 8))

        notes_box = ctk.CTkTextbox(card, height=150, fg_color=COLORS["bg_dark"], text_color=COLORS["text_main"], corner_radius=8)
        notes_box.pack(fill="both", expand=True, padx=18, pady=6)
        display_text = f"{msg}\n\n{notes}".strip() if notes else msg
        notes_box.insert("1.0", display_text)
        notes_box.configure(state="disabled")

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=18, pady=(8, 14))

        ctk.CTkButton(
            btn_row, text="Close", width=100, height=34,
            fg_color=COLORS["key_special"], hover_color=COLORS["card_border"],
            command=self.destroy
        ).pack(side="right", padx=(8, 0))

        if status == "update_available":
            ctk.CTkButton(
                btn_row, text="⬇ Download Latest Release", height=34,
                fg_color=COLORS["success"], hover_color="#059669",
                font=ctk.CTkFont(weight="bold"),
                command=lambda: (webbrowser.open(url), self.destroy())
            ).pack(side="right")
        else:
            ctk.CTkButton(
                btn_row, text="Open GitHub Releases", height=34,
                fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                command=lambda: (webbrowser.open(url), self.destroy())
            ).pack(side="right")


# --- OVERLAY 1: SHORTCUT HUD OVERLAY ---
class RadialHUDOverlay(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        try:
            self.attributes("-alpha", 0.90)
        except Exception:
            pass
        self.configure(fg_color=COLORS["bg_dark"])

        w, h = 520, 340
        scr_w = self.winfo_screenwidth()
        scr_h = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(scr_w - w) // 2}+{scr_h - h - 70}")

        self.outer = ctk.CTkFrame(self, fg_color=COLORS["card_bg"], corner_radius=16, border_width=2, border_color=COLORS["accent"])
        self.outer.pack(fill="both", expand=True, padx=2, pady=2)

        self.lbl_header = ctk.CTkLabel(
            self.outer, text="⚡ COMBO SHIFT OVERLAY",
            font=ctk.CTkFont(size=15, weight="bold"), text_color=COLORS["accent"]
        )
        self.lbl_header.pack(pady=(10, 6))

        self.grid_frame = ctk.CTkFrame(self.outer, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        self.grid_frame.grid_columnconfigure((0, 1), weight=1)

        self.cells = {}
        self.cell_frames = []
        display_btns = [0, 1, 2, 3, 4, 5, 100, 101, 102, 103, 8, 9]
        for idx, b_id in enumerate(display_btns):
            r, c = divmod(idx, 2)
            cell = ctk.CTkFrame(self.grid_frame, fg_color=COLORS["bg_dark"], corner_radius=8)
            cell.grid(row=r, column=c, sticky="ew", padx=5, pady=3)
            self.cell_frames.append(cell)
            ctk.CTkLabel(cell, text=BTN_NAMES[b_id].split(" ")[0], width=65, anchor="w", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["warning"]).pack(side="left", padx=8, pady=4)
            val_lbl = ctk.CTkLabel(cell, text="None", anchor="e", font=ctk.CTkFont(size=12), text_color=COLORS["text_main"])
            val_lbl.pack(side="right", padx=8, pady=4)
            self.cells[b_id] = val_lbl

        self.withdraw()

    def apply_theme(self):
        self.configure(fg_color=COLORS["bg_dark"])
        self.outer.configure(fg_color=COLORS["card_bg"], border_color=COLORS["accent"])
        self.lbl_header.configure(text_color=COLORS["accent"])
        for cf in self.cell_frames:
            cf.configure(fg_color=COLORS["bg_dark"])

    def refresh_and_show(self):
        prof = get_current_profile()
        mod_name = APP_STATE.get("combo_modifier", "Shift")
        self.lbl_header.configure(text=f"⚡ ACTIVE SHORTCUTS  —  Profile: {APP_STATE['active_profile']} (Hold {mod_name})")
        for b_id, lbl in self.cells.items():
            c_act = prof["combo_mappings"].get(b_id, "None")
            if c_act and c_act != "None":
                lbl.configure(text=c_act[:26], text_color=COLORS["accent"])
            else:
                s_act = prof["mappings"].get(b_id, "None")
                lbl.configure(text=s_act[:26], text_color=COLORS["text_muted"])
        self.deiconify()
        self.lift()


# --- OVERLAY 2: 8-SECTOR RADIAL PIE WHEEL ---
class RadialWheelOverlay(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        try:
            self.attributes("-alpha", 0.92)
        except Exception:
            pass
        self.configure(fg_color=COLORS["bg_dark"])
        self.size = 380
        self.canvas = tk.Canvas(self, width=self.size, height=self.size, bg=COLORS["bg_dark"], highlightthickness=2, highlightbackground=COLORS["accent"])
        self.canvas.pack(fill="both", expand=True)
        self.last_sel = -2
        self.withdraw()

    def apply_theme(self):
        self.configure(fg_color=COLORS["bg_dark"])
        self.canvas.configure(bg=COLORS["bg_dark"], highlightbackground=COLORS["accent"])
        self.last_sel = -2

    def show_and_render(self, mouse_pos):
        scr_w = self.winfo_screenwidth()
        scr_h = self.winfo_screenheight()
        mx, my = mouse_pos
        x = max(10, min(scr_w - self.size - 10, int(mx - self.size // 2)))
        y = max(10, min(scr_h - self.size - 10, int(my - self.size // 2)))
        if not self.winfo_viewable():
            self.geometry(f"{self.size}x{self.size}+{x}+{y}")
            self.deiconify()
            self.lift()
            self.last_sel = -2

        sel = APP_STATE.get("radial_selected_idx", -1)
        if sel == self.last_sel:
            return
        self.last_sel = sel

        c = self.canvas
        c.delete("all")
        cx, cy = self.size // 2, self.size // 2
        r_outer = 140
        r_inner = 48

        c.create_oval(cx - 170, cy - 170, cx + 170, cy + 170, outline=COLORS["card_border"], width=2)
        slots = APP_STATE.get("radial_slots", DEFAULT_RADIAL_SLOTS)

        for i in range(8):
            ang_deg = i * 45 - 90
            ang_rad = math.radians(ang_deg)
            tx = cx + math.cos(ang_rad) * r_outer * 0.78
            ty = cy + math.sin(ang_rad) * r_outer * 0.78

            is_sel = (i == sel)
            box_bg = COLORS["accent"] if is_sel else COLORS["card_bg"]
            box_bd = "#ffffff" if is_sel else COLORS["card_border"]
            lbl_txt = slots[i]["label"] if i < len(slots) else f"Slot {i+1}"

            c.create_rectangle(tx - 54, ty - 20, tx + 54, ty + 20, fill=box_bg, outline=box_bd, width=2 if is_sel else 1)
            c.create_text(tx, ty, text=lbl_txt[:13], fill=COLORS["text_main"], font=("Arial", 10, "bold"))

        c.create_oval(cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner, fill=COLORS["card_bg"], outline=COLORS["accent"], width=2)
        center_txt = slots[sel]["label"] if (0 <= sel < len(slots)) else "Flick Stick"
        c.create_text(cx, cy, text=center_txt[:12], fill=COLORS["warning"], font=("Arial", 10, "bold"))


# --- OVERLAY 3: THUMBSTICK DAISYWHEEL KEYBOARD ---
class DaisywheelOverlay(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        try:
            self.attributes("-alpha", 0.93)
        except Exception:
            pass
        self.configure(fg_color=COLORS["bg_dark"])
        w, h = 440, 440
        scr_w = self.winfo_screenwidth()
        scr_h = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(scr_w - w) // 2}+{scr_h - h - 50}")

        self.canvas = tk.Canvas(self, width=w, height=h, bg=COLORS["bg_dark"], highlightthickness=2, highlightbackground=COLORS["accent"])
        self.canvas.pack(fill="both", expand=True)
        self.last_state = None
        self.withdraw()

    def apply_theme(self):
        self.configure(fg_color=COLORS["bg_dark"])
        self.canvas.configure(bg=COLORS["bg_dark"], highlightbackground=COLORS["accent"])
        self.last_state = None

    def update_and_show(self):
        if not self.winfo_viewable():
            self.deiconify()
            self.lift()
            self.last_state = None

        petal = APP_STATE.get("daisywheel_petal_idx", -1)
        caps = APP_STATE.get("daisywheel_caps", False)
        if (petal, caps) == self.last_state:
            return
        self.last_state = (petal, caps)

        c = self.canvas
        c.delete("all")
        cx, cy = 220, 220
        radius = 142

        c.create_text(cx, 20, text="🌼 DAISYWHEEL THUMBSTICK TYPER", fill=COLORS["accent"], font=("Arial", 12, "bold"))
        c.create_text(cx, 420, text="[LB] Bksp   [RB] Space   [L3] Caps   [Start] Enter   [Back] Exit", fill=COLORS["text_muted"], font=("Arial", 9))

        for i, (dir_name, char_map) in enumerate(DAISYWHEEL_PETALS):
            ang_rad = math.radians(i * 45 - 90)
            px = cx + math.cos(ang_rad) * radius
            py = cy + math.sin(ang_rad) * radius
            is_sel = (i == petal)
            bg = COLORS["row_active"] if is_sel else COLORS["card_bg"]
            bd = COLORS["accent"] if is_sel else COLORS["card_border"]
            c.create_oval(px - 44, py - 44, px + 44, py + 44, fill=bg, outline=bd, width=3 if is_sel else 1)

            offsets = {"Y": (0, -24, COLORS["warning"]), "X": (-24, 0, COLORS["accent"]), "B": (24, 0, COLORS["danger"]), "A": (0, 24, COLORS["success"])}
            for btn_k, (ox, oy, col) in offsets.items():
                ch = char_map[btn_k].upper() if caps else char_map[btn_k]
                c.create_text(px + ox, py + oy, text=f"{btn_k}:{ch}", fill=col if is_sel else COLORS["text_main"], font=("Arial", 9, "bold"))

        c.create_oval(cx - 48, cy - 48, cx + 48, cy + 48, fill=COLORS["card_bg"], outline=COLORS["accent"], width=2)
        case_str = "CAPS ON" if caps else "lowercase"
        c.create_text(cx, cy, text=f"Left Stick\n({case_str})", fill=COLORS["text_main"], font=("Arial", 9, "bold"), justify="center")


# --- OVERLAY 4: CURSOR "LASER POINTER" RING ---
class CursorLocatorOverlay(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.size = 96
        self.trans_color = "#010101"
        self.configure(bg=self.trans_color)
        if platform.system() == "Windows":
            try:
                self.attributes("-transparentcolor", self.trans_color)
            except Exception:
                pass
        self.canvas = tk.Canvas(self, width=self.size, height=self.size, bg=self.trans_color, highlightthickness=0)
        self.canvas.pack()
        self.draw_rings()
        self.withdraw()

    def draw_rings(self):
        self.canvas.delete("all")
        self.canvas.create_oval(6, 6, self.size - 6, self.size - 6, outline=COLORS["accent"], width=4)
        self.canvas.create_oval(22, 22, self.size - 22, self.size - 22, outline=COLORS["warning"], width=2)

    def follow_cursor(self, mouse_pos):
        mx, my = mouse_pos
        x = int(mx - self.size // 2)
        y = int(my - self.size // 2)
        self.geometry(f"{self.size}x{self.size}+{x}+{y}")
        if not self.winfo_viewable():
            self.deiconify()
        self.lift()


# --- VISUAL ACTION PICKER ---
class VisualPicker(ctk.CTkToplevel):
    def __init__(self, parent, btn_id, is_combo, callback):
        super().__init__(parent)
        mode_tag = "COMBO SHIFT" if is_combo else "STANDARD"
        self.title(f"Assign Action — {BTN_NAMES.get(btn_id, str(btn_id))} [{mode_tag}]")
        self.geometry("1120x560")
        self.configure(fg_color=COLORS["bg_dark"])
        self.resizable(False, False)
        self.callback = callback
        self.btn_id = btn_id
        self.is_combo = is_combo
        self.macro_steps = []
        self.is_recording_keys = False

        self.after(50, self.grab_set)
        self.focus_force()

        top_bar = ctk.CTkFrame(self, fg_color=COLORS["card_bg"], corner_radius=10, border_width=1, border_color=COLORS["card_border"])
        top_bar.pack(fill="x", padx=15, pady=(14, 5))

        ctk.CTkLabel(
            top_bar,
            text=f"Configuring:  {BTN_NAMES.get(btn_id, str(btn_id))}  ({mode_tag})",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text_main"]
        ).pack(side="left", padx=15, pady=10)

        ctk.CTkButton(
            top_bar, text="Ø Unmap (None)", width=120, height=32,
            fg_color=COLORS["danger"], hover_color="#dc2626",
            command=lambda: self.select_action("None")
        ).pack(side="right", padx=10, pady=10)

        ctk.CTkButton(
            top_bar, text="⌨ Legacy OSK", width=110, height=32,
            fg_color=COLORS["key_special"], hover_color=COLORS["accent"],
            command=lambda: self.select_action("OSK: Legacy")
        ).pack(side="right", padx=4, pady=10)

        ctk.CTkButton(
            top_bar, text="📱 Win11 Touch KB", width=150, height=32,
            fg_color=COLORS["warning"], hover_color="#d97706", text_color="#000000",
            font=ctk.CTkFont(weight="bold"),
            command=lambda: self.select_action("OSK: TabTip")
        ).pack(side="right", padx=4, pady=10)

        ctk.CTkButton(
            top_bar, text="🌼 Daisywheel KB", width=140, height=32,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(weight="bold"),
            command=lambda: self.select_action("System: Daisywheel")
        ).pack(side="right", padx=4, pady=10)

        self.tabs = ctk.CTkTabview(
            self, fg_color=COLORS["card_bg"],
            segmented_button_fg_color=COLORS["bg_dark"],
            segmented_button_selected_color=COLORS["accent"],
            segmented_button_selected_hover_color=COLORS["accent_hover"],
            corner_radius=12
        )
        self.tabs.pack(fill="both", expand=True, padx=15, pady=(5, 14))
        self.tabs.add("Keyboard")
        self.tabs.add("Mouse")
        self.tabs.add("Shortcuts & Macros")
        self.tabs.add("Macro Builder & Text")
        self.tabs.add("Media, Window & System")

        self.build_keyboard_tab()
        self.build_mouse_tab()
        self.build_combo_tab()
        self.build_macro_builder_tab()
        self.build_media_system_tab()

    def select_action(self, action):
        self.is_recording_keys = False
        self.callback(self.btn_id, action, self.is_combo)
        self.destroy()

    def build_macro_builder_tab(self):
        tab = self.tabs.tab("Macro Builder & Text")
        wrap = ctk.CTkFrame(tab, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=16, pady=8)
        wrap.grid_columnconfigure(0, weight=3)
        wrap.grid_columnconfigure(1, weight=2)
        wrap.grid_rowconfigure(0, weight=1)

        seq_card = ctk.CTkFrame(wrap, fg_color=COLORS["bg_dark"], corner_radius=12, border_width=1, border_color=COLORS["card_border"])
        seq_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=4)

        ctk.CTkLabel(seq_card, text="⏱ Step-by-Step Timed Macro Builder", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(seq_card, text="Chain multiple keystrokes or combos with millisecond delays between steps:", text_color=COLORS["text_muted"], font=ctk.CTkFont(size=11)).pack(anchor="w", padx=16)

        ctrl_row = ctk.CTkFrame(seq_card, fg_color="transparent")
        ctrl_row.pack(fill="x", padx=16, pady=8)

        self.ent_macro_step = ctk.CTkEntry(ctrl_row, width=165, height=32, placeholder_text="Key: c  or  Combo: ctrl+c")
        self.ent_macro_step.pack(side="left", padx=(0, 6))

        ctk.CTkButton(ctrl_row, text="+ Add Step", width=90, height=32, fg_color=COLORS["key_special"], hover_color=COLORS["accent"], command=self.add_manual_macro_step).pack(side="left", padx=3)

        self.ent_wait_ms = ctk.CTkEntry(ctrl_row, width=65, height=32, justify="center")
        self.ent_wait_ms.insert(0, "150")
        self.ent_wait_ms.pack(side="left", padx=(8, 4))

        ctk.CTkButton(ctrl_row, text="+ Wait (ms)", width=95, height=32, fg_color=COLORS["key_special"], hover_color=COLORS["warning"], command=self.add_wait_step).pack(side="left", padx=3)

        self.btn_rec_key = ctk.CTkButton(ctrl_row, text="🔴 Record Key", width=110, height=32, fg_color=COLORS["card_bg"], border_width=1, border_color=COLORS["danger"], command=self.toggle_key_capture)
        self.btn_rec_key.pack(side="right")

        self.lbl_seq_preview = ctk.CTkLabel(
            seq_card, text="Sequence is empty. Add steps above or load a preset below.",
            fg_color=COLORS["card_bg"], corner_radius=8, height=64, wraplength=540,
            text_color=COLORS["accent"], font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_seq_preview.pack(fill="x", padx=16, pady=8)

        bot_seq = ctk.CTkFrame(seq_card, fg_color="transparent")
        bot_seq.pack(fill="x", padx=16, pady=6)

        ctk.CTkButton(bot_seq, text="Copy → Alt+Tab → Paste Preset", height=32, fg_color=COLORS["key_special"], command=self.load_copy_switch_paste_preset).pack(side="left", padx=(0, 6))
        ctk.CTkButton(bot_seq, text="Clear Steps", width=90, height=32, fg_color=COLORS["danger"], command=self.clear_macro_steps).pack(side="left")
        ctk.CTkButton(bot_seq, text="Bind Timed Sequence", width=160, height=34, fg_color=COLORS["success"], hover_color="#059669", font=ctk.CTkFont(weight="bold"), command=self.bind_macro_sequence).pack(side="right")

        txt_card = ctk.CTkFrame(wrap, fg_color=COLORS["bg_dark"], corner_radius=12, border_width=1, border_color=COLORS["card_border"])
        txt_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=4)

        ctk.CTkLabel(txt_card, text="📝 Instant Text Snippet Typer", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(txt_card, text="Instantly types out any string (email, command, search phrase, password):", text_color=COLORS["text_muted"], font=ctk.CTkFont(size=11), wraplength=340, justify="left").pack(anchor="w", padx=16, pady=(0, 10))

        self.ent_snippet = ctk.CTkEntry(txt_card, height=38, placeholder_text="Type your text snippet here...")
        self.ent_snippet.pack(fill="x", padx=16, pady=8)

        ctk.CTkButton(
            txt_card, text="Bind Text Snippet", height=38,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(weight="bold"),
            command=self.bind_text_snippet
        ).pack(fill="x", padx=16, pady=8)

    def refresh_macro_preview(self):
        if not self.macro_steps:
            self.lbl_seq_preview.configure(text="Sequence is empty.")
        else:
            self.lbl_seq_preview.configure(text="  →  ".join(self.macro_steps))

    def add_manual_macro_step(self):
        val = self.ent_macro_step.get().strip()
        if not val:
            return
        if not (val.startswith("Key:") or val.startswith("Combo:") or val.startswith("Mouse:")):
            val = f"Combo: {val.lower()}" if "+" in val else f"Key: {val.lower()}"
        self.macro_steps.append(val)
        self.ent_macro_step.delete(0, "end")
        self.refresh_macro_preview()

    def add_wait_step(self):
        ms = self.ent_wait_ms.get().strip()
        if ms.isdigit():
            self.macro_steps.append(f"Wait: {ms}")
            self.refresh_macro_preview()

    def toggle_key_capture(self):
        self.is_recording_keys = not self.is_recording_keys
        if self.is_recording_keys:
            self.btn_rec_key.configure(text="Listening... (Press Key)", fg_color=COLORS["danger"])
            self.bind("<KeyPress>", self._on_recorded_key)
        else:
            self.btn_rec_key.configure(text="🔴 Record Key", fg_color=COLORS["card_bg"])
            self.unbind("<KeyPress>")

    def _on_recorded_key(self, event):
        if not self.is_recording_keys:
            return
        ks = event.keysym.lower()
        key_aliases = {"return": "enter", "escape": "esc", "prior": "page_up", "next": "page_down", "win_l": "cmd", "super_l": "cmd", "control_l": "ctrl", "control_r": "ctrl", "shift_l": "shift", "shift_r": "shift", "alt_l": "alt", "alt_r": "alt"}
        ks = key_aliases.get(ks, ks)
        self.macro_steps.append(f"Key: {ks}")
        self.refresh_macro_preview()
        self.toggle_key_capture()

    def load_copy_switch_paste_preset(self):
        self.macro_steps = ["Combo: ctrl+c", "Wait: 150", "Combo: alt+tab", "Wait: 200", "Combo: ctrl+v", "Wait: 100", "Key: enter"]
        self.refresh_macro_preview()

    def clear_macro_steps(self):
        self.macro_steps.clear()
        self.refresh_macro_preview()

    def bind_macro_sequence(self):
        if self.macro_steps:
            seq = " -> ".join(self.macro_steps)
            self.select_action(f"MacroSeq: {seq}")

    def bind_text_snippet(self):
        txt = self.ent_snippet.get()
        if txt:
            self.select_action(f"Text: {txt}")

    def build_media_system_tab(self):
        tab = self.tabs.tab("Media, Window & System")

        grid_wrap = ctk.CTkFrame(tab, fg_color="transparent")
        grid_wrap.pack(fill="x", padx=12, pady=6)
        grid_wrap.grid_columnconfigure((0, 1, 2, 3), weight=1)

        aud_card = ctk.CTkFrame(grid_wrap, fg_color=COLORS["bg_dark"], corner_radius=10, border_width=1, border_color=COLORS["card_border"])
        aud_card.grid(row=0, column=0, sticky="nsew", padx=5, pady=4)
        ctk.CTkLabel(aud_card, text="🔊 Audio & Media", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(8, 4))
        for lbl, act in [
            ("Volume Up (+)", "Media: Vol Up"),
            ("Volume Down (-)", "Media: Vol Down"),
            ("Mute Audio", "Media: Mute"),
            ("Play / Pause", "Media: Play/Pause"),
            ("Next Track ⏭", "Media: Next Track"),
            ("Prev Track ⏮", "Media: Prev Track")
        ]:
            ctk.CTkButton(aud_card, text=lbl, height=28, fg_color=COLORS["key_special"], hover_color=COLORS["accent"], command=lambda a=act: self.select_action(a)).pack(fill="x", padx=10, pady=2)

        win_card = ctk.CTkFrame(grid_wrap, fg_color=COLORS["bg_dark"], corner_radius=10, border_width=1, border_color=COLORS["card_border"])
        win_card.grid(row=0, column=1, sticky="nsew", padx=5, pady=4)
        ctk.CTkLabel(win_card, text="🪟 Window Manager", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(8, 4))
        for lbl, act in [
            ("Snap Window Left", "System: Snap Left"),
            ("Snap Window Right", "System: Snap Right"),
            ("Maximize Window", "System: Maximize Window"),
            ("Minimize Window", "System: Minimize Window"),
            ("Next Virtual Desktop", "System: Next Desktop"),
            ("Prev Virtual Desktop", "System: Prev Desktop"),
            ("📌 Pin Always-on-Top", "System: Pin Always on Top")
        ]:
            ctk.CTkButton(win_card, text=lbl, height=26, fg_color=COLORS["key_special"], hover_color=COLORS["accent"], command=lambda a=act: self.select_action(a)).pack(fill="x", padx=10, pady=2)

        couch_card = ctk.CTkFrame(grid_wrap, fg_color=COLORS["bg_dark"], corner_radius=10, border_width=1, border_color=COLORS["card_border"])
        couch_card.grid(row=0, column=2, sticky="nsew", padx=5, pady=4)
        ctk.CTkLabel(couch_card, text="🎯 Couch & Monitors", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(8, 4))
        for lbl, act in [
            ("🎡 Hold 8-Way Radial Menu", "System: Radial Wheel"),
            ("🌼 Toggle Daisywheel KB", "System: Daisywheel"),
            ("⭕ Hold Cursor Laser Ring", "System: Laser Ring"),
            ("🔍 Toggle OS Magnifier", "System: Magnifier Toggle"),
            ("🖥 Teleport Next Monitor", "System: Next Monitor"),
            ("🎯 Center Cursor in Window", "System: Center Cursor")
        ]:
            ctk.CTkButton(couch_card, text=lbl, height=28, fg_color=COLORS["key_special"], hover_color=COLORS["accent"], command=lambda a=act: self.select_action(a)).pack(fill="x", padx=10, pady=2)

        sys_card = ctk.CTkFrame(grid_wrap, fg_color=COLORS["bg_dark"], corner_radius=10, border_width=1, border_color=COLORS["card_border"])
        sys_card.grid(row=0, column=3, sticky="nsew", padx=5, pady=4)
        ctk.CTkLabel(sys_card, text="⚙ System & Display", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(8, 4))
        for lbl, act in [
            ("☀ Brightness Up", "System: Brightness Up"),
            ("🔅 Brightness Down", "System: Brightness Down"),
            ("✂ Screenshot (Win+Shift+S)", "System: Screenshot"),
            ("🔒 Lock Workstation", "System: Lock PC"),
            ("🧭 Hold Shortcut HUD", "System: HUD")
        ]:
            ctk.CTkButton(sys_card, text=lbl, height=28, fg_color=COLORS["key_special"], hover_color=COLORS["accent"], command=lambda a=act: self.select_action(a)).pack(fill="x", padx=10, pady=2)

        launcher_card = ctk.CTkFrame(tab, fg_color=COLORS["bg_dark"], corner_radius=10, border_width=1, border_color=COLORS["card_border"])
        launcher_card.pack(fill="x", padx=17, pady=(6, 4))

        ctk.CTkLabel(launcher_card, text="🚀 Launch Custom Application, Script, or URL (.exe, .bat, https://):", text_color=COLORS["text_muted"], font=ctk.CTkFont(size=12)).pack(anchor="w", padx=14, pady=(6, 2))
        l_row = ctk.CTkFrame(launcher_card, fg_color="transparent")
        l_row.pack(fill="x", padx=14, pady=(0, 8))

        self.ent_app_path = ctk.CTkEntry(l_row, placeholder_text="C:\\Windows\\System32\\calc.exe or https://youtube.com", height=32)
        self.ent_app_path.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(l_row, text="Browse...", width=85, height=32, fg_color=COLORS["key_special"], command=self.browse_executable).pack(side="left", padx=4)
        ctk.CTkButton(l_row, text="Bind Launcher", width=115, height=32, fg_color=COLORS["success"], hover_color="#059669", command=self.bind_custom_launcher).pack(side="left", padx=(4, 0))

    def browse_executable(self):
        path = filedialog.askopenfilename(title="Select Application or Script")
        if path:
            self.ent_app_path.delete(0, "end")
            self.ent_app_path.insert(0, path)

    def bind_custom_launcher(self):
        val = self.ent_app_path.get().strip()
        if val:
            self.select_action(f"Launch: {val}")

    def build_combo_tab(self):
        tab = self.tabs.tab("Shortcuts & Macros")
        ctk.CTkLabel(tab, text="Quick OS & App Shortcuts", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5))

        presets_frame = ctk.CTkFrame(tab, fg_color="transparent")
        presets_frame.pack(pady=5)

        presets = [
            ("Copy (Ctrl+C)", "Combo: ctrl+c"),
            ("Paste (Ctrl+V)", "Combo: ctrl+v"),
            ("Cut (Ctrl+X)", "Combo: ctrl+x"),
            ("Undo (Ctrl+Z)", "Combo: ctrl+z"),
            ("Save (Ctrl+S)", "Combo: ctrl+s"),
            ("Select All (Ctrl+A)", "Combo: ctrl+a"),
            ("Find (Ctrl+F)", "Combo: ctrl+f"),
            ("New Tab (Ctrl+T)", "Combo: ctrl+t"),
            ("Close Tab (Ctrl+W)", "Combo: ctrl+w"),
            ("Reopen Tab (Ctrl+Shift+T)", "Combo: ctrl+shift+t"),
            ("Switch App (Alt+Tab)", "Combo: alt+tab"),
            ("Close App (Alt+F4)", "Combo: alt+f4"),
            ("Show Desktop (Win+D)", "Combo: cmd+d"),
            ("Task View (Win+Tab)", "Combo: cmd+tab"),
            ("Explorer (Win+E)", "Combo: cmd+e"),
            ("Task Manager (Ctrl+Shift+Esc)", "Combo: ctrl+shift+esc")
        ]

        for idx, (label, action) in enumerate(presets):
            r, c = divmod(idx, 4)
            ctk.CTkButton(
                presets_frame, text=label, width=210, height=36,
                fg_color=COLORS["key_special"], hover_color=COLORS["accent"],
                command=lambda a=action: self.select_action(a)
            ).grid(row=r, column=c, padx=6, pady=6)

        custom_card = ctk.CTkFrame(tab, fg_color=COLORS["bg_dark"], corner_radius=10, border_width=1, border_color=COLORS["card_border"])
        custom_card.pack(pady=16, padx=40, fill="x")

        ctk.CTkLabel(
            custom_card,
            text="Custom Simultaneous Shortcut (lowercase keys joined by '+', e.g. ctrl+alt+delete or shift+f10):",
            text_color=COLORS["text_muted"]
        ).pack(pady=(10, 5))

        entry_row = ctk.CTkFrame(custom_card, fg_color="transparent")
        entry_row.pack(pady=(0, 12))

        self.ent_custom = ctk.CTkEntry(entry_row, width=320, height=36, placeholder_text="e.g. ctrl+shift+m")
        self.ent_custom.pack(side="left", padx=8)
        self.ent_custom.bind("<Return>", lambda e: self.set_custom_combo())

        ctk.CTkButton(
            entry_row, text="Bind Shortcut", height=36,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            command=self.set_custom_combo
        ).pack(side="left", padx=8)

    def set_custom_combo(self):
        val = self.ent_custom.get().strip().lower()
        if val:
            self.select_action(f"Combo: {val}")

    def build_mouse_tab(self):
        tab = self.tabs.tab("Mouse")
        container = ctk.CTkFrame(tab, fg_color="transparent")
        container.pack(expand=True)

        mouse_body = ctk.CTkFrame(container, width=320, height=310, corner_radius=45, fg_color=COLORS["bg_dark"], border_width=2, border_color=COLORS["card_border"])
        mouse_body.pack(side="left", padx=25, pady=10)
        mouse_body.pack_propagate(False)
        mouse_body.grid_columnconfigure((0, 2), weight=1)
        mouse_body.grid_columnconfigure(1, weight=0)
        mouse_body.grid_rowconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            mouse_body, text="Left Click", font=ctk.CTkFont(size=15, weight="bold"),
            corner_radius=24, fg_color=COLORS["key_special"], hover_color=COLORS["accent"],
            command=lambda: self.select_action("Mouse: Left")
        ).grid(row=0, column=0, rowspan=3, sticky="nsew", padx=(16, 6), pady=16)

        ctk.CTkButton(
            mouse_body, text="▲\nScroll Up", width=68, height=70, corner_radius=14,
            fg_color=COLORS["card_bg"], hover_color=COLORS["accent"],
            command=lambda: self.select_action("Mouse: Scroll Up")
        ).grid(row=0, column=1, sticky="s", pady=(18, 4))

        ctk.CTkButton(
            mouse_body, text="Middle\nClick", width=68, height=64, corner_radius=18,
            fg_color="#374151", hover_color=COLORS["accent"],
            command=lambda: self.select_action("Mouse: Middle")
        ).grid(row=1, column=1, pady=4)

        ctk.CTkButton(
            mouse_body, text="Scroll Dn\n▼", width=68, height=70, corner_radius=14,
            fg_color=COLORS["card_bg"], hover_color=COLORS["accent"],
            command=lambda: self.select_action("Mouse: Scroll Down")
        ).grid(row=2, column=1, sticky="n", pady=(4, 18))

        ctk.CTkButton(
            mouse_body, text="Right Click", font=ctk.CTkFont(size=15, weight="bold"),
            corner_radius=24, fg_color=COLORS["key_special"], hover_color=COLORS["accent"],
            command=lambda: self.select_action("Mouse: Right")
        ).grid(row=0, column=2, rowspan=3, sticky="nsew", padx=(6, 16), pady=16)

        h_scroll = ctk.CTkFrame(container, fg_color=COLORS["bg_dark"], corner_radius=16, border_width=1, border_color=COLORS["card_border"])
        h_scroll.pack(side="left", padx=25, pady=10, ipadx=20, ipady=20)

        ctk.CTkLabel(h_scroll, text="Horizontal Wheel Tilt", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(5, 14))
        btn_row = ctk.CTkFrame(h_scroll, fg_color="transparent")
        btn_row.pack(padx=10, pady=5)

        ctk.CTkButton(
            btn_row, text="◄ Scroll Left", width=135, height=44,
            font=ctk.CTkFont(weight="bold"),
            fg_color=COLORS["key_special"], hover_color=COLORS["accent"],
            command=lambda: self.select_action("Mouse: Scroll Left")
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_row, text="Scroll Right ►", width=135, height=44,
            font=ctk.CTkFont(weight="bold"),
            fg_color=COLORS["key_special"], hover_color=COLORS["accent"],
            command=lambda: self.select_action("Mouse: Scroll Right")
        ).pack(side="left", padx=6)

    def build_keyboard_tab(self):
        tab = self.tabs.tab("Keyboard")
        kb_wrapper = ctk.CTkFrame(tab, fg_color="transparent")
        kb_wrapper.pack(expand=True, pady=10)

        main_kb = ctk.CTkFrame(kb_wrapper, fg_color=COLORS["bg_dark"], corner_radius=10, padx=8, pady=8)
        main_kb.pack(side="left", padx=6)
        nav_kb = ctk.CTkFrame(kb_wrapper, fg_color=COLORS["bg_dark"], corner_radius=10, padx=8, pady=8)
        nav_kb.pack(side="left", padx=6, fill="y")
        numpad_kb = ctk.CTkFrame(kb_wrapper, fg_color=COLORS["bg_dark"], corner_radius=10, padx=8, pady=8)
        numpad_kb.pack(side="left", padx=6, fill="y")

        main_rows = [
            [("esc", "esc"), ("f1", "f1"), ("f2", "f2"), ("f3", "f3"), ("f4", "f4"), ("f5", "f5"), ("f6", "f6"), ("f7", "f7"), ("f8", "f8"), ("f9", "f9"), ("f10", "f10"), ("f11", "f11"), ("f12", "f12")],
            [("`", "`"), ("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5"), ("6", "6"), ("7", "7"), ("8", "8"), ("9", "9"), ("0", "0"), ("-", "-"), ("=", "="), ("bksp", "backspace", 68)],
            [("tab", "tab", 52), ("q", "q"), ("w", "w"), ("e", "e"), ("r", "r"), ("t", "t"), ("y", "y"), ("u", "u"), ("i", "i"), ("o", "o"), ("p", "p"), ("[", "["), ("]", "]"), ("\\", "\\", 48)],
            [("caps", "caps_lock", 62), ("a", "a"), ("s", "s"), ("d", "d"), ("f", "f"), ("g", "g"), ("h", "h"), ("j", "j"), ("k", "k"), ("l", "l"), (";", ";"), ("'", "'"), ("enter", "enter", 72)],
            [("shift", "shift", 82), ("z", "z"), ("x", "x"), ("c", "c"), ("v", "v"), ("b", "b"), ("n", "n"), ("m", "m"), (",", ","), (".", "."), ("/", "/"), ("shift", "shift", 82)],
            [("ctrl", "ctrl", 50), ("win", "cmd", 45), ("alt", "alt", 45), ("space", "space", 215), ("alt", "alt", 45), ("win", "cmd", 45), ("ctrl", "ctrl", 50)]
        ]
        for row in main_rows:
            r_frame = ctk.CTkFrame(main_kb, fg_color="transparent")
            r_frame.pack(pady=2, anchor="w")
            for key in row:
                w = key[2] if len(key) == 3 else 36
                is_mod = len(key[0]) > 1 and key[0] not in ["-", "=", "[", "]", "\\", ";", "'", ",", ".", "/", "`"]
                c = COLORS["key_special"] if is_mod else COLORS["key_std"]
                ctk.CTkButton(
                    r_frame, text=key[0].upper(), width=w, height=36,
                    fg_color=c, hover_color=COLORS["accent"],
                    command=lambda a=f"Key: {key[1]}": self.select_action(a)
                ).pack(side="left", padx=2)

        nav_rows = [
            [("prt", "print_screen"), ("scr", "scroll_lock"), ("pau", "pause")],
            [("ins", "insert"), ("hom", "home"), ("pup", "page_up")],
            [("del", "delete"), ("end", "end"), ("pdn", "page_down")]
        ]
        for row in nav_rows:
            r_frame = ctk.CTkFrame(nav_kb, fg_color="transparent")
            r_frame.pack(pady=2)
            for key in row:
                ctk.CTkButton(
                    r_frame, text=key[0].upper(), width=38, height=36,
                    fg_color=COLORS["key_special"], hover_color=COLORS["accent"],
                    command=lambda a=f"Key: {key[1]}": self.select_action(a)
                ).pack(side="left", padx=2)

        arrow_frame = ctk.CTkFrame(nav_kb, fg_color="transparent")
        arrow_frame.pack(side="bottom", pady=4)
        ctk.CTkButton(arrow_frame, text="▲", width=38, height=36, fg_color=COLORS["accent"], command=lambda: self.select_action("Key: up")).grid(row=0, column=1, padx=2, pady=2)
        ctk.CTkButton(arrow_frame, text="◄", width=38, height=36, fg_color=COLORS["accent"], command=lambda: self.select_action("Key: left")).grid(row=1, column=0, padx=2, pady=2)
        ctk.CTkButton(arrow_frame, text="▼", width=38, height=36, fg_color=COLORS["accent"], command=lambda: self.select_action("Key: down")).grid(row=1, column=1, padx=2, pady=2)
        ctk.CTkButton(arrow_frame, text="►", width=38, height=36, fg_color=COLORS["accent"], command=lambda: self.select_action("Key: right")).grid(row=1, column=2, padx=2, pady=2)

        num_rows = [
            [("num", "num_lock"), ("/", "/"), ("*", "*"), ("-", "-")],
            [("7", "7"), ("8", "8"), ("9", "9"), ("+", "+")],
            [("4", "4"), ("5", "5"), ("6", "6"), ("ent", "enter")],
            [("1", "1"), ("2", "2"), ("3", "3"), (".", ".")],
            [("0", "0", 78)]
        ]
        for row in num_rows:
            r_frame = ctk.CTkFrame(numpad_kb, fg_color="transparent")
            r_frame.pack(pady=2, anchor="w")
            for key in row:
                w = key[2] if len(key) == 3 else 37
                c = COLORS["key_special"] if len(key[0]) > 1 else COLORS["key_std"]
                ctk.CTkButton(
                    r_frame, text=key[0].upper(), width=w, height=36,
                    fg_color=c, hover_color=COLORS["accent"],
                    command=lambda a=f"Key: {key[1]}": self.select_action(a)
                ).pack(side="left", padx=2)


# --- RADIAL WHEEL 8-SLOT EDITOR DIALOG ---
class RadialWheelEditor(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Configure 8-Sector Radial Pie Menu")
        self.geometry("560x480")
        self.configure(fg_color=COLORS["bg_dark"])
        self.after(50, self.grab_set)

        ctk.CTkLabel(self, text="8-Way Radial Wheel Slots", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(12, 4))
        ctk.CTkLabel(self, text="Bind any button to '🎡 Hold 8-Way Radial Menu' (in Media, Window & System tab) to use.", text_color=COLORS["text_muted"], font=ctk.CTkFont(size=11)).pack(pady=(0, 8))

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS["card_bg"])
        self.scroll.pack(fill="both", expand=True, padx=16, pady=8)

        self.entries = []
        self.act_btns = []
        compass = ["N (Up)", "NE", "E (Right)", "SE", "S (Down)", "SW", "W (Left)", "NW"]
        slots = APP_STATE.get("radial_slots", DEFAULT_RADIAL_SLOTS)

        for i in range(8):
            row = ctk.CTkFrame(self.scroll, fg_color=COLORS["bg_dark"], corner_radius=8)
            row.pack(fill="x", padx=6, pady=4)
            ctk.CTkLabel(row, text=compass[i], width=80, anchor="w", font=ctk.CTkFont(weight="bold"), text_color=COLORS["warning"]).pack(side="left", padx=10, pady=8)

            ent = ctk.CTkEntry(row, width=130, height=28)
            ent.insert(0, slots[i].get("label", f"Slot {i+1}"))
            ent.bind("<KeyRelease>", lambda e, idx=i: self.update_slot_label(idx))
            ent.pack(side="left", padx=6)
            self.entries.append(ent)

            act_str = slots[i].get("action", "None")
            btn = ctk.CTkButton(
                row, text=act_str[:26], height=28, fg_color=COLORS["key_special"], hover_color=COLORS["accent"],
                command=lambda idx=i: VisualPicker(self, idx, False, self.update_slot_action)
            )
            btn.pack(side="right", padx=10, pady=6)
            self.act_btns.append(btn)

    def update_slot_label(self, idx):
        APP_STATE["radial_slots"][idx]["label"] = self.entries[idx].get().strip()
        save_config()

    def update_slot_action(self, idx, new_action, _):
        APP_STATE["radial_slots"][idx]["action"] = new_action
        self.act_btns[idx].configure(text=new_action[:26])
        save_config()


# --- MAIN WIDESCREEN DASHBOARD ---
class ModernControllerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        load_config()

        self.title(f"JeetPad v{APP_VERSION} — Pro Controller Suite")
        self.geometry("1120x740")
        self.minsize(1000, 660)
        self.configure(fg_color=COLORS["bg_dark"])
        self.protocol("WM_DELETE_WINDOW", self.force_quit)

        self._save_job = None
        self.tray_icon = None
        self.mapping_badges = {}
        self.mode_buttons = {}
        self.mapping_rows = {}
        self.main_containers = []
        self.current_remap_mode = "Standard"
        self.last_rendered_profile = None
        self.ui_mouse_ref = MouseController()
        self._checking_updates = False
        self._last_update_res = None

        try:
            if platform.system() == "Windows":
                self.iconbitmap(resource_path("icon.ico"))
            else:
                icon_img = tk.PhotoImage(file=resource_path("icon.png"))
                self.wm_iconphoto(True, icon_img)
        except Exception:
            pass

        self.hud_overlay = RadialHUDOverlay(self)
        self.radial_overlay = RadialWheelOverlay(self)
        self.daisywheel_overlay = DaisywheelOverlay(self)
        self.laser_overlay = CursorLocatorOverlay(self)
        self.build_layout()
        self.update_ui_loop()

        # Check for updates automatically every time on startup
        if APP_STATE.get("check_updates_on_startup", True):
            self.after(1200, lambda: self.trigger_update_check(manual=False))

    def schedule_save(self):
        if self._save_job is not None:
            self.after_cancel(self._save_job)
        self._save_job = self.after(400, save_config)

    # --- LIVE COLOR THEME SWITCHER ---
    def change_color_theme(self, new_theme):
        if new_theme not in THEME_PRESETS:
            return
        with STATE_LOCK:
            APP_STATE["color_theme"] = new_theme
            apply_theme_palette(new_theme)
        save_config()

        # Rebuild main dashboard panels cleanly with the new palette
        self.configure(fg_color=COLORS["bg_dark"])
        for w in self.main_containers:
            try:
                w.destroy()
            except Exception:
                pass
        self.main_containers.clear()
        self.build_layout()

        # Update Overlays
        self.hud_overlay.apply_theme()
        self.radial_overlay.apply_theme()
        self.daisywheel_overlay.apply_theme()
        self.laser_overlay.draw_rings()

    # --- UPDATE CHECKER METHODS ---
    def trigger_update_check(self, manual=True):
        if self._checking_updates:
            return
        self._checking_updates = True
        if hasattr(self, "btn_check_update"):
            self.btn_check_update.configure(text="Checking...", state="disabled")

        repo_slug = APP_STATE.get("github_repo", DEFAULT_GITHUB_REPO).strip() or DEFAULT_GITHUB_REPO

        def _worker():
            res = fetch_latest_github_release(repo_slug)
            self.after(0, lambda: self._on_update_check_done(res, manual))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_update_check_done(self, res, manual):
        self._checking_updates = False
        self._last_update_res = res
        status = res.get("status", "error")
        latest_ver = res.get("latest_ver", APP_VERSION)

        if hasattr(self, "btn_check_update"):
            if status == "update_available":
                self.btn_check_update.configure(
                    text=f"⬇ v{latest_ver} Ready!",
                    fg_color=COLORS["success"],
                    hover_color="#059669",
                    state="normal"
                )
            else:
                self.btn_check_update.configure(
                    text="🔄 Check Update",
                    fg_color=COLORS["key_special"],
                    hover_color=COLORS["accent"],
                    state="normal"
                )

        if status == "update_available" or manual:
            UpdateDialog(self, res)

    def build_layout(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- TOP HEADER ---
        header = ctk.CTkFrame(self, fg_color=COLORS["card_bg"], corner_radius=14, border_width=1, border_color=COLORS["card_border"])
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(14, 6))
        self.main_containers.append(header)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", padx=12, pady=10)

        self.status_dot = ctk.CTkLabel(title_box, text="●", font=ctk.CTkFont(size=22), text_color=COLORS["success"])
        self.status_dot.pack(side="left", padx=(0, 8))

        title_stack = ctk.CTkFrame(title_box, fg_color="transparent")
        title_stack.pack(side="left")
        self.lbl_title = ctk.CTkLabel(title_stack, text=f"JeetPad Active  (v{APP_VERSION})", font=ctk.CTkFont(size=16, weight="bold"), anchor="w")
        self.lbl_title.pack(anchor="w")
        self.lbl_hold_hint = ctk.CTkLabel(
            title_stack,
            text=f"Hold [{BTN_NAMES.get(APP_STATE['toggle_button'], 'Start')}] 3s to toggle",
            font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"], anchor="w"
        )
        self.lbl_hold_hint.pack(anchor="w")

        # Profile Selector Bar
        prof_bar = ctk.CTkFrame(header, fg_color=COLORS["bg_dark"], corner_radius=10, border_width=1, border_color=COLORS["card_border"])
        prof_bar.pack(side="left", padx=8, pady=8, ipadx=4, ipady=3)

        ctk.CTkLabel(prof_bar, text="Profile:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text_muted"]).pack(side="left", padx=(8, 4))
        self.opt_profile = ctk.CTkOptionMenu(
            prof_bar, values=list(APP_STATE["profiles"].keys()), width=110, height=28,
            fg_color=COLORS["card_bg"], button_color=COLORS["accent"], button_hover_color=COLORS["accent_hover"],
            command=self.change_profile
        )
        self.opt_profile.set(APP_STATE["active_profile"])
        self.opt_profile.pack(side="left", padx=3)

        ctk.CTkButton(prof_bar, text="Import", width=54, height=26, fg_color=COLORS["key_special"], hover_color=COLORS["accent"], command=self.import_profile).pack(side="left", padx=2)
        ctk.CTkButton(prof_bar, text="Export", width=54, height=26, fg_color=COLORS["key_special"], hover_color=COLORS["accent"], command=self.export_profile).pack(side="left", padx=(2, 6))

        # Color Theme Selector Bar
        theme_bar = ctk.CTkFrame(header, fg_color=COLORS["bg_dark"], corner_radius=10, border_width=1, border_color=COLORS["card_border"])
        theme_bar.pack(side="left", padx=6, pady=8, ipadx=4, ipady=3)

        ctk.CTkLabel(theme_bar, text="🎨 Theme:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text_muted"]).pack(side="left", padx=(8, 4))
        self.opt_theme = ctk.CTkOptionMenu(
            theme_bar, values=list(THEME_PRESETS.keys()), width=128, height=28,
            fg_color=COLORS["card_bg"], button_color=COLORS["accent"], button_hover_color=COLORS["accent_hover"],
            command=self.change_color_theme
        )
        self.opt_theme.set(APP_STATE.get("color_theme", "Ocean Blue"))
        self.opt_theme.pack(side="left", padx=(2, 6))

        right_controls = ctk.CTkFrame(header, fg_color="transparent")
        right_controls.pack(side="right", padx=12, pady=10)

        self.btn_minimize = ctk.CTkButton(
            right_controls, text="Tray", width=58, height=32,
            fg_color=COLORS["key_special"], hover_color=COLORS["accent_hover"],
            command=self.hide_window
        )
        self.btn_minimize.pack(side="right", padx=(6, 0))

        upd_txt = "🔄 Check Update"
        upd_col = COLORS["key_special"]
        if self._last_update_res and self._last_update_res.get("status") == "update_available":
            upd_txt = f"⬇ v{self._last_update_res.get('latest_ver')} Ready!"
            upd_col = COLORS["success"]

        self.btn_check_update = ctk.CTkButton(
            right_controls, text=upd_txt, width=116, height=32,
            fg_color=upd_col, hover_color=COLORS["accent"],
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.trigger_update_check(manual=True)
        )
        self.btn_check_update.pack(side="right", padx=5)

        self.switch_master = ctk.CTkSwitch(
            right_controls, text="Master",
            font=ctk.CTkFont(size=13, weight="bold"),
            progress_color=COLORS["success"], width=78,
            command=self.toggle_master
        )
        if APP_STATE["enabled"]:
            self.switch_master.select()
        self.switch_master.pack(side="right", padx=5)

        self.lbl_shift_indicator = ctk.CTkLabel(
            right_controls, text="SHIFT IDLE",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=COLORS["card_border"], text_color=COLORS["text_muted"],
            corner_radius=6, width=82, height=26
        )
        self.lbl_shift_indicator.pack(side="right", padx=5)

        # --- LEFT SCROLLABLE SIDEBAR ---
        sidebar = ctk.CTkScrollableFrame(self, width=365, fg_color="transparent")
        sidebar.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=(6, 14))
        self.main_containers.append(sidebar)

        # Card 1: Hardware & Auto-Switching Rules
        dev_card = ctk.CTkFrame(sidebar, fg_color=COLORS["card_bg"], corner_radius=12, border_width=1, border_color=COLORS["card_border"])
        dev_card.pack(fill="x", pady=(0, 10), padx=4)

        ctk.CTkLabel(dev_card, text="CONTROLLER & AUTO-SWITCHING", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["accent"]).pack(anchor="w", padx=14, pady=(10, 4))

        self.opt_controller = ctk.CTkOptionMenu(
            dev_card, values=APP_STATE["available_controllers"],
            fg_color=COLORS["bg_dark"], button_color=COLORS["accent"], button_hover_color=COLORS["accent_hover"],
            command=self.change_priority
        )
        self.opt_controller.pack(fill="x", padx=14, pady=(0, 8))

        scan_row = ctk.CTkFrame(dev_card, fg_color="transparent")
        scan_row.pack(fill="x", padx=14, pady=(0, 8))

        self.chk_autoscan = ctk.CTkSwitch(scan_row, text="Auto-Scan", progress_color=COLORS["accent"], command=self.toggle_autoscan, width=90)
        if APP_STATE["auto_scan"]:
            self.chk_autoscan.select()
        self.chk_autoscan.pack(side="left")

        self.ent_interval = ctk.CTkEntry(scan_row, width=38, height=26, justify="center")
        self.ent_interval.insert(0, str(int(APP_STATE["scan_interval"])))
        self.ent_interval.bind("<KeyRelease>", self.update_interval)
        self.ent_interval.pack(side="left", padx=(6, 2))
        ctk.CTkLabel(scan_row, text="s", text_color=COLORS["text_muted"]).pack(side="left")

        ctk.CTkButton(scan_row, text="Rescan", width=65, height=26, fg_color=COLORS["key_special"], hover_color=COLORS["accent"], command=self.request_rescan).pack(side="right")

        ctk.CTkLabel(dev_card, text="Profile App Match Keywords (comma-separated):", font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"]).pack(anchor="w", padx=14, pady=(4, 2))
        self.ent_app_rules = ctk.CTkEntry(dev_card, height=28, placeholder_text="e.g. vlc, spotify, chrome")
        self.ent_app_rules.insert(0, get_current_profile().get("app_rules", ""))
        self.ent_app_rules.bind("<KeyRelease>", self.update_app_rules)
        self.ent_app_rules.pack(fill="x", padx=14, pady=(0, 6))

        self.chk_autoswitch = ctk.CTkSwitch(dev_card, text="Auto-Switch Profile by Active Window", progress_color=COLORS["accent"], command=self.toggle_autoswitch)
        if APP_STATE["auto_switch_profiles"]:
            self.chk_autoswitch.select()
        self.chk_autoswitch.pack(anchor="w", padx=14, pady=3)

        self.chk_gamepause = ctk.CTkSwitch(dev_card, text="Auto-Pause in Fullscreen Games", progress_color=COLORS["accent"], command=self.toggle_gamepause)
        if APP_STATE["auto_pause_fullscreen"]:
            self.chk_gamepause.select()
        self.chk_gamepause.pack(anchor="w", padx=14, pady=(3, 10))

        # Card 2: Precision Cursor, Deadzone & 2D Stick Visualizer
        sens_card = ctk.CTkFrame(sidebar, fg_color=COLORS["card_bg"], corner_radius=12, border_width=1, border_color=COLORS["card_border"])
        sens_card.pack(fill="x", pady=(0, 10), padx=4)

        ctk.CTkLabel(sens_card, text="PRECISION CURSOR & DEADZONE", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["accent"]).pack(anchor="w", padx=14, pady=(10, 4))

        vis_row = ctk.CTkFrame(sens_card, fg_color="transparent")
        vis_row.pack(fill="x", padx=14, pady=4)

        self.stick_canvas = tk.Canvas(vis_row, width=96, height=96, bg=COLORS["bg_dark"], highlightthickness=1, highlightbackground=COLORS["card_border"])
        self.stick_canvas.pack(side="left", padx=(0, 12))

        vis_info = ctk.CTkFrame(vis_row, fg_color="transparent")
        vis_info.pack(side="left", fill="both", expand=True)

        self.lbl_speed_scale = ctk.CTkLabel(vis_info, text="Speed Scale: 1.00x", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["success"], anchor="w")
        self.lbl_speed_scale.pack(anchor="w", pady=(2, 4))

        ctk.CTkLabel(vis_info, text="LT Sniper (30%) / RT Boost (200%)", font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"], anchor="w").pack(anchor="w")
        self.bar_lt = ctk.CTkProgressBar(vis_info, height=8, progress_color=COLORS["warning"])
        self.bar_lt.set(0)
        self.bar_lt.pack(fill="x", pady=(4, 3))

        self.bar_rt = ctk.CTkProgressBar(vis_info, height=8, progress_color=COLORS["accent"])
        self.bar_rt.set(0)
        self.bar_rt.pack(fill="x", pady=(0, 4))

        self.chk_trig_prec = ctk.CTkSwitch(vis_info, text="Analog Trigger Speed", progress_color=COLORS["accent"], command=self.toggle_trig_precision)
        if APP_STATE["trigger_Precision"]:
            self.chk_trig_prec.select()
        self.chk_trig_prec.pack(anchor="w")

        m_row = ctk.CTkFrame(sens_card, fg_color="transparent")
        m_row.pack(fill="x", padx=14, pady=(6, 0))
        ctk.CTkLabel(m_row, text="Cursor Speed").pack(side="left")
        self.lbl_mouse_val = ctk.CTkLabel(m_row, text=f"{APP_STATE['mouse_speed']:.0f}", text_color=COLORS["accent"], font=ctk.CTkFont(weight="bold"))
        self.lbl_mouse_val.pack(side="right")
        self.mouse_slider = ctk.CTkSlider(sens_card, from_=2, to=40, button_color=COLORS["accent"], progress_color=COLORS["accent"], command=self.update_mouse)
        self.mouse_slider.set(APP_STATE["mouse_speed"])
        self.mouse_slider.pack(fill="x", padx=14, pady=(2, 6))

        dz_row = ctk.CTkFrame(sens_card, fg_color="transparent")
        dz_row.pack(fill="x", padx=14)
        ctk.CTkLabel(dz_row, text="Stick Deadzone").pack(side="left")
        self.lbl_dz_val = ctk.CTkLabel(dz_row, text=f"{int(APP_STATE['deadzone']*100)}%", text_color=COLORS["warning"], font=ctk.CTkFont(weight="bold"))
        self.lbl_dz_val.pack(side="right")
        self.dz_slider = ctk.CTkSlider(sens_card, from_=0.05, to=0.35, button_color=COLORS["accent"], progress_color=COLORS["accent"], command=self.update_deadzone)
        self.dz_slider.set(APP_STATE["deadzone"])
        self.dz_slider.pack(fill="x", padx=14, pady=(2, 6))

        s_row = ctk.CTkFrame(sens_card, fg_color="transparent")
        s_row.pack(fill="x", padx=14)
        ctk.CTkLabel(s_row, text="Scroll Speed").pack(side="left")
        self.lbl_scroll_val = ctk.CTkLabel(s_row, text=f"{APP_STATE['scroll_speed']:.1f}x", text_color=COLORS["accent"], font=ctk.CTkFont(weight="bold"))
        self.lbl_scroll_val.pack(side="right")
        self.scroll_slider = ctk.CTkSlider(sens_card, from_=0.2, to=5.0, button_color=COLORS["accent"], progress_color=COLORS["accent"], command=self.update_scroll)
        self.scroll_slider.set(APP_STATE["scroll_speed"])
        self.scroll_slider.pack(fill="x", padx=14, pady=(2, 10))

        # Card 3: Modifiers, Turbo Rate & Startup / Update Settings
        pref_card = ctk.CTkFrame(sidebar, fg_color=COLORS["card_bg"], corner_radius=12, border_width=1, border_color=COLORS["card_border"])
        pref_card.pack(fill="x", padx=4, pady=(0, 10))

        ctk.CTkLabel(pref_card, text="TURBO, MODIFIERS & UPDATES", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["accent"]).pack(anchor="w", padx=14, pady=(10, 6))

        t_row = ctk.CTkFrame(pref_card, fg_color="transparent")
        t_row.pack(fill="x", padx=14)
        ctk.CTkLabel(t_row, text="⚡ Turbo Rapid-Fire Rate").pack(side="left")
        self.lbl_turbo_val = ctk.CTkLabel(t_row, text=f"{APP_STATE['turbo_rate']:.0f} CPS", text_color=COLORS["warning"], font=ctk.CTkFont(weight="bold"))
        self.lbl_turbo_val.pack(side="right")
        self.turbo_slider = ctk.CTkSlider(pref_card, from_=5, to=25, button_color=COLORS["accent"], progress_color=COLORS["accent"], command=self.update_turbo_rate)
        self.turbo_slider.set(APP_STATE["turbo_rate"])
        self.turbo_slider.pack(fill="x", padx=14, pady=(2, 8))

        grid_f = ctk.CTkFrame(pref_card, fg_color="transparent")
        grid_f.pack(fill="x", padx=14)
        grid_f.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(grid_f, text="Hold Toggle Btn:").grid(row=0, column=0, sticky="w", pady=4)
        self.opt_toggle_btn = ctk.CTkOptionMenu(grid_f, values=list(BTN_NAMES.values()), width=140, fg_color=COLORS["bg_dark"], button_color=COLORS["accent"], button_hover_color=COLORS["accent_hover"], command=self.change_toggle_btn)
        self.opt_toggle_btn.set(BTN_NAMES.get(APP_STATE["toggle_button"], "Start / Menu"))
        self.opt_toggle_btn.grid(row=0, column=1, sticky="e", pady=4)

        ctk.CTkLabel(grid_f, text="Combo Shift Key:").grid(row=1, column=0, sticky="w", pady=4)
        self.opt_combo_btn = ctk.CTkOptionMenu(grid_f, values=["None", "LT", "RT", "LB", "RB"], width=140, fg_color=COLORS["bg_dark"], button_color=COLORS["accent"], button_hover_color=COLORS["accent_hover"], command=self.change_combo_mod)
        self.opt_combo_btn.set(APP_STATE.get("combo_modifier", "LB"))
        self.opt_combo_btn.grid(row=1, column=1, sticky="e", pady=4)

        self.chk_swap = ctk.CTkSwitch(pref_card, text="Swap Left & Right Sticks", progress_color=COLORS["accent"], command=self.toggle_swap)
        if APP_STATE["swap_sticks"]:
            self.chk_swap.select()
        self.chk_swap.pack(anchor="w", padx=14, pady=(8, 4))

        self.chk_startup = ctk.CTkSwitch(pref_card, text="Launch on System Startup", progress_color=COLORS["accent"], command=self.toggle_autostart)
        if is_autostart_enabled():
            self.chk_startup.select()
        self.chk_startup.pack(anchor="w", padx=14, pady=4)

        self.chk_update_startup = ctk.CTkSwitch(pref_card, text="Auto-Check Updates on Startup", progress_color=COLORS["accent"], command=self.toggle_update_on_startup)
        if APP_STATE.get("check_updates_on_startup", True):
            self.chk_update_startup.select()
        self.chk_update_startup.pack(anchor="w", padx=14, pady=(4, 12))

        # Card 4: Optional Couch & Power Extensions (All Disabled by Default)
        ext_card = ctk.CTkFrame(sidebar, fg_color=COLORS["card_bg"], corner_radius=12, border_width=1, border_color=COLORS["card_border"])
        ext_card.pack(fill="x", padx=4, pady=(0, 8))

        ctk.CTkLabel(ext_card, text="COUCH & POWER EXTENSIONS (OFF BY DEFAULT)", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["accent"]).pack(anchor="w", padx=14, pady=(10, 6))

        self.chk_hud = ctk.CTkSwitch(ext_card, text="On-Screen Shortcut HUD Overlay", progress_color=COLORS["accent"], command=self.toggle_hud)
        if APP_STATE.get("hud_enabled", False):
            self.chk_hud.select()
        self.chk_hud.pack(anchor="w", padx=14, pady=4)

        rad_row = ctk.CTkFrame(ext_card, fg_color="transparent")
        rad_row.pack(fill="x", padx=14, pady=4)
        self.chk_radial = ctk.CTkSwitch(rad_row, text="8-Way Radial Pie Wheel", progress_color=COLORS["accent"], command=self.toggle_radial_wheel)
        if APP_STATE.get("radial_wheel_enabled", False):
            self.chk_radial.select()
        self.chk_radial.pack(side="left")
        ctk.CTkButton(rad_row, text="Edit Slots", width=72, height=24, fg_color=COLORS["key_special"], hover_color=COLORS["accent"], command=lambda: RadialWheelEditor(self)).pack(side="right")

        self.chk_daisy = ctk.CTkSwitch(ext_card, text="Daisywheel Thumbstick Typing", progress_color=COLORS["accent"], command=self.toggle_daisywheel)
        if APP_STATE.get("daisywheel_enabled", False):
            self.chk_daisy.select()
        self.chk_daisy.pack(anchor="w", padx=14, pady=4)

        self.chk_edgewrap = ctk.CTkSwitch(ext_card, text="Screen-Edge Cursor Wrap (Pac-Man)", progress_color=COLORS["accent"], command=self.toggle_edge_wrap)
        if APP_STATE.get("edge_wrap_enabled", False):
            self.chk_edgewrap.select()
        self.chk_edgewrap.pack(anchor="w", padx=14, pady=4)

        self.chk_laser = ctk.CTkSwitch(ext_card, text="Cursor Laser Pointer Ring", progress_color=COLORS["accent"], command=self.toggle_laser_ring)
        if APP_STATE.get("laser_ring_enabled", False):
            self.chk_laser.select()
        self.chk_laser.pack(anchor="w", padx=14, pady=4)

        self.chk_beeps = ctk.CTkSwitch(ext_card, text="Audio Chime Feedback (Non-Rumble)", progress_color=COLORS["accent"], command=self.toggle_audio_beeps)
        if APP_STATE.get("audio_beeps_enabled", False):
            self.chk_beeps.select()
        self.chk_beeps.pack(anchor="w", padx=14, pady=4)

        self.chk_idlesleep = ctk.CTkSwitch(ext_card, text="Inactivity Auto-Screen Off", progress_color=COLORS["accent"], command=self.toggle_idle_sleep)
        if APP_STATE.get("idle_sleep_enabled", False):
            self.chk_idlesleep.select()
        self.chk_idlesleep.pack(anchor="w", padx=14, pady=(4, 2))

        idle_row = ctk.CTkFrame(ext_card, fg_color="transparent")
        idle_row.pack(fill="x", padx=14)
        ctk.CTkLabel(idle_row, text="Idle Timeout").pack(side="left")
        self.lbl_idle_val = ctk.CTkLabel(idle_row, text=f"{APP_STATE['idle_timeout_min']:.0f} min", text_color=COLORS["accent"], font=ctk.CTkFont(weight="bold"))
        self.lbl_idle_val.pack(side="right")
        self.idle_slider = ctk.CTkSlider(ext_card, from_=5, to=60, button_color=COLORS["accent"], progress_color=COLORS["accent"], command=self.update_idle_timeout)
        self.idle_slider.set(APP_STATE["idle_timeout_min"])
        self.idle_slider.pack(fill="x", padx=14, pady=(2, 12))

        # --- RIGHT PANEL (LIVE MAPPING MATRIX) ---
        right_panel = ctk.CTkFrame(self, fg_color=COLORS["card_bg"], corner_radius=14, border_width=1, border_color=COLORS["card_border"])
        right_panel.grid(row=1, column=1, sticky="nsew", padx=(6, 16), pady=(6, 14))
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)
        self.main_containers.append(right_panel)

        remap_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        remap_header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))

        ctk.CTkLabel(remap_header, text="BUTTON MAPPINGS & FIRE MODES", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["text_muted"]).pack(side="left")

        ctk.CTkButton(
            remap_header, text="Reset Profile", width=100, height=28,
            fg_color="transparent", border_width=1, border_color=COLORS["card_border"],
            text_color=COLORS["text_muted"], hover_color=COLORS["danger"],
            command=self.reset_current_mappings
        ).pack(side="right", padx=(8, 0))

        self.seg_mode = ctk.CTkSegmentedButton(
            remap_header,
            values=["Standard", "Combo (Hold Shift)"],
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            command=self.switch_remap_mode
        )
        self.seg_mode.set(self.current_remap_mode)
        self.seg_mode.pack(side="right")

        self.scroll_frame = ctk.CTkScrollableFrame(right_panel, fg_color="transparent")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self.render_remap_list()

    def format_badge_state(self, btn_id, is_combo):
        prof = get_current_profile()
        mod_btn_id = MODIFIER_BTN_MAP.get(APP_STATE["combo_modifier"])
        if btn_id == mod_btn_id:
            return f"Reserved ({APP_STATE['combo_modifier']} Shift)", COLORS["warning"], "#000000"

        if is_combo:
            act = prof["combo_mappings"].get(btn_id, "None")
            if act and act != "None":
                return act[:30], COLORS["accent"], COLORS["text_main"]
            std_act = prof["mappings"].get(btn_id, "None")
            if std_act and std_act != "None":
                return f"Fallback → {std_act[:20]}", "transparent", COLORS["text_muted"]
            return "None", "transparent", COLORS["text_muted"]
        else:
            act = prof["mappings"].get(btn_id, "None")
            if act and act != "None":
                return act[:30], COLORS["key_special"], COLORS["text_main"]
            if APP_STATE["trigger_Precision"] and btn_id == 106:
                return "Analog Sniper (30%)", "transparent", COLORS["warning"]
            if APP_STATE["trigger_Precision"] and btn_id == 107:
                return "Analog Boost (200%)", "transparent", COLORS["accent"]
            return "None", "transparent", COLORS["text_muted"]

    def format_mode_btn_style(self, mode):
        if mode == "Turbo":
            return "⚡ Turbo", COLORS["warning"], "#000000"
        elif mode == "Toggle":
            return "🔒 Toggle", COLORS["accent"], COLORS["text_main"]
        return "1x Normal", COLORS["key_std"], COLORS["text_muted"]

    def render_remap_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        self.mapping_badges.clear()
        self.mode_buttons.clear()
        self.mapping_rows.clear()
        is_combo = (self.current_remap_mode != "Standard")
        prof = get_current_profile()
        self.last_rendered_profile = APP_STATE["active_profile"]

        for category, btn_ids in BTN_CATEGORIES.items():
            cat_lbl = ctk.CTkLabel(
                self.scroll_frame, text=category.upper(),
                font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["accent"]
            )
            cat_lbl.pack(anchor="w", padx=10, pady=(8, 3))

            for btn_id in btn_ids:
                btn_name = BTN_NAMES[btn_id]
                row = ctk.CTkFrame(self.scroll_frame, fg_color=COLORS["row_idle"], corner_radius=8, height=42)
                row.pack(fill="x", pady=2, padx=6)
                self.mapping_rows[btn_id] = row

                ctk.CTkLabel(
                    row, text=btn_name, width=140, anchor="w",
                    font=ctk.CTkFont(size=13, weight="bold")
                ).pack(side="left", padx=(12, 4), pady=7)

                cur_mode = prof["btn_modes"].get(btn_id, "Normal")
                m_txt, m_bg, m_fg = self.format_mode_btn_style(cur_mode)
                mode_btn = ctk.CTkButton(
                    row, text=m_txt, width=84, height=26,
                    fg_color=m_bg, text_color=m_fg, hover_color=COLORS["card_border"],
                    font=ctk.CTkFont(size=11, weight="bold"), corner_radius=6,
                    command=lambda b_id=btn_id: self.cycle_button_mode(b_id)
                )
                mode_btn.pack(side="right", padx=(4, 10), pady=6)
                self.mode_buttons[btn_id] = mode_btn

                txt, bg_col, txt_col = self.format_badge_state(btn_id, is_combo)
                badge = ctk.CTkButton(
                    row, text=txt, height=26,
                    fg_color=bg_col, hover_color=COLORS["accent"],
                    text_color=txt_col, corner_radius=6,
                    command=lambda b_id=btn_id, c=is_combo: VisualPicker(self, b_id, c, self.update_mapping)
                )
                badge.pack(side="right", padx=4, pady=6)
                self.mapping_badges[btn_id] = badge

    def cycle_button_mode(self, btn_id):
        order = ["Normal", "Turbo", "Toggle"]
        prof = get_current_profile()
        cur = prof["btn_modes"].get(btn_id, "Normal")
        nxt = order[(order.index(cur) + 1) % len(order)]
        prof["btn_modes"][btn_id] = nxt
        m_txt, m_bg, m_fg = self.format_mode_btn_style(nxt)
        if btn_id in self.mode_buttons:
            self.mode_buttons[btn_id].configure(text=m_txt, fg_color=m_bg, text_color=m_fg)
        save_config()

    def change_profile(self, profile_name):
        with STATE_LOCK:
            APP_STATE["active_profile"] = profile_name
        play_audio_cue("profile")
        self.ent_app_rules.delete(0, "end")
        self.ent_app_rules.insert(0, get_current_profile().get("app_rules", ""))
        save_config()
        self.render_remap_list()

    def update_app_rules(self, event):
        prof = get_current_profile()
        prof["app_rules"] = self.ent_app_rules.get().strip()
        self.schedule_save()

    def export_profile(self):
        prof_name = APP_STATE["active_profile"]
        path = filedialog.asksaveasfilename(
            title=f"Export Profile ({prof_name})",
            defaultextension=".json",
            initialfile=f"JeetPad_{prof_name}.json",
            filetypes=[("JSON Profile", "*.json")]
        )
        if path:
            try:
                data = {"profile_name": prof_name, "profile_data": get_current_profile()}
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
            except Exception:
                pass

    def import_profile(self):
        path = filedialog.askopenfilename(title="Import Profile JSON", filetypes=[("JSON Profile", "*.json")])
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                p_name = loaded.get("profile_name", Path(path).stem.replace("JeetPad_", ""))
                p_data = sanitize_profile_dict(loaded.get("profile_data", loaded))
                with STATE_LOCK:
                    APP_STATE["profiles"][p_name] = p_data
                    APP_STATE["active_profile"] = p_name
                self.opt_profile.configure(values=list(APP_STATE["profiles"].keys()))
                self.opt_profile.set(p_name)
                self.change_profile(p_name)
            except Exception:
                pass

    def switch_remap_mode(self, value):
        self.current_remap_mode = value
        self.refresh_badges()

    def reset_current_mappings(self):
        p_name = APP_STATE["active_profile"]
        with STATE_LOCK:
            if p_name in DEFAULT_PROFILES:
                APP_STATE["profiles"][p_name] = json.loads(json.dumps(DEFAULT_PROFILES[p_name]))
                APP_STATE["profiles"][p_name] = sanitize_profile_dict(APP_STATE["profiles"][p_name])
            else:
                APP_STATE["profiles"][p_name] = make_profile(BASE_DESKTOP_MAP)
        save_config()
        self.render_remap_list()

    def update_mapping(self, btn_id, new_action, is_combo):
        prof = get_current_profile()
        with STATE_LOCK:
            if is_combo:
                prof["combo_mappings"][btn_id] = new_action
            else:
                prof["mappings"][btn_id] = new_action
        save_config()
        self.refresh_badges()

    def refresh_badges(self):
        is_combo = (self.current_remap_mode != "Standard")
        prof = get_current_profile()
        for btn_id, badge in self.mapping_badges.items():
            txt, bg_col, txt_col = self.format_badge_state(btn_id, is_combo)
            badge.configure(text=txt, fg_color=bg_col, text_color=txt_col)
            if btn_id in self.mode_buttons:
                m_txt, m_bg, m_fg = self.format_mode_btn_style(prof["btn_modes"].get(btn_id, "Normal"))
                self.mode_buttons[btn_id].configure(text=m_txt, fg_color=m_bg, text_color=m_fg)

    def request_rescan(self):
        APP_STATE["rescan_requested"] = True

    def toggle_autoscan(self):
        APP_STATE["auto_scan"] = bool(self.chk_autoscan.get())
        save_config()

    def toggle_autoswitch(self):
        APP_STATE["auto_switch_profiles"] = bool(self.chk_autoswitch.get())
        save_config()

    def toggle_gamepause(self):
        APP_STATE["auto_pause_fullscreen"] = bool(self.chk_gamepause.get())
        save_config()

    def toggle_trig_precision(self):
        APP_STATE["trigger_Precision"] = bool(self.chk_trig_prec.get())
        self.refresh_badges()
        save_config()

    def toggle_update_on_startup(self):
        APP_STATE["check_updates_on_startup"] = bool(self.chk_update_startup.get())
        save_config()

    def toggle_hud(self):
        APP_STATE["hud_enabled"] = bool(self.chk_hud.get())
        save_config()

    def toggle_radial_wheel(self):
        APP_STATE["radial_wheel_enabled"] = bool(self.chk_radial.get())
        save_config()

    def toggle_daisywheel(self):
        APP_STATE["daisywheel_enabled"] = bool(self.chk_daisy.get())
        if not APP_STATE["daisywheel_enabled"]:
            APP_STATE["daisywheel_active"] = False
        save_config()

    def toggle_edge_wrap(self):
        APP_STATE["edge_wrap_enabled"] = bool(self.chk_edgewrap.get())
        save_config()

    def toggle_laser_ring(self):
        APP_STATE["laser_ring_enabled"] = bool(self.chk_laser.get())
        if not APP_STATE["laser_ring_enabled"]:
            APP_STATE["laser_ring_active"] = False
        save_config()

    def toggle_audio_beeps(self):
        APP_STATE["audio_beeps_enabled"] = bool(self.chk_beeps.get())
        if APP_STATE["audio_beeps_enabled"]:
            play_audio_cue("enable")
        save_config()

    def toggle_idle_sleep(self):
        APP_STATE["idle_sleep_enabled"] = bool(self.chk_idlesleep.get())
        save_config()

    def update_idle_timeout(self, val):
        APP_STATE["idle_timeout_min"] = float(val)
        self.lbl_idle_val.configure(text=f"{float(val):.0f} min")
        self.schedule_save()

    def update_interval(self, event):
        try:
            val = float(self.ent_interval.get())
            if val >= 1.0:
                APP_STATE["scan_interval"] = val
                self.schedule_save()
        except ValueError:
            pass

    def change_priority(self, choice):
        if choice in ("No Controller Detected", "Scanning..."):
            return
        try:
            APP_STATE["selected_controller_idx"] = int(choice.split("]")[0].replace("[", ""))
            save_config()
        except ValueError:
            pass

    def change_toggle_btn(self, choice):
        for btn_id, name in BTN_NAMES.items():
            if name == choice:
                APP_STATE["toggle_button"] = btn_id
                self.lbl_hold_hint.configure(text=f"Hold [{name}] 3s to toggle")
                save_config()
                break

    def change_combo_mod(self, choice):
        APP_STATE["combo_modifier"] = choice
        save_config()
        self.refresh_badges()

    def toggle_master(self):
        APP_STATE["enabled"] = bool(self.switch_master.get())
        play_audio_cue("enable" if APP_STATE["enabled"] else "pause")
        self.sync_master_visuals()
        save_config()

    def sync_master_visuals(self):
        if APP_STATE["auto_paused_by_game"]:
            self.lbl_title.configure(text=f"Auto-Paused (Game)  (v{APP_VERSION})")
            self.status_dot.configure(text_color=COLORS["purple"])
        elif APP_STATE["enabled"]:
            self.lbl_title.configure(text=f"JeetPad Active  (v{APP_VERSION})")
            self.status_dot.configure(text_color=COLORS["success"])
        else:
            self.lbl_title.configure(text=f"JeetPad Paused  (v{APP_VERSION})")
            self.status_dot.configure(text_color=COLORS["warning"])

    def toggle_swap(self):
        APP_STATE["swap_sticks"] = bool(self.chk_swap.get())
        save_config()

    def toggle_autostart(self):
        set_autostart(bool(self.chk_startup.get()))

    def update_mouse(self, val):
        APP_STATE["mouse_speed"] = float(val)
        self.lbl_mouse_val.configure(text=f"{float(val):.0f}")
        self.schedule_save()

    def update_deadzone(self, val):
        APP_STATE["deadzone"] = float(val)
        self.lbl_dz_val.configure(text=f"{int(float(val)*100)}%")
        self.schedule_save()

    def update_scroll(self, val):
        APP_STATE["scroll_speed"] = float(val)
        self.lbl_scroll_val.configure(text=f"{float(val):.1f}x")
        self.schedule_save()

    def update_turbo_rate(self, val):
        APP_STATE["turbo_rate"] = float(val)
        self.lbl_turbo_val.configure(text=f"{float(val):.0f} CPS")
        self.schedule_save()

    def draw_stick_visualizer(self):
        c = self.stick_canvas
        c.delete("all")
        cx, cy, r = 48, 48, 40

        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=COLORS["card_border"], width=2)
        c.create_line(cx - r, cy, cx + r, cy, fill=COLORS["key_std"])
        c.create_line(cx, cy - r, cx, cy + r, fill=COLORS["key_std"])

        dz_r = r * float(APP_STATE.get("deadzone", 0.14))
        c.create_oval(cx - dz_r, cy - dz_r, cx + dz_r, cy + dz_r, outline=COLORS["warning"], dash=(2, 2))

        sx, sy, lt_val, rt_val = APP_STATE.get("stick_telemetry", (0.0, 0.0, 0.0, 0.0))
        px = cx + sx * r
        py = cy + sy * r
        in_dz = (sx ** 2 + sy ** 2) ** 0.5 < APP_STATE.get("deadzone", 0.14)
        dot_col = COLORS["text_muted"] if in_dz else COLORS["accent"]
        c.create_oval(px - 5, py - 5, px + 5, py + 5, fill=dot_col, outline="white")

        self.bar_lt.set(max(0.0, min(1.0, lt_val)))
        self.bar_rt.set(max(0.0, min(1.0, rt_val)))
        mult = APP_STATE.get("speed_multiplier", 1.0)
        self.lbl_speed_scale.configure(text=f"Speed Scale: {mult:.2f}x")

    def update_ui_loop(self):
        current_list = APP_STATE["available_controllers"]
        if self.opt_controller.cget("values") != current_list:
            self.opt_controller.configure(values=current_list)
            idx = APP_STATE["selected_controller_idx"]
            self.opt_controller.set(current_list[idx] if idx < len(current_list) else current_list[0])

        if APP_STATE["active_profile"] != self.last_rendered_profile:
            self.opt_profile.set(APP_STATE["active_profile"])
            self.ent_app_rules.delete(0, "end")
            self.ent_app_rules.insert(0, get_current_profile().get("app_rules", ""))
            self.render_remap_list()

        if APP_STATE["enabled"] != bool(self.switch_master.get()):
            if APP_STATE["enabled"]:
                self.switch_master.select()
            else:
                self.switch_master.deselect()
        self.sync_master_visuals()

        if APP_STATE.get("mod_currently_held", False):
            self.lbl_shift_indicator.configure(text="SHIFT HELD", fg_color=COLORS["accent"], text_color=COLORS["text_main"])
        else:
            self.lbl_shift_indicator.configure(text="SHIFT IDLE", fg_color=COLORS["card_border"], text_color=COLORS["text_muted"])

        if APP_STATE.get("hud_visible", False) and APP_STATE.get("hud_enabled", False):
            if not self.hud_overlay.winfo_viewable():
                self.hud_overlay.refresh_and_show()
        else:
            if self.hud_overlay.winfo_viewable():
                self.hud_overlay.withdraw()

        if APP_STATE.get("radial_active", False) and APP_STATE.get("radial_wheel_enabled", False):
            self.radial_overlay.show_and_render(self.ui_mouse_ref.position)
        else:
            if self.radial_overlay.winfo_viewable():
                self.radial_overlay.withdraw()

        if APP_STATE.get("daisywheel_active", False) and APP_STATE.get("daisywheel_enabled", False):
            self.daisywheel_overlay.update_and_show()
        else:
            if self.daisywheel_overlay.winfo_viewable():
                self.daisywheel_overlay.withdraw()

        if APP_STATE.get("laser_ring_active", False) and APP_STATE.get("laser_ring_enabled", False):
            self.laser_overlay.follow_cursor(self.ui_mouse_ref.position)
        else:
            if self.laser_overlay.winfo_viewable():
                self.laser_overlay.withdraw()

        pressed = APP_STATE.get("pressed_buttons", set())
        latched = APP_STATE.get("toggled_buttons", set())
        for btn_id, row_widget in self.mapping_rows.items():
            if btn_id in pressed or btn_id in latched:
                target_col = COLORS["row_active"]
            else:
                target_col = COLORS["row_idle"]
            if row_widget.cget("fg_color") != target_col:
                row_widget.configure(fg_color=target_col)

        self.draw_stick_visualizer()
        self.after(50, self.update_ui_loop)

    def create_fallback_icon(self):
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        fill_rgba = hex_to_rgb_tuple(COLORS["accent"])
        draw.rounded_rectangle((4, 4, 60, 60), radius=14, fill=fill_rgba)
        draw.ellipse((16, 20, 28, 32), fill="white")
        draw.ellipse((36, 32, 48, 44), fill="white")
        return img

    def hide_window(self):
        self.withdraw()
        if self.tray_icon is not None:
            return
        try:
            image = Image.open(resource_path("icon.png"))
        except Exception:
            image = self.create_fallback_icon()

        menu = pystray.Menu(
            pystray.MenuItem("Open JeetPad", self.show_window, default=True),
            pystray.MenuItem("Check for Updates", self.tray_check_update),
            pystray.MenuItem("Toggle Active/Pause", self.tray_toggle),
            pystray.MenuItem("Quit", self.quit_app)
        )
        self.tray_icon = pystray.Icon("JeetPad", image, f"JeetPad v{APP_VERSION}", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def tray_check_update(self, icon, item):
        self.show_window(icon, item)
        self.after(200, lambda: self.trigger_update_check(manual=True))

    def tray_toggle(self, icon, item):
        APP_STATE["enabled"] = not APP_STATE["enabled"]
        save_config()

    def show_window(self, icon, item):
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.after(0, self.deiconify)

    def quit_app(self, icon, item):
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.after(0, self.force_quit)

    def force_quit(self):
        save_config()
        try:
            self.destroy()
        except Exception:
            pass
        os._exit(0)


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False

if __name__ == "__main__":
    if platform.system() == "Windows" and not is_admin():
        if getattr(sys, "frozen", False):
            params = " ".join(f'"{a}"' for a in sys.argv[1:])
        else:
            params = " ".join(f'"{a}"' for a in sys.argv)
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        sys.exit(0)

    threading.Thread(target=controller_worker, daemon=True).start()
    app = ModernControllerApp()
    app.mainloop()
