#!/usr/bin/env python3
import os
import sys
import json
import shutil
import urllib.request
import urllib.error
import zipfile
import re
import threading
import time
import sqlite3
import tkinter as tk
from tkinter import messagebox, filedialog

# Color Palette: Modern Glassmorphic Theme (Premium Dark)
CAT_BASE = "#0d1117"       # Deeper, premium dark base
CAT_MANTLE = "#161b22"     # Sleeker dark gray-blue mantle
CAT_CRUST = "#090d12"      # Ultra-dark header accents
CAT_SURFACE0 = "#30363d"    # Clean border color
CAT_SURFACE1 = "#8b949e"    # Highlight border
CAT_TEXT = "#f0f6fc"       # Main Text (Crisp white)
CAT_SUBTEXT0 = "#8b949e"   # Muted Text (Subdued gray)
CAT_BLUE = "#58a6ff"       # Primary Accent (Premium blue)
CAT_GREEN = "#3fb950"      # Success Accent
CAT_RED = "#f85149"        # Error Accent
CAT_YELLOW = "#d29922"     # Warning Accent
CAT_BTN_CONFIRM = "#58a6ff"  # Confirm button bright fill
CAT_BTN_OUTLINE = "#30363d"  # Button outline/border color
CAT_CARD_BORDER = "#30363d"  # Card row border color

# Globally cached images (to prevent garbage collection in Tkinter!)
TK_IMAGE_CACHE = {}

def get_game_image(appid):
    """Downloads game capsule from Steam CDN, converts to PNG using sips, and returns the path to the PNG."""
    cache_dir = os.path.join(DEFAULT_TEMP_DIR, "image_cache")
    try:
        os.makedirs(cache_dir, exist_ok=True)
    except Exception:
        pass
        
    png_path = os.path.join(cache_dir, f"{appid}.png")
    if os.path.exists(png_path):
        return png_path
        
    jpg_path = os.path.join(cache_dir, f"{appid}.jpg")
    url = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/capsule_184x69.jpg"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            with open(jpg_path, "wb") as f:
                f.write(response.read())
        
        # Convert to PNG using sips (macOS native command)
        import subprocess
        subprocess.run(["sips", "-s", "format", "png", jpg_path, "--out", png_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if os.path.exists(jpg_path):
            try:
                os.remove(jpg_path)
            except Exception:
                pass
                
        if os.path.exists(png_path):
            return png_path
    except Exception as e:
        print(f"Error downloading image for {appid}: {e}")
        
    return None

def get_game_image_thumbnail(appid):
    """Downloads game capsule from Steam CDN, resizes to 120x45 using sips, and returns the path to the PNG."""
    cache_dir = os.path.join(DEFAULT_TEMP_DIR, "image_cache")
    try:
        os.makedirs(cache_dir, exist_ok=True)
    except Exception:
        pass
        
    png_path = os.path.join(cache_dir, f"{appid}_thumb.png")
    if os.path.exists(png_path):
        return png_path
        
    jpg_path = os.path.join(cache_dir, f"{appid}.jpg")
    if not os.path.exists(jpg_path):
        url = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/capsule_184x69.jpg"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                with open(jpg_path, "wb") as f:
                    f.write(response.read())
        except Exception as e:
            print(f"Error downloading image for thumb {appid}: {e}")
            return None
            
    # Resize and convert to PNG using sips
    import subprocess
    subprocess.run(["sips", "-z", "45", "120", jpg_path, "--out", png_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return png_path if os.path.exists(png_path) else None

# State Constants
STATE_DETECT = 0
STATE_DOWNLOAD = 1
STATE_SUCCESS = 2
STATE_RESTART = 3
STATE_MANAGE = 4

# Default Paths on Mac_EXT
MAC_EXT_ROOT = "/Volumes/Mac_EXT"
DEFAULT_STEAM_PATH = os.path.join(MAC_EXT_ROOT, "CrossOverData/CrossOver/Bottles/Steam/drive_c/Program Files (x86)/Steam")
DEFAULT_TEMP_DIR = os.path.join(MAC_EXT_ROOT, "Steam break/luatools_temp")
DEFAULT_SETTINGS_FILE = os.path.join(DEFAULT_STEAM_PATH, "millennium/plugins/tools/backend/data/settings.json")
DEFAULT_API_FILE = os.path.join(DEFAULT_STEAM_PATH, "millennium/plugins/tools/backend/api.json")

FALLBACK_APIS = [
    {"name": "Morrenus", "url": "https://hubcapmanifest.com/api/v1/manifest/<appid>?api_key=<moapikey>", "success_code": 200, "enabled": True},
    {"name": "Ryuu", "url": "http://167.235.229.108/<appid>", "success_code": 200, "enabled": True},
    {"name": "TwentyTwo Cloud", "url": "https://api.twentytwocloud.com/download?appid=<appid>", "success_code": 200, "enabled": True},
    {"name": "Sushi", "url": "https://raw.githubusercontent.com/sushi-dev55-alt/sushitools-games-repo-alt/refs/heads/main/<appid>.zip", "success_code": 200, "enabled": True}
]

# Custom Styled Label Button (tk.Button has severe color limitations on macOS)
class LabelButton(tk.Frame):
    """Custom styled button using Frame+Label for bordered pill appearance."""
    def __init__(self, parent, text, command, bg=CAT_BLUE, fg="#0e1621", hover_bg="#8ad4f8", active_bg="#4fc3f7", font=("Helvetica", 11, "bold"), pady=6, padx=15, state="normal", outlined=False):
        self.command = command
        self.bg = bg
        self.fg = fg
        self.hover_bg = hover_bg
        self.active_bg = active_bg
        self._state = state
        self.outlined = outlined
        
        # Border frame for outlined style
        border_color = CAT_BTN_OUTLINE if outlined else bg
        super().__init__(
            parent,
            bg=border_color,
            highlightthickness=0,
            bd=0,
        )
        
        inner_bg = CAT_BASE if outlined else bg
        inner_fg = CAT_TEXT if outlined else fg
        
        self.label = tk.Label(
            self,
            text=text,
            bg=inner_bg,
            fg=inner_fg,
            font=font,
            pady=pady,
            padx=padx,
            cursor="hand2",
            relief="flat",
            bd=0
        )
        self.label.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        self._inner_bg = inner_bg
        self._inner_fg = inner_fg
        
        self.label.bind("<Enter>", self.on_enter)
        self.label.bind("<Leave>", self.on_leave)
        self.label.bind("<ButtonPress-1>", self.on_press)
        self.label.bind("<ButtonRelease-1>", self.on_release)
        
        if state == "disabled":
            self.disable()

    def on_enter(self, event):
        if self._state == "normal":
            if self.outlined:
                self.label.configure(bg="#1e3048")
            else:
                self.label.configure(bg=self.hover_bg)

    def on_leave(self, event):
        if self._state == "normal":
            self.label.configure(bg=self._inner_bg)

    def on_press(self, event):
        if self._state == "normal":
            if self.outlined:
                self.label.configure(bg="#253a50")
            else:
                self.label.configure(bg=self.active_bg)

    def on_release(self, event):
        if self._state == "normal":
            self.label.configure(bg=self._inner_bg)
            if self.command:
                self.command()

    def configure_state(self, state):
        self._state = state
        if state == "disabled":
            self.disable()
        else:
            self.enable()

    def disable(self):
        self._state = "disabled"
        self.configure(bg=CAT_SURFACE0)
        self.label.configure(bg="#1a2838", fg=CAT_SUBTEXT0, cursor="arrow")

    def enable(self):
        self._state = "normal"
        border_color = CAT_BTN_OUTLINE if self.outlined else self.bg
        self.configure(bg=border_color)
        self.label.configure(bg=self._inner_bg, fg=self._inner_fg, cursor="hand2")

    def configure(self, **kwargs):
        """Override configure to handle bg on the outer frame."""
        super().configure(**kwargs)

# Custom Dropdown menu using tk.Label + tk.Menu
class TkDropdown:
    def __init__(self, parent, options, callback, bg=CAT_SURFACE0, fg=CAT_TEXT):
        self.callback = callback
        self.options = options
        self.current_value = options[0] if options else ""
        self.state = "normal"
        
        self.frame = tk.Frame(parent, bg=CAT_SURFACE0, highlightbackground=CAT_SURFACE1, highlightthickness=1, bd=0)
        
        self.lbl = tk.Label(
            self.frame, 
            text=f"  {self.current_value}  ▼", 
            bg=bg, 
            fg=fg, 
            font=("Helvetica", 11), 
            anchor="w",
            padx=10,
            pady=6,
            cursor="hand2"
        )
        self.lbl.pack(fill=tk.X)
        self.lbl.bind("<Button-1>", lambda e: self.show_menu())
        self.lbl.bind("<Enter>", lambda e: self.lbl.configure(bg=CAT_SURFACE1) if self.state == "normal" else None)
        self.lbl.bind("<Leave>", lambda e: self.lbl.configure(bg=bg) if self.state == "normal" else None)
        
        self.menu = tk.Menu(parent, tearoff=0, bg=CAT_MANTLE, fg=CAT_TEXT, activebackground=CAT_BLUE, activeforeground=CAT_CRUST, font=("Helvetica", 11))
        self.update_options(options)
        
    def update_options(self, options):
        self.options = options
        self.menu.delete(0, tk.END)
        for opt in options:
            self.menu.add_command(label=opt, command=lambda val=opt: self.select_option(val))
            
    def select_option(self, val):
        self.current_value = val
        self.lbl.configure(text=f"  {val}  ▼")
        self.callback(val)
        
    def show_menu(self):
        if self.state == "disabled":
            return
        x = self.lbl.winfo_rootx()
        y = self.lbl.winfo_rooty() + self.lbl.winfo_height()
        self.menu.post(x, y)
        
    def get(self):
        return self.current_value
        
    def set(self, val):
        self.current_value = val
        self.lbl.configure(text=f"  {val}  ▼")

    def configure_state(self, state):
        self.state = state
        if state == "disabled":
            self.lbl.configure(bg=CAT_SURFACE0, fg=CAT_SUBTEXT0, cursor="arrow")
        else:
            self.lbl.configure(bg=CAT_SURFACE0, fg=CAT_TEXT, cursor="hand2")

class ScrollableFrame(tk.Frame):
    def __init__(self, parent, bg=CAT_BASE, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0, bg=bg)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview, width=8, bd=0, highlightthickness=0)
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        
    def _on_mousewheel(self, event):
        try:
            self.canvas.yview_scroll(int(-1 * (event.delta)), "units")
        except Exception:
            pass

class LuaToolsHelperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LuaTools macOS Helper")
        self.root.geometry("800x350")
        self.root.configure(bg=CAT_BASE)
        self.root.resizable(False, False)
        
        # Apply Glassmorphism alpha
        try:
            self.root.wm_attributes("-alpha", 0.94)
        except Exception:
            pass
        
        # State variables
        self.steam_path = DEFAULT_STEAM_PATH
        self.temp_dir = DEFAULT_TEMP_DIR
        self.morrenus_key = ""
        self.apis = []
        self.installed_games = {} # appid -> name
        self.game_name_to_appid = {} # name -> appid
        self.game_name_cache = {} # appid -> name
        
        # Scanner states
        self.active_running_appid = 0
        self.active_running_name = ""
        self.last_detected_store_appid = 0
        self.last_detected_store_name = ""
        
        self.last_user_reg_mtime = 0
        self.cef_log_position = 0
        self.js_log_position = 0
        
        # Animation & Flow state
        self.running = True
        self.pulse_phase = False
        self.app_state = STATE_DETECT
        self.advanced_expanded = False
        self.patches_map = {} # listbox index -> appid_str
        
        # Configuration setup
        self.load_settings()
        self.load_apis()
        self.scan_installed_games()
        
        # Layout container
        self.container_frame = tk.Frame(self.root, bg=CAT_BASE)
        self.container_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # Render initial screen
        self.switch_state(STATE_DETECT)
        
        # Launch background monitors
        self.animate_pulse_loop()
        self.monitor_thread = threading.Thread(target=self.steam_monitor_loop, daemon=True)
        self.monitor_thread.start()

    def load_game_image_async(self, appid, callback):
        if appid in TK_IMAGE_CACHE:
            callback(TK_IMAGE_CACHE[appid])
            return
            
        def worker():
            png_path = get_game_image(appid)
            if png_path and os.path.exists(png_path):
                self.root.after(0, lambda: self.create_and_cache_photoimage(appid, png_path, callback))
        threading.Thread(target=worker, daemon=True).start()

    def load_game_image_thumb_async(self, appid, callback):
        cache_key = f"{appid}_thumb"
        if cache_key in TK_IMAGE_CACHE:
            callback(TK_IMAGE_CACHE[cache_key])
            return
            
        def worker():
            png_path = get_game_image_thumbnail(appid)
            if png_path and os.path.exists(png_path):
                self.root.after(0, lambda: self.create_and_cache_photoimage(cache_key, png_path, callback))
        threading.Thread(target=worker, daemon=True).start()

    def create_and_cache_photoimage(self, cache_key, png_path, callback):
        try:
            img = tk.PhotoImage(file=png_path)
            TK_IMAGE_CACHE[cache_key] = img
            callback(img)
        except Exception as e:
            print(f"Error creating PhotoImage for {cache_key}: {e}")

    # ── SETTINGS & DATA LOADERS ──
    def load_settings(self):
        if os.path.exists(DEFAULT_SETTINGS_FILE):
            try:
                with open(DEFAULT_SETTINGS_FILE, "r") as f:
                    data = json.load(f)
                    self.morrenus_key = data.get("values", {}).get("general", {}).get("morrenusApiKey", "")
                    saved_steam = data.get("values", {}).get("general", {}).get("steamPath", "")
                    saved_temp = data.get("values", {}).get("general", {}).get("tempDir", "")
                    if saved_steam and os.path.isdir(saved_steam):
                        self.steam_path = saved_steam
                    if saved_temp:
                        self.temp_dir = saved_temp
            except Exception as e:
                print(f"Error reading settings.json: {e}")

    def save_settings(self):
        try:
            data = {}
            if os.path.exists(DEFAULT_SETTINGS_FILE):
                with open(DEFAULT_SETTINGS_FILE, "r") as f:
                    try:
                        data = json.load(f)
                    except Exception:
                        pass
            if "values" not in data:
                data["values"] = {}
            if "general" not in data["values"]:
                data["values"]["general"] = {}
            data["values"]["general"]["morrenusApiKey"] = self.morrenus_key
            data["values"]["general"]["steamPath"] = self.steam_path
            data["values"]["general"]["tempDir"] = self.temp_dir
            
            os.makedirs(os.path.dirname(DEFAULT_SETTINGS_FILE), exist_ok=True)
            with open(DEFAULT_SETTINGS_FILE, "w") as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            messagebox.showerror("Settings Error", f"Failed to save settings: {e}")
            return False

    def load_apis(self):
        if os.path.exists(DEFAULT_API_FILE):
            try:
                with open(DEFAULT_API_FILE, "r") as f:
                    data = json.load(f)
                    self.apis = data.get("api_list", FALLBACK_APIS)
            except Exception as e:
                print(f"Error reading api.json: {e}")
                self.apis = FALLBACK_APIS
        else:
            self.apis = FALLBACK_APIS

    def scan_installed_games(self):
        self.installed_games = {}
        self.game_name_to_appid = {}
        steamapps_dir = os.path.join(self.steam_path, "steamapps")
        if not os.path.exists(steamapps_dir):
            return
        
        try:
            for file in os.listdir(steamapps_dir):
                if file.startswith("appmanifest_") and file.endswith(".acf"):
                    filepath = os.path.join(steamapps_dir, file)
                    appid, name = self.parse_acf_file(filepath)
                    if appid and name:
                        self.installed_games[appid] = name
                        self.game_name_to_appid[name] = appid
        except Exception as e:
            print(f"Error scanning steamapps: {e}")

    def parse_acf_file(self, filepath):
        try:
            appid = None
            name = None
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    appid_match = re.search(r'"appid"\s+"(\d+)"', line, re.IGNORECASE)
                    if appid_match:
                        appid = int(appid_match.group(1))
                    name_match = re.search(r'"name"\s+"([^"]+)"', line, re.IGNORECASE)
                    if name_match:
                        name = name_match.group(1)
            return appid, name
        except Exception:
            return None, None

    # ── STATE-DRIVEN SWITCHING & RENDERING ──
    def clear_container(self):
        for widget in self.container_frame.winfo_children():
            widget.destroy()

    def switch_state(self, new_state):
        self.app_state = new_state
        self.clear_container()
        
        if new_state == STATE_DETECT:
            self.root.geometry("800x380")
            self.render_detect_screen()
        elif new_state == STATE_DOWNLOAD:
            self.root.geometry("800x380")
            self.render_download_screen()
        elif new_state == STATE_SUCCESS:
            self.root.geometry("800x300")
            self.render_success_screen()
        elif new_state == STATE_RESTART:
            self.root.geometry("800x280")
            self.render_restart_screen()
        elif new_state == STATE_MANAGE:
            self.root.geometry("800x520")
            self.render_manage_screen()

    # ── STATE 0: DETECT SCREEN ──
    def render_detect_screen(self):
        # Header Status Pulse Badge
        status_bar = tk.Frame(self.container_frame, bg=CAT_CRUST, highlightbackground=CAT_SURFACE0, highlightthickness=1, bd=0, height=35)
        status_bar.pack(fill=tk.X, pady=(0, 15))
        status_bar.pack_propagate(False)
        
        self.pulse_canvas = tk.Canvas(status_bar, width=12, height=12, bg=CAT_CRUST, highlightthickness=0)
        self.pulse_canvas.pack(side=tk.LEFT, padx=(12, 6))
        self.pulse_circle = self.pulse_canvas.create_oval(2, 2, 10, 10, fill="#2a4a6b", outline="")
        
        self.status_lbl = tk.Label(status_bar, text="Waiting for Steam Store activity...", font=("Helvetica", 11, "bold"), fg=CAT_TEXT, bg=CAT_CRUST)
        self.status_lbl.pack(side=tk.LEFT)

        # Scanned Cart & Store Dropdown section
        scanned_lbl = tk.Label(self.container_frame, text="Recently Viewed & Cart Games:", font=("Helvetica", 11, "bold"), fg=CAT_SUBTEXT0, bg=CAT_BASE)
        scanned_lbl.pack(anchor=tk.W, pady=(5, 3))
        
        # Build options mapping
        detected_options = self.get_scanned_dropdown_options()
        self.scanned_dropdown = TkDropdown(self.container_frame, detected_options, self.on_dropdown_game_selected)
        self.scanned_dropdown.frame.pack(fill=tk.X, pady=2)
        
        # Display Area Card
        self.game_card = tk.Frame(self.container_frame, bg=CAT_MANTLE, highlightbackground=CAT_SURFACE0, highlightthickness=1, bd=0, height=110)
        self.game_card.pack(fill=tk.X, pady=15)
        self.game_card.pack_propagate(False)
        
        # Left: image thumbnail
        self.game_card_img = tk.Label(self.game_card, bg=CAT_MANTLE)
        self.game_card_img.pack(side=tk.LEFT, padx=15, pady=10)
        
        # Right: title and details
        self.game_card_info = tk.Frame(self.game_card, bg=CAT_MANTLE)
        self.game_card_info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=10)
        
        self.game_card_title = tk.Label(self.game_card_info, text="No Steam Store Game Detected", font=("Helvetica", 14, "bold"), fg=CAT_TEXT, bg=CAT_MANTLE)
        self.game_card_title.pack(anchor=tk.W, pady=(15, 2))
        
        self.game_card_sub = tk.Label(self.game_card_info, text="Browse any game store page inside Steam and it will show up here", font=("Helvetica", 11), fg=CAT_SUBTEXT0, bg=CAT_MANTLE)
        self.game_card_sub.pack(anchor=tk.W, pady=2)
        
        # Action Buttons frame
        btn_frame = tk.Frame(self.container_frame, bg=CAT_BASE)
        btn_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.btn_add = LabelButton(
            btn_frame, 
            text="Add via LuaTools", 
            command=self.on_add_clicked,
            bg=CAT_BLUE,
            fg="#0e1621",
            pady=8
        )
        self.btn_add.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.btn_add.configure_state("disabled")
        
        btn_manage = LabelButton(
            btn_frame,
            text="Manage Patches",
            command=lambda: self.switch_state(STATE_MANAGE),
            bg=CAT_SURFACE0,
            fg=CAT_TEXT,
            hover_bg=CAT_SURFACE1,
            active_bg=CAT_SURFACE1,
            pady=8,
            outlined=True
        )
        btn_manage.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Trigger an initial check to populate game details
        self.on_dropdown_game_selected(detected_options[0])

    def get_scanned_dropdown_options(self):
        detected = self.scan_steam_activity()
        options = []
        for appid, name, source in detected:
            options.append(f"{name} ({source} - App ID: {appid})")
        if not options:
            options.append("No activity detected (Empty)")
        return options

    def on_dropdown_game_selected(self, selected_str):
        if "App ID: " in selected_str:
            match = re.search(r'App ID:\s*(\d+)', selected_str)
            if match:
                appid = int(match.group(1))
                name = selected_str.split(" (")[0]
                self.set_selected_game(appid, name)
                return
        
        # If manual AppID input has value when advanced is open
        if hasattr(self, 'adv_appid_ent') and self.adv_appid_ent.get().strip().isdigit():
            appid = int(self.adv_appid_ent.get().strip())
            name = self.installed_games.get(appid, self.game_name_cache.get(appid, f"Game {appid}"))
            self.set_selected_game(appid, name)
            return

        self.set_selected_game(0, "")

    def set_selected_game(self, appid, name):
        self.selected_appid = appid
        self.selected_name = name
        
        if appid > 0:
            self.game_card_title.configure(text=name, fg=CAT_TEXT)
            self.game_card_sub.configure(text=f"App ID: {appid} | Ready to download patch files", fg=CAT_SUBTEXT0)
            self.btn_add.configure_state("normal")
            
            # Load and display image
            self.game_card_img.configure(image="")
            self.load_game_image_async(appid, lambda img: self.game_card_img.configure(image=img) if self.game_card_img.winfo_exists() else None)
            
            # Fill manual entry if open
            if hasattr(self, 'adv_appid_ent'):
                self.adv_appid_ent.delete(0, tk.END)
                self.adv_appid_ent.insert(0, str(appid))
        else:
            self.game_card_title.configure(text="No Steam Store Game Selected", fg=CAT_SUBTEXT0)
            self.game_card_sub.configure(text="Select a game from the dropdown or browse store pages in Steam", fg=CAT_SUBTEXT0)
            self.btn_add.configure_state("disabled")
            self.game_card_img.configure(image="")

    def render_manage_screen(self):
        title_lbl = tk.Label(self.container_frame, text="Manage Patches & Settings", font=("Helvetica", 14, "bold"), fg=CAT_BLUE, bg=CAT_BASE)
        title_lbl.pack(anchor=tk.W, pady=(0, 10))
        
        # Main Grid Frame
        manage_frame = tk.Frame(self.container_frame, bg=CAT_BASE)
        manage_frame.pack(fill=tk.BOTH, expand=True)
        
        manage_frame.columnconfigure(0, weight=1)
        manage_frame.columnconfigure(1, weight=1)
        
        # LEFT COLUMN: Manual Entry & Settings
        left_sub = tk.Frame(manage_frame, bg=CAT_BASE)
        left_sub.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # AppID Manual entry
        manual_lbl = tk.Label(left_sub, text="Manual App ID Entry:", font=("Helvetica", 10, "bold"), fg=CAT_SUBTEXT0, bg=CAT_BASE)
        manual_lbl.pack(anchor=tk.W)
        
        entry_bg = tk.Frame(left_sub, bg=CAT_SURFACE0, highlightbackground=CAT_SURFACE1, highlightthickness=1, bd=0)
        entry_bg.pack(fill=tk.X, pady=(2, 10))
        self.adv_appid_ent = tk.Entry(entry_bg, bg=CAT_MANTLE, fg=CAT_TEXT, insertbackground=CAT_TEXT, relief="flat", bd=0, font=("Helvetica", 11))
        self.adv_appid_ent.pack(fill=tk.X, padx=6, pady=4)
        if hasattr(self, 'selected_appid') and self.selected_appid > 0:
            self.adv_appid_ent.insert(0, str(self.selected_appid))
        self.adv_appid_ent.bind("<KeyRelease>", self.on_manual_appid_typed)
        
        # Settings Inputs
        settings_card = tk.Frame(left_sub, bg=CAT_MANTLE, highlightbackground=CAT_SURFACE0, highlightthickness=1, bd=0)
        settings_card.pack(fill=tk.BOTH, expand=True)
        
        sett_lbl = tk.Label(settings_card, text="Settings & Folders", font=("Helvetica", 10, "bold"), fg=CAT_BLUE, bg=CAT_MANTLE)
        sett_lbl.pack(anchor=tk.W, padx=10, pady=(8, 2))
        
        self.setting_steam_ent = self.create_adv_entry(settings_card, "Steam Path", self.steam_path, self.browse_steam_path)
        self.setting_temp_ent = self.create_adv_entry(settings_card, "Temp Download Path", self.temp_dir, self.browse_temp_path)
        self.setting_key_ent = self.create_adv_entry(settings_card, "Morrenus API Key (Optional)", self.morrenus_key, None)
        
        save_btn = LabelButton(settings_card, text="Save Settings", command=self.apply_and_save_settings, bg=CAT_BLUE, fg="#0e1621", font=("Helvetica", 9, "bold"), pady=4)
        save_btn.pack(anchor=tk.E, padx=10, pady=10)

        # RIGHT COLUMN: Installed Patches Scrollable Container
        right_sub = tk.Frame(manage_frame, bg=CAT_BASE)
        right_sub.grid(row=0, column=1, sticky="nsew")
        
        patches_lbl = tk.Label(right_sub, text="Installed Patches:", font=("Helvetica", 10, "bold"), fg=CAT_SUBTEXT0, bg=CAT_BASE)
        patches_lbl.pack(anchor=tk.W)
        
        list_container = tk.Frame(right_sub, bg=CAT_MANTLE, highlightbackground=CAT_SURFACE0, highlightthickness=1, bd=0)
        list_container.pack(fill=tk.BOTH, expand=True, pady=2)
        
        self.scroll_frame = ScrollableFrame(list_container, bg=CAT_MANTLE)
        self.scroll_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        self.refresh_installed_list()
        
        # BOTTOM: Back Button
        btn_back = LabelButton(
            self.container_frame,
            text="Back to Detections",
            command=lambda: self.switch_state(STATE_DETECT),
            bg=CAT_SURFACE0,
            fg=CAT_TEXT,
            pady=6,
            outlined=True
        )
        btn_back.pack(fill=tk.X, pady=(15, 0))

    def create_adv_entry(self, parent, label_text, value, browse_cmd):
        lbl = tk.Label(parent, text=label_text, font=("Helvetica", 9), fg=CAT_SUBTEXT0, bg=CAT_MANTLE)
        lbl.pack(anchor=tk.W, padx=10, pady=(5, 1))
        
        row = tk.Frame(parent, bg=CAT_MANTLE)
        row.pack(fill=tk.X, padx=10)
        
        entry_bg = tk.Frame(row, bg=CAT_SURFACE0, highlightbackground=CAT_SURFACE1, highlightthickness=1, bd=0)
        entry_bg.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ent = tk.Entry(entry_bg, bg=CAT_MANTLE, fg=CAT_TEXT, insertbackground=CAT_TEXT, relief="flat", bd=0, font=("Helvetica", 10))
        ent.pack(fill=tk.X, padx=4, pady=3)
        ent.insert(0, value)
        
        if browse_cmd:
            btn_br = LabelButton(row, text="...", command=browse_cmd, bg=CAT_SURFACE0, fg=CAT_TEXT, font=("Helvetica", 10, "bold"), pady=3, padx=8)
            btn_br.pack(side=tk.RIGHT, padx=(5, 0))
            
        return ent

    def on_manual_appid_typed(self, event):
        val = self.adv_appid_ent.get().strip()
        if val.isdigit():
            appid = int(val)
            name = self.installed_games.get(appid, self.game_name_cache.get(appid, f"Game {appid}"))
            self.selected_appid = appid
            self.selected_name = name
            self.game_card_title.configure(text=name, fg=CAT_TEXT)
            self.game_card_sub.configure(text=f"App ID: {appid} | Ready to download patch files", fg=CAT_SUBTEXT0)
            self.btn_add.configure_state("normal")
            if appid not in self.game_name_cache and appid not in self.installed_games:
                self.resolve_game_name(appid)
        else:
            self.btn_add.configure_state("disabled")

    def on_add_clicked(self):
        if self.selected_appid > 0:
            self.start_download_flow(self.selected_appid)

    # ── STATE 1: DOWNLOAD SCREEN ──
    def render_download_screen(self):
        # Header with cloud icon and title
        header_frame = tk.Frame(self.container_frame, bg=CAT_BASE)
        header_frame.pack(fill=tk.X, pady=(5, 12))
        
        cloud_canvas = tk.Canvas(header_frame, width=24, height=24, bg=CAT_BASE, highlightthickness=0)
        cloud_canvas.pack(side=tk.LEFT, padx=(0, 8))
        cloud_canvas.create_text(12, 12, text="☁", font=("Helvetica", 16), fill=CAT_BLUE)
        
        title = tk.Label(header_frame, text="Select Download Source", font=("Helvetica", 16, "bold"), fg=CAT_TEXT, bg=CAT_BASE)
        title.pack(side=tk.LEFT)
        
        # Individual bordered card rows for each API source
        self.api_status_widgets = {}
        for api in self.apis:
            name = api["name"]
            row_border = tk.Frame(self.container_frame, bg=CAT_CARD_BORDER, bd=0)
            row_border.pack(fill=tk.X, pady=3)
            
            row = tk.Frame(row_border, bg=CAT_MANTLE, bd=0)
            row.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
            
            lbl_name = tk.Label(row, text=name, font=("Helvetica", 12), fg=CAT_TEXT, bg=CAT_MANTLE)
            lbl_name.pack(side=tk.LEFT, padx=12, pady=8)
            
            lbl_status = tk.Label(row, text="Waiting...", font=("Helvetica", 11), fg=CAT_SUBTEXT0, bg=CAT_MANTLE)
            lbl_status.pack(side=tk.RIGHT, padx=12, pady=8)
            self.api_status_widgets[name] = lbl_status

        # Progress description label
        self.progress_lbl = tk.Label(self.container_frame, text="Searching across sources...", font=("Helvetica", 11), fg=CAT_SUBTEXT0, bg=CAT_BASE)
        self.progress_lbl.pack(pady=(12, 5))
        
        # Progress Bar with border outline (matching reference)
        prog_border = tk.Frame(self.container_frame, bg=CAT_BTN_OUTLINE, bd=0)
        prog_border.pack(fill=tk.X, pady=(0, 5))
        self.prog_canvas = tk.Canvas(prog_border, height=14, bg=CAT_MANTLE, highlightthickness=0)
        self.prog_canvas.pack(fill=tk.X, padx=1, pady=1)
        self.prog_bar = self.prog_canvas.create_rectangle(0, 0, 0, 14, fill=CAT_BLUE, outline="")
        
        # Percentage label
        self.pct_lbl = tk.Label(self.container_frame, text="0%", font=("Helvetica", 10), fg=CAT_SUBTEXT0, bg=CAT_BASE)
        self.pct_lbl.pack(anchor=tk.W, pady=(0, 12))
        
        # Twin buttons: Cancel + Hide (bordered pill style)
        btn_frame = tk.Frame(self.container_frame, bg=CAT_BASE)
        btn_frame.pack(fill=tk.X)
        
        btn_cancel = LabelButton(btn_frame, text="Cancel", command=lambda: self.switch_state(STATE_DETECT), bg=CAT_SURFACE0, fg=CAT_TEXT, pady=6, outlined=True)
        btn_cancel.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        btn_hide = LabelButton(btn_frame, text="Hide", command=lambda: self.root.iconify(), bg=CAT_SURFACE0, fg=CAT_TEXT, pady=6, outlined=True)
        btn_hide.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

    def update_progress(self, percent, text):
        if self.app_state != STATE_DOWNLOAD:
            return
        self.root.after(0, lambda: self._sync_progress(percent, text))

    def _sync_progress(self, percent, text):
        self.progress_lbl.configure(text=text)
        width = self.prog_canvas.winfo_width()
        fill_width = int((percent / 100.0) * width)
        self.prog_canvas.coords(self.prog_bar, 0, 0, fill_width, 14)
        if hasattr(self, 'pct_lbl'):
            self.pct_lbl.configure(text=f"{int(percent)}%")

    def update_api_status(self, name, text, color):
        if self.app_state != STATE_DOWNLOAD:
            return
        if name in self.api_status_widgets:
            self.root.after(0, lambda: self.api_status_widgets[name].configure(text=text, fg=color))

    # ── STATE 2: SUCCESS SCREEN ──
    def render_success_screen(self):
        # Green Circle with checkmark
        canvas_check = tk.Canvas(self.container_frame, width=50, height=50, bg=CAT_BASE, highlightthickness=0)
        canvas_check.pack(pady=(20, 8))
        canvas_check.create_oval(5, 5, 45, 45, fill=CAT_GREEN, outline="")
        canvas_check.create_text(25, 25, text="✔", font=("Helvetica", 18, "bold"), fill="#ffffff")
        
        title = tk.Label(self.container_frame, text="Game Added!", font=("Helvetica", 18, "bold"), fg=CAT_TEXT, bg=CAT_BASE)
        title.pack(pady=2)
        
        sub = tk.Label(self.container_frame, text="The game has been added successfully.", font=("Helvetica", 12), fg=CAT_SUBTEXT0, bg=CAT_BASE)
        sub.pack(pady=(0, 25))
        
        btn_close = LabelButton(self.container_frame, text="Close", command=self.on_success_closed, bg=CAT_SURFACE0, fg=CAT_TEXT, pady=6, outlined=True)
        btn_close.pack(fill=tk.X)

    def on_success_closed(self):
        # Flow proceeds to restart request prompt
        self.switch_state(STATE_RESTART)

    # ── STATE 3: RESTART CONFIRMATION SCREEN ──
    def render_restart_screen(self):
        # Centered question-mark badge (matching reference)
        canvas_q = tk.Canvas(self.container_frame, width=40, height=40, bg=CAT_BASE, highlightthickness=0)
        canvas_q.pack(pady=(15, 5))
        # Light blue circle outline with ? inside
        canvas_q.create_oval(2, 2, 38, 38, fill="", outline=CAT_BLUE, width=2)
        canvas_q.create_text(20, 20, text="?", font=("Helvetica", 16, "bold"), fill=CAT_BLUE)
        
        title = tk.Label(self.container_frame, text="LuaTools", font=("Helvetica", 16, "bold"), fg=CAT_TEXT, bg=CAT_BASE)
        title.pack(pady=2)
        
        prompt = tk.Label(self.container_frame, text="Restart Steam now?", font=("Helvetica", 12), fg=CAT_SUBTEXT0, bg=CAT_BASE)
        prompt.pack(pady=(0, 25))
        
        btn_frame = tk.Frame(self.container_frame, bg=CAT_BASE)
        btn_frame.pack(fill=tk.X)
        
        btn_cancel = LabelButton(btn_frame, text="Cancel", command=lambda: self.switch_state(STATE_DETECT), bg=CAT_SURFACE0, fg=CAT_TEXT, pady=8, padx=25, outlined=True)
        btn_cancel.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        
        btn_confirm = LabelButton(btn_frame, text="Confirm", command=self.restart_steam_bottle, bg=CAT_BTN_CONFIRM, fg="#0e1621", hover_bg="#80d4f8", active_bg="#3db8e8", pady=8, padx=25)
        btn_confirm.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(8, 0))

    # ── DOWNLOAD FLOW PROCESS ──
    def start_download_flow(self, appid):
        self.switch_state(STATE_DOWNLOAD)
        threading.Thread(target=self.async_download_flow, args=(appid,), daemon=True).start()

    def get_urls_for_appid(self, appid):
        resolved_items = []
        for api in self.apis:
            if not api.get("enabled", True):
                continue
            url_template = api.get("url", "")
            url = url_template.replace("<appid>", str(appid))
            url = url.replace("<moapikey>", self.morrenus_key)
            resolved_items.append({"name": api.get("name"), "url": url, "success_code": api.get("success_code", 200)})
        return resolved_items

    def check_url_available(self, url, expected_code):
        try:
            req = urllib.request.Request(url, method='HEAD')
            req.add_header('User-Agent', 'discord(dot)gg/luatools')
            with urllib.request.urlopen(req, timeout=5) as response:
                status = response.status
        except urllib.error.HTTPError as e:
            status = e.code
        except Exception:
            status = 404

        if status == expected_code:
            return True
            
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'discord(dot)gg/luatools')
            req.add_header('Range', 'bytes=0-0')
            with urllib.request.urlopen(req, timeout=5) as response:
                status = response.status
        except urllib.error.HTTPError as e:
            status = e.code
        except Exception:
            status = 404
            
        return status in [expected_code, 206]

    def download_file_with_progress(self, url, dest_path):
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'discord(dot)gg/luatools')
        with urllib.request.urlopen(req, timeout=20) as response:
            total_size = int(response.info().get('Content-Length', 0))
            bytes_downloaded = 0
            block_size = 8192
            
            with open(dest_path, 'wb') as f:
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    f.write(buffer)
                    bytes_downloaded += len(buffer)
                    if total_size > 0:
                        percent = int((bytes_downloaded / total_size) * 50) + 10  # download is 10%-60% progress
                        self.update_progress(percent, f"Downloading... {percent}%")

    def async_download_flow(self, appid):
        resolved_items = self.get_urls_for_appid(appid)
        found_url = None
        found_api_name = None
        
        self.update_progress(0, "Connecting to patch servers...")
        
        for i, item in enumerate(resolved_items):
            name = item["name"]
            url = item["url"]
            expected_code = item["success_code"]
            
            if self.app_state != STATE_DOWNLOAD:
                return
                
            self.update_api_status(name, "Checking...", CAT_YELLOW)
            success = self.check_url_available(url, expected_code)
            
            if success:
                self.update_api_status(name, "Found ✔", CAT_GREEN)
                found_url = url
                found_api_name = name
                # Mark subsequent APIs as skipped
                for j in range(i + 1, len(resolved_items)):
                    self.update_api_status(resolved_items[j]["name"], "Skipped -", CAT_SUBTEXT0)
                break
            else:
                self.update_api_status(name, "Offline ✘", CAT_RED)
                
        if not found_url:
            self.root.after(0, lambda: messagebox.showerror("Download Error", f"Could not find patch files for App ID {appid} on any server."))
            self.root.after(0, lambda: self.switch_state(STATE_DETECT))
            return
            
        try:
            self.update_progress(10, f"Downloading from {found_api_name}...")
            
            st_plug_dir = os.path.join(self.steam_path, "config/stplug-in")
            depot_cache = os.path.join(self.steam_path, "depotcache")
            
            os.makedirs(st_plug_dir, exist_ok=True)
            os.makedirs(depot_cache, exist_ok=True)
            os.makedirs(self.temp_dir, exist_ok=True)
            
            zip_path = os.path.join(self.temp_dir, f"{appid}.zip")
            extract_dir = os.path.join(self.temp_dir, f"extracted_{appid}")
            
            self.download_file_with_progress(found_url, zip_path)
            
            if self.app_state != STATE_DOWNLOAD:
                return
                
            self.update_progress(65, "Extracting fix files...")
            
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            os.makedirs(extract_dir)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                
            self.update_progress(80, "Installing manifests & configuring script...")
            extracted_lua_path = None
            manifests_found = []
            
            for root_dir, _, files in os.walk(extract_dir):
                for file in files:
                    file_path = os.path.join(root_dir, file)
                    if file.endswith(".manifest"):
                        # Normalize Windows backslash paths and use only the basename
                        clean_name = os.path.basename(file.replace('\\', '/'))
                        dest = os.path.join(depot_cache, clean_name)
                        shutil.copy2(file_path, dest)
                        manifests_found.append(clean_name)
                    elif file == f"{appid}.lua":
                        extracted_lua_path = file_path
                    elif not extracted_lua_path and file.endswith(".lua"):
                        extracted_lua_path = file_path
                        
            if extracted_lua_path and os.path.exists(extracted_lua_path):
                target_lua = os.path.join(st_plug_dir, f"{appid}.lua")
                
                with open(extracted_lua_path, "r", encoding="utf-8", errors="ignore") as lf:
                    lines = lf.readlines()
                    
                processed_lines = []
                for line in lines:
                    if "setManifestid(" in line:
                        processed_lines.append("-- " + line.lstrip())
                    else:
                        processed_lines.append(line)
                        
                with open(target_lua, "w", encoding="utf-8") as tf:
                    tf.writelines(processed_lines)
                    
                self.update_progress(100, "Success!")
                time.sleep(0.5)
                self.root.after(0, lambda: self.switch_state(STATE_SUCCESS))
            else:
                raise Exception("No valid .lua file found inside patch package")
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Download Error", f"Failed to download/install: {e}"))
            self.root.after(0, lambda: self.switch_state(STATE_DETECT))
        finally:
            if 'zip_path' in locals() and os.path.exists(zip_path):
                os.remove(zip_path)
            if 'extract_dir' in locals() and os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)

    # ── SETTINGS & ADVANCED OPTIONS PANEL ACTIONS ──
    def browse_steam_path(self):
        selected = filedialog.askdirectory(title="Select Steam Installation Folder", initialdir=self.steam_path)
        if selected:
            self.setting_steam_ent.delete(0, tk.END)
            self.setting_steam_ent.insert(0, selected)

    def browse_temp_path(self):
        selected = filedialog.askdirectory(title="Select Temp Download Folder", initialdir=self.temp_dir)
        if selected:
            self.setting_temp_ent.delete(0, tk.END)
            self.setting_temp_ent.insert(0, selected)

    def apply_and_save_settings(self):
        self.steam_path = self.setting_steam_ent.get().strip()
        self.temp_dir = self.setting_temp_ent.get().strip()
        self.morrenus_key = self.setting_key_ent.get().strip()
        
        if self.save_settings():
            self.scan_installed_games()
            self.refresh_installed_list()
            
            # Refresh activity dropdown
            opts = self.get_scanned_dropdown_options()
            self.scanned_dropdown.update_options(opts)
            self.scanned_dropdown.set(opts[0])
            self.on_dropdown_game_selected(opts[0])
            
            messagebox.showinfo("Success", "Configuration saved and game library rescanned!")

    def refresh_installed_list(self):
        if not hasattr(self, 'scroll_frame'):
            return
            
        for widget in self.scroll_frame.scrollable_frame.winfo_children():
            widget.destroy()
            
        self.patches_map = {}
        
        # Dictionary of appid_str -> {"status": ..., "has_lua": bool}
        patches_data = {}
        
        # 1. Scan config/stplug-in for lua files
        st_plug_dir = os.path.join(self.steam_path, "config/stplug-in")
        if os.path.exists(st_plug_dir):
            try:
                for file in os.listdir(st_plug_dir):
                    if file.endswith(".lua"):
                        appid_str = file.replace(".lua", "")
                        patches_data[appid_str] = {"status": "Active", "has_lua": True}
                    elif file.endswith(".lua.disabled"):
                        appid_str = file.replace(".lua.disabled", "")
                        patches_data[appid_str] = {"status": "Disabled", "has_lua": True}
            except Exception as e:
                print(f"Error scanning stplug-in: {e}")
                
        # 2. Scan depotcache for manifest files to include manifest-only fixes
        depot_cache = os.path.join(self.steam_path, "depotcache")
        if os.path.exists(depot_cache):
            try:
                for file in os.listdir(depot_cache):
                    if file.endswith(".manifest"):
                        parts = file.split("_")
                        if parts:
                            appid_str = parts[0]
                            if appid_str.isdigit():
                                if appid_str not in patches_data:
                                    patches_data[appid_str] = {"status": "Active (Manifest)", "has_lua": False}
                    elif file.endswith(".manifest.disabled"):
                        parts = file.split("_")
                        if parts:
                            appid_str = parts[0]
                            if appid_str.isdigit():
                                if appid_str not in patches_data:
                                    patches_data[appid_str] = {"status": "Disabled (Manifest)", "has_lua": False}
            except Exception as e:
                print(f"Error scanning depotcache: {e}")

        if not patches_data:
            empty_lbl = tk.Label(self.scroll_frame.scrollable_frame, text="No patches installed.", font=("Helvetica", 11), fg=CAT_SUBTEXT0, bg=CAT_MANTLE)
            empty_lbl.pack(pady=20)
            return

        idx = 0
        for appid_str in sorted(patches_data.keys(), key=lambda x: int(x) if x.isdigit() else 999999):
            appid = int(appid_str)
            item = patches_data[appid_str]
            status = item["status"]
            game_name = self.installed_games.get(appid, self.game_name_cache.get(appid, f"Game {appid}"))
            
            # Custom Card Container
            card = tk.Frame(self.scroll_frame.scrollable_frame, bg=CAT_BASE, highlightbackground=CAT_SURFACE0, highlightthickness=1, bd=0)
            card.pack(fill=tk.X, pady=4, padx=5)
            
            # Left: Game Capsule Image (120x45)
            img_lbl = tk.Label(card, bg=CAT_BASE, width=120, height=45)
            img_lbl.pack(side=tk.LEFT, padx=8, pady=5)
            img_lbl.pack_propagate(False)
            
            # Load the thumbnail image asynchronously (using 120x45 size)
            self.load_game_image_thumb_async(appid, lambda img, l=img_lbl: l.configure(image=img) if l.winfo_exists() else None)
            
            # Center: Title & App ID
            info_frame = tk.Frame(card, bg=CAT_BASE)
            info_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, expand=True)
            
            name_lbl = tk.Label(info_frame, text=game_name, font=("Helvetica", 11, "bold"), fg=CAT_TEXT, bg=CAT_BASE, anchor="w")
            name_lbl.pack(anchor=tk.W, pady=(5, 0))
            
            is_active = status.startswith("Active")
            status_indicator = "🟢 Active" if is_active else "⚪ Disabled"
            if "Manifest" in status:
                status_indicator += " (Manifest)"
                
            status_color = CAT_GREEN if is_active else CAT_SUBTEXT0
            sub_lbl = tk.Label(info_frame, text=f"App ID: {appid} | {status_indicator}", font=("Helvetica", 9), fg=status_color, bg=CAT_BASE, anchor="w")
            sub_lbl.pack(anchor=tk.W, pady=(0, 5))
            
            # Right: Action Buttons
            btn_frame = tk.Frame(card, bg=CAT_BASE)
            btn_frame.pack(side=tk.RIGHT, padx=8)
            
            toggle_action = lambda a=appid_str, s=status: self.toggle_patch_direct(a, s)
            delete_action = lambda a=appid_str, s=status: self.delete_patch_direct(a, s)
            
            btn_toggle = LabelButton(btn_frame, text="Toggle", command=toggle_action, bg=CAT_SURFACE0, fg=CAT_TEXT, font=("Helvetica", 9, "bold"), pady=3, padx=6, outlined=True)
            btn_toggle.pack(side=tk.LEFT, padx=3)
            
            btn_delete = LabelButton(btn_frame, text="Delete", command=delete_action, bg=CAT_RED, fg="#ffffff", font=("Helvetica", 9, "bold"), pady=3, padx=6)
            btn_delete.pack(side=tk.LEFT, padx=3)
            
            self.patches_map[idx] = (appid_str, status)
            idx += 1
            
            if game_name.startswith("Game "):
                self.resolve_game_name(appid)

    def toggle_patch_direct(self, appid_str, status):
        st_plug_dir = os.path.join(self.steam_path, "config/stplug-in")
        depot_cache = os.path.join(self.steam_path, "depotcache")
        
        # 1. Toggle Lua script if it exists
        lua_active = os.path.join(st_plug_dir, f"{appid_str}.lua")
        lua_disabled = os.path.join(st_plug_dir, f"{appid_str}.lua.disabled")
        
        has_lua = os.path.exists(lua_active) or os.path.exists(lua_disabled)
        if has_lua:
            try:
                if status.startswith("Active"):
                    if os.path.exists(lua_active):
                        os.rename(lua_active, lua_disabled)
                else:
                    if os.path.exists(lua_disabled):
                        os.rename(lua_disabled, lua_active)
            except Exception as e:
                print(f"Error toggling lua patch: {e}")
                
        # 2. Toggle Manifest files in depotcache
        if os.path.exists(depot_cache):
            try:
                for file in os.listdir(depot_cache):
                    parts = file.split("_")
                    if parts and parts[0] == appid_str:
                        if status.startswith("Active"):
                            if file.endswith(".manifest"):
                                os.rename(os.path.join(depot_cache, file), os.path.join(depot_cache, f"{file}.disabled"))
                        else:
                            if file.endswith(".manifest.disabled"):
                                clean_name = file.replace(".manifest.disabled", ".manifest")
                                os.rename(os.path.join(depot_cache, file), os.path.join(depot_cache, clean_name))
            except Exception as e:
                print(f"Error toggling manifest files: {e}")
                
        self.refresh_installed_list()

    def delete_patch_direct(self, appid_str, status):
        confirm = messagebox.askyesno("Confirm", f"Are you sure you want to remove all files and manifests for App ID {appid_str}?")
        if not confirm:
            return

        st_plug_dir = os.path.join(self.steam_path, "config/stplug-in")
        depot_cache = os.path.join(self.steam_path, "depotcache")
        
        # Delete Lua script files
        for ext in [".lua", ".lua.disabled"]:
            lua_path = os.path.join(st_plug_dir, f"{appid_str}{ext}")
            try:
                if os.path.exists(lua_path):
                    os.remove(lua_path)
            except Exception:
                pass
                
        # Delete manifest files
        if os.path.exists(depot_cache):
            try:
                for file in os.listdir(depot_cache):
                    parts = file.split("_")
                    if parts and parts[0] == appid_str:
                        if file.endswith(".manifest") or file.endswith(".manifest.disabled"):
                            os.remove(os.path.join(depot_cache, file))
            except Exception:
                pass
                
        self.refresh_installed_list()
        messagebox.showinfo("Deleted", f"Successfully removed App ID {appid_str} patch files.")

    def resolve_game_name(self, appid):
        if appid in self.installed_games or appid in self.game_name_cache:
            return
        threading.Thread(target=self.async_resolve_game_name, args=(appid,), daemon=True).start()

    def async_resolve_game_name(self, appid):
        try:
            url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                if str(appid) in data and data[str(appid)].get('success'):
                    game_name = data[str(appid)]['data'].get('name', f"Game {appid}")
                    self.game_name_cache[appid] = game_name
                    # Trigger UI refresh
                    self.root.after(0, self.refresh_lists_and_dropdown)
        except Exception:
            pass

    def refresh_lists_and_dropdown(self):
        if self.app_state == STATE_DETECT:
            # Refresh dropdown list keeping selection
            selected_idx = self.scanned_dropdown.options.index(self.scanned_dropdown.get()) if self.scanned_dropdown.get() in self.scanned_dropdown.options else 0
            opts = self.get_scanned_dropdown_options()
            self.scanned_dropdown.update_options(opts)
            if selected_idx < len(opts):
                self.scanned_dropdown.set(opts[selected_idx])
            self.refresh_installed_list()

    # ── STEAM CLOSING & RESTART LOGIC ──
    def restart_steam_bottle(self):
        try:
            # Kill Steam Win32 processes running under CrossOver/Wine prefix
            os.system("pkill -9 -f steam.exe")
            os.system("pkill -9 -f steamwebhelper.exe")
            os.system("pkill -9 -f Steam.app")
            time.sleep(2.0)
        except Exception as e:
            print(f"Error terminating Steam: {e}")
            
        try:
            # Relaunch the specific CrossOver Steam launcher app
            launcher_path = "/Users/Vedant/Applications/CrossOver/Steam/Steam.app"
            if os.path.exists(launcher_path):
                os.system(f'open "{launcher_path}"')
                self.switch_state(STATE_DETECT)
            else:
                messagebox.showinfo("Steam Closed", "Steam has been closed. Please launch Steam manually from CrossOver.")
                self.switch_state(STATE_DETECT)
        except Exception as e:
            print(f"Error relaunching Steam: {e}")
            self.switch_state(STATE_DETECT)

    # ── PULSING LIGHT & STEAM MONITORING ──
    def animate_pulse_loop(self):
        if not self.running:
            return
            
        self.pulse_phase = not self.pulse_phase
        
        if self.app_state == STATE_DETECT:
            # Update connection/activity indicator color
            is_active = (self.active_running_appid > 0 or self.last_detected_store_appid > 0)
            if is_active:
                color = CAT_BLUE if self.pulse_phase else "#3d8ecf"
                self.status_lbl.configure(text=f"Detected Store Game: {self.selected_name}", fg=CAT_BLUE)
            else:
                color = "#2a4a6b"
                self.status_lbl.configure(text="Waiting for Steam Store activity...", fg=CAT_TEXT)
            self.pulse_canvas.itemconfig(self.pulse_circle, fill=color)
            
        self.root.after(500, self.animate_pulse_loop)

    def steam_monitor_loop(self):
        cef_log_path = os.path.join(self.steam_path, "logs/cef_log.txt")
        if os.path.exists(cef_log_path):
            self.cef_log_position = os.path.getsize(cef_log_path)
            
        js_log_path = os.path.join(self.steam_path, "logs/webhelper_js.txt")
        if os.path.exists(js_log_path):
            self.js_log_position = os.path.getsize(js_log_path)
            
        bottle_root = os.path.dirname(os.path.dirname(os.path.dirname(self.steam_path)))
        history_path = os.path.join(bottle_root, "drive_c/users/crossover/AppData/Local/Steam/htmlcache/Default/History")
        last_history_mtime = 0
        
        while self.running:
            try:
                self.check_running_game()
                self.check_cef_logs()
                self.check_webhelper_js_logs()
                
                if os.path.exists(history_path):
                    try:
                        mtime = os.path.getmtime(history_path)
                        if mtime > last_history_mtime:
                            last_history_mtime = mtime
                            self.check_steam_history()
                    except Exception as e:
                        print(f"Error checking history mtime: {e}")
            except Exception as e:
                print(f"Error in monitor loop: {e}")
            time.sleep(0.25)

    def check_running_game(self):
        # Poll user.reg for RunningAppID
        user_reg_path = os.path.join(os.path.dirname(os.path.dirname(self.steam_path)), "user.reg")
        if not os.path.exists(user_reg_path):
            return
            
        try:
            mtime = os.path.getmtime(user_reg_path)
            if mtime > self.last_user_reg_mtime:
                self.last_user_reg_mtime = mtime
                appid = 0
                in_steam_section = False
                
                with open(user_reg_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('[Software\\Valve\\Steam]'):
                            in_steam_section = True
                        elif line.startswith('[') and in_steam_section:
                            break
                        elif in_steam_section and line.startswith('"RunningAppID"=dword:'):
                            hex_str = line.split(':')[-1]
                            appid = int(hex_str, 16)
                            break
                
                if appid != self.active_running_appid:
                    self.active_running_appid = appid
                    if appid > 0:
                        name = self.installed_games.get(appid, self.game_name_cache.get(appid, f"Game {appid}"))
                        self.active_running_name = name
                        self.resolve_game_name(appid)
                        
                        # Automatically select it and check
                        if self.app_state == STATE_DETECT:
                            self.root.after(0, lambda: self.set_selected_game(appid, name))
                    else:
                        self.active_running_name = ""
        except Exception as e:
            print(f"Error reading user.reg: {e}")

    def check_cef_logs(self):
        cef_log_path = os.path.join(self.steam_path, "logs/cef_log.txt")
        if not os.path.exists(cef_log_path):
            return
            
        try:
            size = os.path.getsize(cef_log_path)
            if size < self.cef_log_position:
                self.cef_log_position = 0
                
            if size > self.cef_log_position:
                with open(cef_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(self.cef_log_position)
                    lines = f.readlines()
                    self.cef_log_position = f.tell()
                    
                for line in reversed(lines):
                    match = re.search(r'store\.steampowered\.com/app/(\d+)(?:/([^/\s\'\"]+))?', line)
                    if match:
                        appid = int(match.group(1))
                        if appid in [228980]: # Skip Steamworks Common Redistributables
                            continue
                            
                        slug = match.group(2) if match.group(2) else ""
                        name = slug.replace('_', ' ').replace('-', ' ').title()
                        
                        if appid != self.last_detected_store_appid:
                            self.last_detected_store_appid = appid
                            self.last_detected_store_name = name if name else f"Game {appid}"
                            self.resolve_game_name(appid)
                            
                            # Auto select on main screen
                            if self.app_state == STATE_DETECT:
                                self.root.after(0, lambda: self.set_selected_game(appid, self.last_detected_store_name))
                            break
        except Exception as e:
            print(f"Error parsing cef logs: {e}")

    def check_webhelper_js_logs(self):
        js_log_path = os.path.join(self.steam_path, "logs/webhelper_js.txt")
        if not os.path.exists(js_log_path):
            return
            
        try:
            size = os.path.getsize(js_log_path)
            if size < self.js_log_position:
                self.js_log_position = 0
                
            if size > self.js_log_position:
                with open(js_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(self.js_log_position)
                    lines = f.readlines()
                    self.js_log_position = f.tell()
                    
                for line in reversed(lines):
                    match = re.search(r'store\.steampowered\.com/(?:agecheck/)?app/(\d+)(?:/([^/\s\'\":\?]+))?', line)
                    if match:
                        appid = int(match.group(1))
                        if appid in [228980]:
                            continue
                            
                        slug = match.group(2) if match.group(2) else ""
                        name = slug.replace('_', ' ').replace('-', ' ').title()
                        
                        if appid != self.last_detected_store_appid:
                            self.last_detected_store_appid = appid
                            self.last_detected_store_name = name if name else f"Game {appid}"
                            self.resolve_game_name(appid)
                            
                            if self.app_state == STATE_DETECT:
                                self.root.after(0, lambda: self.handle_new_store_game_detected(appid, self.last_detected_store_name))
                            break
        except Exception as e:
            print(f"Error parsing webhelper js logs: {e}")

    def check_steam_history(self):
        bottle_root = os.path.dirname(os.path.dirname(os.path.dirname(self.steam_path)))
        history_path = os.path.join(bottle_root, "drive_c/users/crossover/AppData/Local/Steam/htmlcache/Default/History")
        if not os.path.exists(history_path):
            return
            
        try:
            conn = sqlite3.connect(f"file:{history_path}?immutable=1", uri=True)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT url, title FROM urls "
                "WHERE url LIKE '%store.steampowered.com/app/%' OR url LIKE '%store.steampowered.com/cart%' "
                "ORDER BY last_visit_time DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                url = row[0]
                title = row[1]
                match = re.search(r'store\.steampowered\.com/(?:agecheck/)?app/(\d+)(?:/([^/]+))?', url)
                if match:
                    appid = int(match.group(1))
                    if appid not in [228980]:
                        slug = match.group(2) if match.group(2) else ""
                        name = slug.replace('_', ' ').replace('-', ' ').title()
                        if title and "on Steam" in title:
                            t_clean = title.split(" on Steam")[0]
                            if "Save " in t_clean and "%" in t_clean:
                                parts = t_clean.split(" on ")
                                if len(parts) > 1:
                                    t_clean = parts[-1]
                            name = t_clean.strip()
                        
                        if appid != self.last_detected_store_appid:
                            self.last_detected_store_appid = appid
                            self.last_detected_store_name = name if name else f"Game {appid}"
                            self.resolve_game_name(appid)
                            
                            if self.app_state == STATE_DETECT:
                                self.root.after(0, lambda: self.handle_new_store_game_detected(appid, self.last_detected_store_name))
            conn.close()
        except Exception as e:
            print(f"Error checking History in monitor loop: {e}")

    def handle_new_store_game_detected(self, appid, name):
        self.set_selected_game(appid, name)
        opts = self.get_scanned_dropdown_options()
        self.scanned_dropdown.update_options(opts)
        
        matching_opt = None
        for opt in opts:
            if f"App ID: {appid}" in opt:
                matching_opt = opt
                break
        if matching_opt:
            self.scanned_dropdown.set(matching_opt)

    def scan_steam_activity(self):
        detected_games = []
        seen_appids = set()

        # 1. Currently running game
        if self.active_running_appid > 0:
            name = self.installed_games.get(self.active_running_appid, self.game_name_cache.get(self.active_running_appid, self.active_running_name))
            detected_games.append((self.active_running_appid, name, "Running"))
            seen_appids.add(self.active_running_appid)

        # 2. CEF store views
        if self.last_detected_store_appid > 0 and self.last_detected_store_appid not in seen_appids:
            name = self.installed_games.get(self.last_detected_store_appid, self.game_name_cache.get(self.last_detected_store_appid, self.last_detected_store_name))
            detected_games.append((self.last_detected_store_appid, name, "Active Store Page"))
            seen_appids.add(self.last_detected_store_appid)

        # 3. Chromium History records
        bottle_root = os.path.dirname(os.path.dirname(os.path.dirname(self.steam_path)))
        history_path = os.path.join(bottle_root, "drive_c/users/crossover/AppData/Local/Steam/htmlcache/Default/History")
        if os.path.exists(history_path):
            try:
                conn = sqlite3.connect(f"file:{history_path}?immutable=1", uri=True)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT url, title FROM urls "
                    "WHERE url LIKE '%store.steampowered.com/app/%' OR url LIKE '%store.steampowered.com/cart%' "
                    "ORDER BY last_visit_time DESC LIMIT 15"
                )
                rows = cursor.fetchall()
                for r in rows:
                    url = r[0]
                    title = r[1]
                    match = re.search(r'store\.steampowered\.com/(?:agecheck/)?app/(\d+)(?:/([^/]+))?', url)
                    if match:
                        appid = int(match.group(1))
                        if appid in [228980]:
                            continue
                        if appid not in seen_appids:
                            slug = match.group(2) if match.group(2) else ""
                            name = slug.replace('_', ' ').replace('-', ' ').title()
                            if title and "on Steam" in title:
                                t_clean = title.split(" on Steam")[0]
                                if "Save " in t_clean and "%" in t_clean:
                                    parts = t_clean.split(" on ")
                                    if len(parts) > 1:
                                        t_clean = parts[-1]
                                name = t_clean.strip()
                            name = self.installed_games.get(appid, self.game_name_cache.get(appid, name if name else f"Game {appid}"))
                            detected_games.append((appid, name, "Store History"))
                            seen_appids.add(appid)
                conn.close()
            except Exception as e:
                print(f"Error scanning History: {e}")

        # 4. Library Games (ACF)
        for appid, name in self.installed_games.items():
            if appid not in seen_appids:
                detected_games.append((appid, name, "Installed"))
                seen_appids.add(appid)

        return detected_games

    def cleanup(self):
        self.running = False

if __name__ == "__main__":
    if not os.path.exists(DEFAULT_STEAM_PATH):
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning("Path Warning", f"Steam path not found at:\n{DEFAULT_STEAM_PATH}\n\nPlease select your Steam installation folder.")
        selected_dir = filedialog.askdirectory(title="Select Steam Installation Folder")
        if not selected_dir:
            sys.exit(1)
        DEFAULT_STEAM_PATH = selected_dir
        DEFAULT_SETTINGS_FILE = os.path.join(DEFAULT_STEAM_PATH, "millennium/plugins/tools/backend/data/settings.json")
        DEFAULT_API_FILE = os.path.join(DEFAULT_STEAM_PATH, "millennium/plugins/tools/backend/api.json")
        root.destroy()

    root = tk.Tk()
    app = LuaToolsHelperApp(root)
    
    def on_closing():
        app.cleanup()
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
