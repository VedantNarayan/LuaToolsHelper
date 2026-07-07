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

# State Constants
STATE_DETECT = 0
STATE_DOWNLOAD = 1
STATE_SUCCESS = 2
STATE_RESTART = 3
STATE_MANAGE = 4

# Globally cached images (to prevent garbage collection in Tkinter!)
TK_IMAGE_CACHE = {}

# Beautiful dark purple geometric placeholder (120x45) when app/capsule returns 404
BASE64_PLACEHOLDER = 'R0lGODdheAAtAIUAAFim/0VHWjAxTS8wTC4vSy4vSi4uSS0uSS0uSCwtRywtRissRissRSsrRCorRCoqQykqQikqQSgpQSgpQCgoPycoPicnPiYnPSYmPCYmOyUmOyUlOiQlOSQkOSMkOCMjNyMjNiIiNiIiNSEiNCEhMyAhMyAgMiAgMR8fMB4eLx4eLgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACwAAAAAeAAtAEAI/wADCBxIsKDBgwgTKlzIsKHDhwFISJxIsaLFixgzatzIsaPHjgI5iBxJsqTJkyhTmgQAQOVIli5jypwpkILNmzhz6tzJsydOljcBqBhKlCiAoEd9Kl3KlIJABlCjSp1KtarVq1gZsNzKciqArGDDhhVIoKzZs2jTql3Ltq3bt3DjwhWIoq7du3jz6t3Lt6/fv4ADAxYIorDhw4gTK17MGDEAx1xZNp5MuTJjgRgya97MubPnz6A3s9QstGhRAKRRh17NujUGgRBiy55Nu7bt27hrs8wtezfv38CBC0RAvLjx48iTK1/OvLnz59CfQ5xOtbr16wtTaN/Ovbv37+DDi/8fT768+fICTahfz769+/fw48ufT7++/foCRejfz7+///8ABijgfiwNaOCBCAIokAcMNujggxBGKOGED0bGUoUWUqjhhhw2KJAGIIYo4ogklmjiiSOyJGJpRq0IAIowxihjiAJZYOONOOao44489mhBZDeyaJoKAATJlY9IJpmkQBI06eSTUEYp5ZRUQsnSk0ISiSUAVXbp5ZdOCuTAmGSWaeaZaKapppkWAsCmhWvGKeecZAqkwJ145qnnnnz26eefebIE6KCEFsqnQAYkquiijDbq6KOQRirppJRWSqlAA2Sq6aacdurpp6CGKuqopJZKqkBDpqrqqqy26uqrsMb/+ipdgtVq66245vqXQCf06uuvwAYr7LDEFmvsscgmi6xAJTTr7LPQRivttNRWa+212GaLrUAjdOvtt+CGK+645JbrLUvmpqvuuuMKFMK78MYr77z01mvvvfCyhO++/PZbr0AfBCzwwAQXbPDBCA+8VcBtcsVwwhBHLPHAAnVg8cUYZ6zxxhx3rDFXHYPs8cgkl3yxQBukrPLKLLfs8ssws7zVypHRzFLMOOess8oCZeDzz0AHLfTQRBcN9FY/ZzkUAEmzZPTTUEfts0AXVG311VhnrfXWXF8QmdVKGwU2AF2XbfbZVQtUwdpst+3223DHLXfbLLEd9tJ2czX33nzz5S3QBIAHLvjghBdu+OGCbxV42AAszhLikEcuOeACRWD55ZhnrvnmnHee+VaYRxY6S56Xbvrplwv0wOqst+7667DHLvvrXMle++y456476wI14PvvwAcv/PDEFy88AL43vFXyLBnv/PPQ+y7QAtRXb/312Gev/fbcW89S9+CHL372AiVg/vnop6/++uy37z76LL0v//z0ry/QAfjnr//+/Pfv//8ADKAAB0jAAQqkAAhMoAIXyMAGOvCBEIygBCdIwQliylQYzKAGN8jBUQlEACAMoQhHSMISmvCEKEyhClfIwhUGICAAOw=='

def get_game_image(appid):
    """Downloads game capsule from Steam CDN, converts to GIF using sips, and returns the path to the GIF."""
    cache_dir = os.path.join(DEFAULT_TEMP_DIR, "image_cache")
    try:
        os.makedirs(cache_dir, exist_ok=True)
    except Exception:
        pass
        
    gif_path = os.path.join(cache_dir, f"{appid}.gif")
    if os.path.exists(gif_path):
        return gif_path
        
    jpg_path = os.path.join(cache_dir, f"{appid}.jpg")
    if not os.path.exists(jpg_path):
        url = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/capsule_184x69.jpg"
        download_success = False
        import uuid
        temp_jpg = os.path.join(cache_dir, f"{appid}_{uuid.uuid4().hex}.jpg")
        
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            req.add_header('Accept', 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8')
            req.add_header('Accept-Language', 'en-US,en;q=0.9')
            
            with urllib.request.urlopen(req, timeout=3) as response:
                with open(temp_jpg, "wb") as f:
                    f.write(response.read())
            download_success = True
        except Exception:
            pass
            
        # Fallback to Steam App Details API for hashed/seasonal app URLs
        if not download_success:
            try:
                api_url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
                api_req = urllib.request.Request(api_url)
                api_req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
                with urllib.request.urlopen(api_req, timeout=3) as api_res:
                    res_data = json.loads(api_res.read().decode('utf-8', errors='ignore'))
                    if res_data and res_data.get(str(appid), {}).get("success"):
                        app_info = res_data[str(appid)]["data"]
                        img_url = app_info.get("capsule_imagev5") or app_info.get("capsule_image") or app_info.get("header_image")
                        if img_url:
                            req_fallback = urllib.request.Request(img_url)
                            req_fallback.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
                            with urllib.request.urlopen(req_fallback, timeout=3) as fb_res:
                                with open(temp_jpg, "wb") as f:
                                    f.write(fb_res.read())
                                download_success = True
            except Exception as e:
                print(f"Fallback fetch failed for {appid}: {e}")
                
        if download_success and os.path.exists(temp_jpg):
            try:
                os.rename(temp_jpg, jpg_path)
            except Exception:
                pass
        else:
            if os.path.exists(temp_jpg):
                try:
                    os.remove(temp_jpg)
                except Exception:
                    pass
            return None
            
    # Convert to GIF using sips
    try:
        import subprocess
        subprocess.run(["sips", "-s", "format", "gif", jpg_path, "--out", gif_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if os.path.exists(jpg_path):
            try:
                os.remove(jpg_path)
            except Exception:
                pass
                
        return gif_path if os.path.exists(gif_path) else None
    except Exception as e:
        print(f"Error converting to GIF for {appid}: {e}")
        return None

def get_game_image_thumbnail(appid):
    """Downloads game capsule from Steam CDN, resizes to 120x45 in GIF format using sips, and returns the path."""
    cache_dir = os.path.join(DEFAULT_TEMP_DIR, "image_cache")
    try:
        os.makedirs(cache_dir, exist_ok=True)
    except Exception:
        pass
        
    gif_path = os.path.join(cache_dir, f"{appid}_thumb.gif")
    if os.path.exists(gif_path):
        return gif_path
        
    full_gif = get_game_image(appid)
    if not full_gif or not os.path.exists(full_gif):
        return None
        
    # Resize and convert to GIF using sips
    try:
        import subprocess
        subprocess.run(["sips", "-s", "format", "gif", "-z", "45", "120", full_gif, "--out", gif_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return gif_path if os.path.exists(gif_path) else None
    except Exception as e:
        print(f"Error converting thumb for {appid}: {e}")
        return None


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
        
        # Pack scrollbar first to avoid overlapping with canvas
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)


# Sidebar Button for Modern UI layout
class SidebarButton(tk.Frame):
    def __init__(self, parent, text, icon, command, active=False):
        super().__init__(parent, bg=CAT_CRUST, height=45)
        self.command = command
        self.active = active
        self.pack_propagate(False)
        
        # Indicator strip on the left
        self.indicator = tk.Frame(self, bg=CAT_BLUE if active else CAT_CRUST, width=4)
        self.indicator.pack(side=tk.LEFT, fill=tk.Y)
        
        self.lbl = tk.Label(
            self,
            text=f"  {icon}   {text}",
            bg=CAT_MANTLE if active else CAT_CRUST,
            fg=CAT_TEXT if active else CAT_SUBTEXT0,
            font=("Helvetica", 11, "bold" if active else "normal"),
            anchor="w",
            cursor="hand2"
        )
        self.lbl.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.lbl.bind("<Enter>", self.on_enter)
        self.lbl.bind("<Leave>", self.on_leave)
        self.lbl.bind("<Button-1>", lambda e: self.on_click())
        
    def on_enter(self, e):
        if not self.active:
            self.lbl.configure(bg="#1a202c", fg=CAT_TEXT)
            
    def on_leave(self, e):
        if not self.active:
            self.lbl.configure(bg=CAT_CRUST, fg=CAT_SUBTEXT0)
            
    def on_click(self):
        self.command()
        
    def set_active(self, active):
        self.active = active
        self.indicator.configure(bg=CAT_BLUE if active else CAT_CRUST)
        self.lbl.configure(
            bg=CAT_MANTLE if active else CAT_CRUST,
            fg=CAT_TEXT if active else CAT_SUBTEXT0,
            font=("Helvetica", 11, "bold" if active else "normal")
        )


class LuaToolsHelperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LuaTools macOS Helper")
        self.root.geometry("900x580")
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
        self.name_labels = {} # appid -> label reference to update names without flickering
        self.last_auto_selected_appid = 0
        
        # Scanner states
        self.active_running_appid = 0
        self.active_running_name = ""
        self.last_detected_store_appid = 0
        self.last_detected_store_name = ""
        
        self.last_user_reg_mtime = 0
        self.cef_log_position = 0
        self.js_log_position = 0
        
        # Dynamic tailing of CEF logs to ignore old sessions (supports cef_log.txt and cef.log)
        try:
            log_path = os.path.join(self.steam_path, "logs/cef_log.txt")
            if not os.path.exists(log_path):
                log_path = os.path.join(self.steam_path, "logs/cef.log")
            if os.path.exists(log_path):
                self.cef_log_position = os.path.getsize(log_path)
        except Exception:
            self.cef_log_position = 0
            
        # Dynamic tailing of JS logs (webhelper_js.txt)
        try:
            js_log_path = os.path.join(self.steam_path, "logs/webhelper_js.txt")
            if os.path.exists(js_log_path):
                self.js_log_position = os.path.getsize(js_log_path)
        except Exception:
            self.js_log_position = 0
            
        # Animation & Flow state
        self.running = True
        self.pulse_phase = False
        self.current_tab = "dashboard"
        self.app_state = STATE_DETECT
        self.patches_map = {}
        
        # Configuration setup
        self.load_settings()
        self.load_apis()
        self.scan_installed_games()
        
        # ── SIDEBAR NAVIGATION PANEL ──
        self.sidebar_frame = tk.Frame(self.root, bg=CAT_CRUST, width=200)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_frame.pack_propagate(False)
        
        # Sidebar Logo & Title
        logo_container = tk.Frame(self.sidebar_frame, bg=CAT_CRUST, height=70)
        logo_container.pack(fill=tk.X, pady=(20, 10))
        logo_container.pack_propagate(False)
        
        logo_lbl = tk.Label(logo_container, text="🔧", font=("Helvetica", 22), fg=CAT_BLUE, bg=CAT_CRUST)
        logo_lbl.pack(side=tk.LEFT, padx=(20, 5))
        
        title_lbl = tk.Label(logo_container, text="LuaTools Helper", font=("Helvetica", 13, "bold"), fg=CAT_TEXT, bg=CAT_CRUST)
        title_lbl.pack(side=tk.LEFT, pady=10)
        
        # Sidebar Buttons Group
        self.nav_buttons = {}
        
        self.nav_buttons["dashboard"] = SidebarButton(self.sidebar_frame, "Dashboard", "🔍", lambda: self.switch_tab("dashboard"), active=True)
        self.nav_buttons["dashboard"].pack(fill=tk.X, pady=2)
        
        self.nav_buttons["patches"] = SidebarButton(self.sidebar_frame, "Manage Patches", "📦", lambda: self.switch_tab("patches"))
        self.nav_buttons["patches"].pack(fill=tk.X, pady=2)
        
        self.nav_buttons["settings"] = SidebarButton(self.sidebar_frame, "Settings", "⚙️", lambda: self.switch_tab("settings"))
        self.nav_buttons["settings"].pack(fill=tk.X, pady=2)
        
        self.nav_buttons["apis"] = SidebarButton(self.sidebar_frame, "API Catalog", "🌐", lambda: self.switch_tab("apis"))
        self.nav_buttons["apis"].pack(fill=tk.X, pady=2)
        
        # ── CONTENT MAIN PANEL ──
        self.content_frame = tk.Frame(self.root, bg=CAT_BASE)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        # ── PROGRESS / MODAL OVERLAY FRAME ──
        self.overlay_frame = tk.Frame(self.root, bg=CAT_CRUST, highlightbackground=CAT_SURFACE0, highlightthickness=1)
        self.overlay_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=500, height=340)
        self.overlay_frame.place_forget() # Initially hidden
        
        # Render initial screen
        self.switch_tab("dashboard")
        
        # Launch background monitors
        self.animate_pulse_loop()
        self.monitor_thread = threading.Thread(target=self.steam_monitor_loop, daemon=True)
        self.monitor_thread.start()

    def load_game_image_async(self, appid, callback):
        if appid in TK_IMAGE_CACHE:
            callback(TK_IMAGE_CACHE[appid])
            return
            
        def worker():
            gif_path = get_game_image(appid)
            self.root.after(0, lambda: self.create_and_cache_photoimage(appid, gif_path, callback))
        threading.Thread(target=worker, daemon=True).start()

    def load_game_image_thumb_async(self, appid, callback):
        cache_key = f"{appid}_thumb"
        if cache_key in TK_IMAGE_CACHE:
            callback(TK_IMAGE_CACHE[cache_key])
            return
            
        def worker():
            gif_path = get_game_image_thumbnail(appid)
            self.root.after(0, lambda: self.create_and_cache_photoimage(cache_key, gif_path, callback))
        threading.Thread(target=worker, daemon=True).start()

    def create_and_cache_photoimage(self, cache_key, gif_path, callback):
        try:
            if gif_path and os.path.exists(gif_path):
                img = tk.PhotoImage(file=gif_path)
            else:
                img = tk.PhotoImage(data=BASE64_PLACEHOLDER)
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

    def save_apis(self):
        try:
            os.makedirs(os.path.dirname(DEFAULT_API_FILE), exist_ok=True)
            with open(DEFAULT_API_FILE, "w") as f:
                json.dump({"api_list": self.apis}, f, indent=4)
            return True
        except Exception as e:
            print(f"Failed to save apis: {e}")
            return False

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

    # ── TAB SWITCHING SYSTEM ──
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def switch_tab(self, tab_name):
        self.current_tab = tab_name
        
        # Update sidebar button states
        for name, btn in self.nav_buttons.items():
            btn.set_active(name == tab_name)
            
        self.clear_content()
        self.overlay_frame.place_forget() # Hide progress overlays
        
        if tab_name == "dashboard":
            self.render_dashboard()
        elif tab_name == "patches":
            self.render_patches()
        elif tab_name == "settings":
            self.render_settings()
        elif tab_name == "apis":
            self.render_apis()

    # ── TAB 1: DASHBOARD VIEW ──
    def render_dashboard(self):
        # Header Status Pulse Badge
        status_bar = tk.Frame(self.content_frame, bg=CAT_CRUST, highlightbackground=CAT_SURFACE0, highlightthickness=1, bd=0, height=40)
        status_bar.pack(fill=tk.X, pady=(0, 20))
        status_bar.pack_propagate(False)
        
        self.pulse_canvas = tk.Canvas(status_bar, width=12, height=12, bg=CAT_CRUST, highlightthickness=0)
        self.pulse_canvas.pack(side=tk.LEFT, padx=(15, 8))
        self.pulse_circle = self.pulse_canvas.create_oval(2, 2, 10, 10, fill="#2a4a6b", outline="")
        
        self.status_lbl = tk.Label(status_bar, text="Steam Activity Monitor: Waiting for pages...", font=("Helvetica", 11, "bold"), fg=CAT_TEXT, bg=CAT_CRUST)
        self.status_lbl.pack(side=tk.LEFT)

        # Scanned Cart & Store Dropdown section with prominent Refresh button
        scanned_header = tk.Frame(self.content_frame, bg=CAT_BASE)
        scanned_header.pack(fill=tk.X, pady=(5, 3))
        
        scanned_lbl = tk.Label(scanned_header, text="Recently Viewed & Cart Games:", font=("Helvetica", 11, "bold"), fg=CAT_SUBTEXT0, bg=CAT_BASE)
        scanned_lbl.pack(side=tk.LEFT)
        
        dropdown_row = tk.Frame(self.content_frame, bg=CAT_BASE)
        dropdown_row.pack(fill=tk.X, pady=5)
        
        detected_options = self.get_scanned_dropdown_options()
        self.scanned_dropdown = TkDropdown(dropdown_row, detected_options, self.on_dropdown_game_selected)
        self.scanned_dropdown.frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Highly visible solid blue refresh button
        self.btn_refresh_dashboard = LabelButton(
            dropdown_row, 
            text="🔄 Scan Activity", 
            command=self.manual_refresh_dashboard, 
            bg=CAT_BLUE, 
            fg="#0e1621",
            hover_bg="#8ad4f8",
            active_bg="#4fc3f7",
            font=("Helvetica", 10, "bold"),
            pady=6,
            padx=15
        )
        self.btn_refresh_dashboard.pack(side=tk.RIGHT)
        
        # Display Area Card (Glassmorphic)
        self.game_card = tk.Frame(self.content_frame, bg=CAT_MANTLE, highlightbackground=CAT_SURFACE0, highlightthickness=1, bd=0, height=180)
        self.game_card.pack(fill=tk.X, pady=25)
        self.game_card.pack_propagate(False)
        
        # Left: large image thumbnail wrapper in pixel container
        img_container = tk.Frame(self.game_card, bg=CAT_MANTLE, width=184, height=69)
        img_container.pack(side=tk.LEFT, padx=20, pady=20)
        img_container.pack_propagate(False)
        
        self.game_card_img = tk.Label(img_container, bg=CAT_MANTLE)
        self.game_card_img.pack(fill=tk.BOTH, expand=True)
        
        # Right: title and details
        self.game_card_info = tk.Frame(self.game_card, bg=CAT_MANTLE)
        self.game_card_info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=20, padx=10)
        
        self.game_card_title = tk.Label(self.game_card_info, text="No Steam Store Game Selected", font=("Helvetica", 15, "bold"), fg=CAT_TEXT, bg=CAT_MANTLE, anchor="w")
        self.game_card_title.pack(anchor=tk.W, pady=(15, 4))
        
        self.game_card_sub = tk.Label(self.game_card_info, text="Select a game from the dropdown or browse store pages in Steam", font=("Helvetica", 11), fg=CAT_SUBTEXT0, bg=CAT_MANTLE, anchor="w")
        self.game_card_sub.pack(anchor=tk.W, pady=2)
        
        # Action Buttons frame
        btn_frame = tk.Frame(self.content_frame, bg=CAT_BASE)
        btn_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.btn_add = LabelButton(
            btn_frame, 
            text="Add via LuaTools", 
            command=self.on_add_clicked,
            bg=CAT_BLUE,
            fg="#0e1621",
            pady=10
        )
        self.btn_add.pack(fill=tk.X)
        self.btn_add.configure_state("disabled")
        
        # Initialize selection
        latest_appid = 0
        match = re.search(r'App ID: (\d+)', detected_options[0])
        if match:
            latest_appid = int(match.group(1))
        self.last_auto_selected_appid = latest_appid
        
        self.on_dropdown_game_selected(detected_options[0])

    def set_selected_game(self, appid, name):
        if hasattr(self, 'selected_appid') and self.selected_appid == appid:
            # Prevent duplicate loader thread spawns for the same selected game
            return
            
        self.selected_appid = appid
        self.selected_name = name
        
        if not hasattr(self, 'game_card_title'):
            return
            
        if appid > 0:
            self.game_card_title.configure(text=name, fg=CAT_TEXT)
            self.game_card_sub.configure(text=f"App ID: {appid} | Ready to download patch files", fg=CAT_SUBTEXT0)
            self.btn_add.configure_state("normal")
            
            # Load and display image
            self.game_card_img.configure(image="")
            self.load_game_image_async(appid, lambda img: self.game_card_img.configure(image=img) if self.game_card_img.winfo_exists() else None)
        else:
            self.game_card_title.configure(text="No Steam Store Game Selected", fg=CAT_SUBTEXT0)
            self.game_card_sub.configure(text="Select a game from the dropdown or browse store pages in Steam", fg=CAT_SUBTEXT0)
            self.btn_add.configure_state("disabled")
            self.game_card_img.configure(image="")

    def manual_refresh_dashboard(self):
        # Force clear all cached timestamps to trigger a true hard sync
        self.last_user_reg_mtime = 0
        self.last_detected_store_appid = 0
        self.last_detected_store_name = ""
        self.last_auto_selected_appid = 0
        
        self.check_cef_logs()
        self.check_history_db()
        
        # Explicitly force UI rebuild and dropdown sync
        self.refresh_lists_and_dropdown()
        messagebox.showinfo("Refreshed", "Steam activity log and store history scanned successfully!")

    def bind_scroll_recursive(self, widget, handler):
        widget.bind("<MouseWheel>", handler)
        widget.bind("<Button-4>", handler)
        widget.bind("<Button-5>", handler)
        for child in widget.winfo_children():
            self.bind_scroll_recursive(child, handler)

    def _on_patches_mousewheel(self, event):
        try:
            delta = event.delta
            if sys.platform == "darwin":
                # Prevent decimal rounding truncation (floats under 1.0 freezing the canvas)
                import math
                if delta != 0:
                    amount = -int(math.copysign(max(1, abs(delta * 2.0)), delta))
                    self.scroll_frame.canvas.yview_scroll(amount, "units")
            else:
                if event.num == 4:
                    self.scroll_frame.canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.scroll_frame.canvas.yview_scroll(1, "units")
                else:
                    self.scroll_frame.canvas.yview_scroll(int(-1 * (delta / 120)), "units")
        except Exception:
            pass

    def _on_apis_mousewheel(self, event):
        try:
            delta = event.delta
            if sys.platform == "darwin":
                import math
                if delta != 0:
                    amount = -int(math.copysign(max(1, abs(delta * 2.0)), delta))
                    self.apis_scroll_frame.canvas.yview_scroll(amount, "units")
            else:
                if event.num == 4:
                    self.apis_scroll_frame.canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.apis_scroll_frame.canvas.yview_scroll(1, "units")
                else:
                    self.apis_scroll_frame.canvas.yview_scroll(int(-1 * (delta / 120)), "units")
        except Exception:
            pass

    # ── TAB 2: MANAGE PATCHES VIEW ──
    def render_patches(self):
        title_frame = tk.Frame(self.content_frame, bg=CAT_BASE)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_lbl = tk.Label(title_frame, text="Manage Installed Patches", font=("Helvetica", 14, "bold"), fg=CAT_BLUE, bg=CAT_BASE)
        title_lbl.pack(side=tk.LEFT)
        
        # Highly visible solid blue refresh button
        btn_refresh = LabelButton(
            title_frame, 
            text="🔄 Refresh List", 
            command=self.refresh_installed_list, 
            bg=CAT_BLUE, 
            fg="#0e1621",
            hover_bg="#8ad4f8",
            active_bg="#4fc3f7",
            font=("Helvetica", 9, "bold"),
            pady=4,
            padx=12
        )
        btn_refresh.pack(side=tk.RIGHT)
        
        list_container = tk.Frame(self.content_frame, bg=CAT_MANTLE, highlightbackground=CAT_SURFACE0, highlightthickness=1, bd=0)
        list_container.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.scroll_frame = ScrollableFrame(list_container, bg=CAT_MANTLE)
        self.scroll_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        self.refresh_installed_list()

    def get_parent_id(self, appid_val):
        """Finds the main parent game App ID for a given depot/manifest App ID."""
        # 1. Collect known main App IDs from settings and directories
        known_mains = set()
        for appid in self.installed_games:
            known_mains.add(int(appid))
            
        st_plug_dir = os.path.join(self.steam_path, "config/stplug-in")
        if os.path.exists(st_plug_dir):
            try:
                for file in os.listdir(st_plug_dir):
                    if file.endswith(".lua") or file.endswith(".lua.disabled"):
                        clean_id = file.replace(".lua.disabled", "").replace(".lua", "")
                        if clean_id.isdigit():
                            known_mains.add(int(clean_id))
            except Exception:
                pass
                
        # 2. Check if this ID is already a main
        if appid_val in known_mains:
            return appid_val
            
        # Check nearby IDs (within a diff of 10)
        for diff in range(1, 10):
            if (appid_val - diff) in known_mains:
                return appid_val - diff
                
        # Fallback: Group to nearest multiple of 10
        return (appid_val // 10) * 10

    def refresh_installed_list(self):
        if not hasattr(self, 'scroll_frame'):
            return
            
        self.name_labels.clear()
        
        for widget in self.scroll_frame.scrollable_frame.winfo_children():
            widget.destroy()
            
        self.patches_map = {}
        
        # Gather all script files
        st_plug_dir = os.path.join(self.steam_path, "config/stplug-in")
        lua_files = []
        if os.path.exists(st_plug_dir):
            try:
                for file in os.listdir(st_plug_dir):
                    if file.endswith(".lua") or file.endswith(".lua.disabled"):
                        lua_files.append(file)
            except Exception as e:
                print(f"Error scanning stplug-in: {e}")
                
        # Gather all manifest files
        depot_cache = os.path.join(self.steam_path, "depotcache")
        manifest_files = []
        if os.path.exists(depot_cache):
            try:
                for file in os.listdir(depot_cache):
                    if file.endswith(".manifest") or file.endswith(".manifest.disabled"):
                        manifest_files.append(file)
            except Exception as e:
                print(f"Error scanning depotcache: {e}")
                
        # Group files under their parent game App ID
        grouped = {} # parent_id -> {"has_lua": bool, "lua_files": [], "manifest_files": []}
        
        for file in lua_files:
            clean_id = file.replace(".lua.disabled", "").replace(".lua", "")
            if clean_id.isdigit():
                appid = int(clean_id)
                parent = self.get_parent_id(appid)
                if parent not in grouped:
                    grouped[parent] = {"has_lua": True, "lua_files": [], "manifest_files": []}
                grouped[parent]["lua_files"].append(file)
                grouped[parent]["has_lua"] = True
                
        for file in manifest_files:
            parts = file.split("_")
            if parts and parts[0].isdigit():
                appid = int(parts[0])
                parent = self.get_parent_id(appid)
                if parent not in grouped:
                    grouped[parent] = {"has_lua": False, "lua_files": [], "manifest_files": []}
                grouped[parent]["manifest_files"].append(file)

        if not grouped:
            empty_lbl = tk.Label(self.scroll_frame.scrollable_frame, text="No patches installed.", font=("Helvetica", 11), fg=CAT_SUBTEXT0, bg=CAT_MANTLE)
            empty_lbl.pack(pady=40)
            return

        idx = 0
        for parent_id in sorted(grouped.keys()):
            item = grouped[parent_id]
            game_name = self.installed_games.get(parent_id, self.game_name_cache.get(parent_id, f"Game {parent_id}"))
            
            # Determine overall active status
            is_active = False
            if item["lua_files"]:
                for lf in item["lua_files"]:
                    if lf.endswith(".lua"):
                        is_active = True
            else:
                for mf in item["manifest_files"]:
                    if mf.endswith(".manifest"):
                        is_active = True
                        
            status_indicator = "🟢 Active" if is_active else "⚪ Disabled"
            if not item["has_lua"]:
                status_indicator += " (Manifest)"
            
            # Custom Card Container
            card = tk.Frame(self.scroll_frame.scrollable_frame, bg=CAT_BASE, highlightbackground=CAT_SURFACE0, highlightthickness=1, bd=0)
            card.pack(fill=tk.X, pady=5, padx=5)
            
            # Left: Game Capsule Image pixel wrapper (120x45)
            img_container = tk.Frame(card, bg=CAT_BASE, width=120, height=45)
            img_container.pack(side=tk.LEFT, padx=10, pady=8)
            img_container.pack_propagate(False)
            
            img_lbl = tk.Label(img_container, bg=CAT_BASE)
            img_lbl.pack(fill=tk.BOTH, expand=True)
            
            # Load the thumbnail image asynchronously
            self.load_game_image_thumb_async(parent_id, lambda img, l=img_lbl: l.configure(image=img) if l.winfo_exists() else None)
            
            # Center: Title & App ID
            info_frame = tk.Frame(card, bg=CAT_BASE)
            info_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=10)
            
            name_lbl = tk.Label(info_frame, text=game_name, font=("Helvetica", 11, "bold"), fg=CAT_TEXT, bg=CAT_BASE, anchor="w")
            name_lbl.pack(anchor=tk.W, pady=(5, 0))
            self.name_labels[parent_id] = name_lbl
            
            status_color = CAT_GREEN if is_active else CAT_SUBTEXT0
            sub_lbl = tk.Label(info_frame, text=f"App ID: {parent_id} | {status_indicator}", font=("Helvetica", 9), fg=status_color, bg=CAT_BASE, anchor="w")
            sub_lbl.pack(anchor=tk.W, pady=(0, 5))
            
            # Right: Action Buttons
            btn_frame = tk.Frame(card, bg=CAT_BASE)
            btn_frame.pack(side=tk.RIGHT, padx=10)
            
            # Action hooks
            toggle_action = lambda p=parent_id, act=is_active: self.toggle_patch_direct(p, act)
            delete_action = lambda p=parent_id: self.delete_patch_direct(p)
            
            btn_toggle = LabelButton(btn_frame, text="Toggle", command=toggle_action, bg=CAT_SURFACE0, fg=CAT_TEXT, font=("Helvetica", 9, "bold"), pady=3, padx=6, outlined=True)
            btn_toggle.pack(side=tk.LEFT, padx=3)
            
            btn_delete = LabelButton(btn_frame, text="Delete", command=delete_action, bg=CAT_RED, fg="#ffffff", font=("Helvetica", 9, "bold"), pady=3, padx=6)
            btn_delete.pack(side=tk.LEFT, padx=3)
            
            self.patches_map[idx] = (str(parent_id), "Active" if is_active else "Disabled")
            idx += 1
            
            if game_name.startswith("Game "):
                self.resolve_game_name(parent_id)
                
        # Recursively bind scroll wheel to the canvas and all dynamically generated child widgets
        self.bind_scroll_recursive(self.scroll_frame, self._on_patches_mousewheel)

    def toggle_patch_direct(self, parent_id, current_active_state):
        st_plug_dir = os.path.join(self.steam_path, "config/stplug-in")
        depot_cache = os.path.join(self.steam_path, "depotcache")
        
        # If it was active, we want to disable it. If disabled, enable it.
        target_enable = not current_active_state
        
        # 1. Toggle Lua files
        if os.path.exists(st_plug_dir):
            try:
                for file in os.listdir(st_plug_dir):
                    if file.endswith(".lua") or file.endswith(".lua.disabled"):
                        clean_id = file.replace(".lua.disabled", "").replace(".lua", "")
                        if clean_id.isdigit():
                            child_id = int(clean_id)
                            if self.get_parent_id(child_id) == parent_id:
                                src = os.path.join(st_plug_dir, file)
                                if not target_enable:
                                    # Disable
                                    if file.endswith(".lua"):
                                        dst = os.path.join(st_plug_dir, f"{clean_id}.lua.disabled")
                                        os.rename(src, dst)
                                else:
                                    # Enable
                                    if file.endswith(".lua.disabled"):
                                        dst = os.path.join(st_plug_dir, f"{clean_id}.lua")
                                        os.rename(src, dst)
            except Exception as e:
                print(f"Error toggling lua files: {e}")
                
        # 2. Toggle Manifest files
        if os.path.exists(depot_cache):
            try:
                for file in os.listdir(depot_cache):
                    if file.endswith(".manifest") or file.endswith(".manifest.disabled"):
                        parts = file.split("_")
                        if parts and parts[0].isdigit():
                            child_id = int(parts[0])
                            if self.get_parent_id(child_id) == parent_id:
                                src = os.path.join(depot_cache, file)
                                if not target_enable:
                                    # Disable
                                    if file.endswith(".manifest"):
                                        dst = os.path.join(depot_cache, f"{file}.disabled")
                                        os.rename(src, dst)
                                else:
                                    # Enable
                                    if file.endswith(".manifest.disabled"):
                                        clean_name = file.replace(".manifest.disabled", ".manifest")
                                        dst = os.path.join(depot_cache, clean_name)
                                        os.rename(src, dst)
            except Exception as e:
                print(f"Error toggling manifests: {e}")
                
        self.refresh_installed_list()

    def delete_patch_direct(self, parent_id):
        confirm = messagebox.askyesno("Confirm", f"Are you sure you want to remove all files and manifests for App ID {parent_id}?")
        if not confirm:
            return

        st_plug_dir = os.path.join(self.steam_path, "config/stplug-in")
        depot_cache = os.path.join(self.steam_path, "depotcache")
        
        # 1. Delete Lua files
        if os.path.exists(st_plug_dir):
            try:
                for file in os.listdir(st_plug_dir):
                    if file.endswith(".lua") or file.endswith(".lua.disabled"):
                        clean_id = file.replace(".lua.disabled", "").replace(".lua", "")
                        if clean_id.isdigit():
                            child_id = int(clean_id)
                            if self.get_parent_id(child_id) == parent_id:
                                try:
                                    os.remove(os.path.join(st_plug_dir, file))
                                except Exception:
                                    pass
            except Exception:
                pass
                
        # 2. Delete Manifest files
        if os.path.exists(depot_cache):
            try:
                for file in os.listdir(depot_cache):
                    if file.endswith(".manifest") or file.endswith(".manifest.disabled"):
                        parts = file.split("_")
                        if parts and parts[0].isdigit():
                            child_id = int(parts[0])
                            if self.get_parent_id(child_id) == parent_id:
                                try:
                                    os.remove(os.path.join(depot_cache, file))
                                except Exception:
                                    pass
            except Exception:
                pass
                
        self.refresh_installed_list()
        messagebox.showinfo("Deleted", f"Successfully removed all files for App ID {parent_id}.")

    # ── TAB 3: SETTINGS VIEW ──
    def render_settings(self):
        title_lbl = tk.Label(self.content_frame, text="Application Settings", font=("Helvetica", 14, "bold"), fg=CAT_BLUE, bg=CAT_BASE)
        title_lbl.pack(anchor=tk.W, pady=(0, 15))
        
        settings_card = tk.Frame(self.content_frame, bg=CAT_MANTLE, highlightbackground=CAT_SURFACE0, highlightthickness=1, bd=0)
        settings_card.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.setting_steam_ent = self.create_adv_entry(settings_card, "CrossOver Steam Path", self.steam_path, self.browse_steam_path)
        self.setting_temp_ent = self.create_adv_entry(settings_card, "Temp Download Path", self.temp_dir, self.browse_temp_path)
        self.setting_key_ent = self.create_adv_entry(settings_card, "Morrenus API Key (Optional)", self.morrenus_key, None)
        
        save_btn = LabelButton(settings_card, text="Save Settings", command=self.apply_and_save_settings, bg=CAT_BLUE, fg="#0e1621", font=("Helvetica", 10, "bold"), pady=8)
        save_btn.pack(anchor=tk.E, padx=15, pady=20)

    def create_adv_entry(self, parent, label_text, value, browse_cmd):
        lbl = tk.Label(parent, text=label_text, font=("Helvetica", 10, "bold"), fg=CAT_SUBTEXT0, bg=CAT_MANTLE)
        lbl.pack(anchor=tk.W, padx=15, pady=(15, 2))
        
        row = tk.Frame(parent, bg=CAT_MANTLE)
        row.pack(fill=tk.X, padx=15)
        
        entry_bg = tk.Frame(row, bg=CAT_SURFACE0, highlightbackground=CAT_SURFACE1, highlightthickness=1, bd=0)
        entry_bg.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ent = tk.Entry(entry_bg, bg=CAT_MANTLE, fg=CAT_TEXT, insertbackground=CAT_TEXT, relief="flat", bd=0, font=("Helvetica", 11))
        ent.pack(fill=tk.X, padx=6, pady=5)
        ent.insert(0, value)
        
        if browse_cmd:
            btn_br = LabelButton(row, text="Browse...", command=browse_cmd, bg=CAT_SURFACE0, fg=CAT_TEXT, font=("Helvetica", 10, "bold"), pady=5, padx=10, outlined=True)
            btn_br.pack(side=tk.RIGHT, padx=(10, 0))
            
        return ent

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
            messagebox.showinfo("Success", "Configuration saved and game library rescanned!")

    # ── TAB 4: API CATALOG VIEW ──
    def render_apis(self):
        title_lbl = tk.Label(self.content_frame, text="API Catalog Providers", font=("Helvetica", 14, "bold"), fg=CAT_BLUE, bg=CAT_BASE)
        title_lbl.pack(anchor=tk.W, pady=(0, 15))
        
        scroll_container = tk.Frame(self.content_frame, bg=CAT_BASE)
        scroll_container.pack(fill=tk.BOTH, expand=True)
        
        scr = ScrollableFrame(scroll_container, bg=CAT_BASE)
        scr.pack(fill=tk.BOTH, expand=True)
        
        for idx, api in enumerate(self.apis):
            name = api["name"]
            url = api["url"]
            enabled = api.get("enabled", True)
            
            # Check if API Key is required
            is_key_required = ("<moapikey>" in url)
            has_key = bool(self.morrenus_key.strip())
            
            card = tk.Frame(scr.scrollable_frame, bg=CAT_MANTLE, highlightbackground=CAT_SURFACE0, highlightthickness=1, bd=0)
            card.pack(fill=tk.X, pady=6, padx=5)
            
            # Left side checkbox
            var = tk.BooleanVar(value=enabled if not (is_key_required and not has_key) else False)
            cb_state = "disabled" if (is_key_required and not has_key) else "normal"
            
            cb = tk.Checkbutton(
                card, 
                text="", 
                variable=var, 
                command=lambda i=idx, v=var: self.toggle_api(i, v.get()),
                state=cb_state,
                bg=CAT_MANTLE, 
                activebackground=CAT_MANTLE, 
                selectcolor=CAT_BASE,
                highlightthickness=0,
                bd=0
            )
            cb.pack(side=tk.LEFT, padx=15, pady=15)
            
            # Center title and url (Perfect Left Alignment)
            info = tk.Frame(card, bg=CAT_MANTLE)
            info.pack(side=tk.LEFT, fill=tk.BOTH, padx=15)
            
            title_text = name
            title_color = CAT_TEXT
            if is_key_required and not has_key:
                title_text += "  ⚠️ (API Key Required - Check Settings)"
                title_color = CAT_YELLOW
                
            lbl_name = tk.Label(info, text=title_text, font=("Helvetica", 12, "bold"), fg=title_color, bg=CAT_MANTLE, anchor="w")
            lbl_name.pack(anchor=tk.W, pady=(5, 0))
            
            # Display masked/cleared URL
            display_url = url
            if has_key:
                display_url = url.replace("<moapikey>", self.morrenus_key[:4] + "..." + self.morrenus_key[-4:] if len(self.morrenus_key) > 8 else "****")
            else:
                display_url = url.replace("<moapikey>", "MISSING_API_KEY")
                
            lbl_url = tk.Label(info, text=display_url, font=("Helvetica", 9), fg=CAT_SUBTEXT0, bg=CAT_MANTLE, anchor="w")
            lbl_url.pack(anchor=tk.W, pady=(0, 5))
            
        self.apis_scroll_frame = scr
        self.bind_scroll_recursive(self.apis_scroll_frame, self._on_apis_mousewheel)

    def toggle_api(self, index, val):
        self.apis[index]["enabled"] = val
        self.save_apis()

    # ── OVERLAY PROGRESS & DOWNLOAD SHEET FLOW ──
    def show_progress_overlay(self, title_text):
        self.clear_overlay()
        self.overlay_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=500, height=320)
        
        self.overlay_title = tk.Label(self.overlay_frame, text=title_text, font=("Helvetica", 15, "bold"), fg=CAT_TEXT, bg=CAT_CRUST)
        self.overlay_title.pack(pady=(20, 10))
        
        # Search API grid in overlay
        self.api_status_widgets = {}
        for api in self.apis:
            if not api.get("enabled", True):
                continue
            name = api["name"]
            row = tk.Frame(self.overlay_frame, bg=CAT_MANTLE, height=28)
            row.pack(fill=tk.X, padx=20, pady=2)
            row.pack_propagate(False)
            
            lbl_name = tk.Label(row, text=name, font=("Helvetica", 10), fg=CAT_TEXT, bg=CAT_MANTLE)
            lbl_name.pack(side=tk.LEFT, padx=10)
            
            lbl_status = tk.Label(row, text="Searching...", font=("Helvetica", 10), fg=CAT_SUBTEXT0, bg=CAT_MANTLE)
            lbl_status.pack(side=tk.RIGHT, padx=10)
            self.api_status_widgets[name] = lbl_status
            
        # Progress status and bar
        self.progress_lbl = tk.Label(self.overlay_frame, text="Connecting...", font=("Helvetica", 10), fg=CAT_SUBTEXT0, bg=CAT_CRUST)
        self.progress_lbl.pack(pady=(15, 2))
        
        prog_border = tk.Frame(self.overlay_frame, bg=CAT_BTN_OUTLINE, bd=0)
        prog_border.pack(fill=tk.X, padx=20, pady=2)
        self.prog_canvas = tk.Canvas(prog_border, height=12, bg=CAT_MANTLE, highlightthickness=0)
        self.prog_canvas.pack(fill=tk.X, padx=1, pady=1)
        self.prog_bar = self.prog_canvas.create_rectangle(0, 0, 0, 12, fill=CAT_BLUE, outline="")
        
        self.pct_lbl = tk.Label(self.overlay_frame, text="0%", font=("Helvetica", 9), fg=CAT_SUBTEXT0, bg=CAT_CRUST)
        self.pct_lbl.pack(anchor=tk.W, padx=20)
        
        # Buttons
        btn_frame = tk.Frame(self.overlay_frame, bg=CAT_CRUST)
        btn_frame.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        btn_cancel = LabelButton(btn_frame, text="Cancel", command=self.cancel_download_flow, bg=CAT_SURFACE0, fg=CAT_TEXT, pady=5, outlined=True)
        btn_cancel.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        btn_hide = LabelButton(btn_frame, text="Minimize", command=lambda: self.root.iconify(), bg=CAT_SURFACE0, fg=CAT_TEXT, pady=5, outlined=True)
        btn_hide.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

    def clear_overlay(self):
        for widget in self.overlay_frame.winfo_children():
            widget.destroy()

    def cancel_download_flow(self):
        self.app_state = STATE_DETECT
        self.overlay_frame.place_forget()

    def start_download_flow(self, appid):
        self.app_state = STATE_DOWNLOAD
        self.show_progress_overlay(f"Patching {self.selected_name}")
        threading.Thread(target=self.async_download_flow, args=(appid,), daemon=True).start()

    def update_progress(self, percent, text):
        if self.app_state != STATE_DOWNLOAD:
            return
        self.root.after(0, lambda: self._sync_progress(percent, text))

    def _sync_progress(self, percent, text):
        if not hasattr(self, 'prog_canvas') or not self.prog_canvas.winfo_exists():
            return
        self.progress_lbl.configure(text=text)
        width = self.prog_canvas.winfo_width()
        fill_width = int((percent / 100.0) * width)
        self.prog_canvas.coords(self.prog_bar, 0, 0, fill_width, 12)
        if hasattr(self, 'pct_lbl'):
            self.pct_lbl.configure(text=f"{int(percent)}%")

    def update_api_status(self, name, text, color):
        if self.app_state != STATE_DOWNLOAD:
            return
        if name in self.api_status_widgets:
            self.root.after(0, lambda: self.api_status_widgets[name].configure(text=text, fg=color))

    # Show Success dialog in overlay
    def show_success_overlay(self):
        self.clear_overlay()
        
        canvas_check = tk.Canvas(self.overlay_frame, width=50, height=50, bg=CAT_CRUST, highlightthickness=0)
        canvas_check.pack(pady=(25, 8))
        canvas_check.create_oval(5, 5, 45, 45, fill=CAT_GREEN, outline="")
        canvas_check.create_text(25, 25, text="✔", font=("Helvetica", 18, "bold"), fill="#ffffff")
        
        title = tk.Label(self.overlay_frame, text="Download Successful!", font=("Helvetica", 16, "bold"), fg=CAT_TEXT, bg=CAT_CRUST)
        title.pack(pady=2)
        
        sub = tk.Label(self.overlay_frame, text="Patch files and manifests have been installed.", font=("Helvetica", 11), fg=CAT_SUBTEXT0, bg=CAT_CRUST)
        sub.pack(pady=(0, 20))
        
        btn_next = LabelButton(self.overlay_frame, text="Configure Steam", command=self.show_restart_overlay, bg=CAT_BLUE, fg="#0e1621", pady=8)
        btn_next.pack(fill=tk.X, padx=30, pady=10)

    def show_restart_overlay(self):
        self.clear_overlay()
        
        canvas_q = tk.Canvas(self.overlay_frame, width=45, height=45, bg=CAT_CRUST, highlightthickness=0)
        canvas_q.pack(pady=(20, 8))
        canvas_q.create_oval(2, 2, 43, 43, fill="", outline=CAT_BLUE, width=2)
        canvas_q.create_text(22, 22, text="?", font=("Helvetica", 16, "bold"), fill=CAT_BLUE)
        
        title = tk.Label(self.overlay_frame, text="Restart Steam Bottle?", font=("Helvetica", 16, "bold"), fg=CAT_TEXT, bg=CAT_CRUST)
        title.pack(pady=2)
        
        prompt = tk.Label(self.overlay_frame, text="You must restart Steam in order to load the new manifests.", font=("Helvetica", 11), fg=CAT_SUBTEXT0, bg=CAT_CRUST)
        prompt.pack(pady=(0, 25))
        
        btn_frame = tk.Frame(self.overlay_frame, bg=CAT_CRUST)
        btn_frame.pack(fill=tk.X, padx=30)
        
        btn_cancel = LabelButton(btn_frame, text="Later", command=self.close_overlay, bg=CAT_SURFACE0, fg=CAT_TEXT, pady=8, outlined=True)
        btn_cancel.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        btn_confirm = LabelButton(btn_frame, text="Restart Steam", command=self.restart_steam_bottle, bg=CAT_BTN_CONFIRM, fg="#0e1621", hover_bg="#80d4f8", active_bg="#3db8e8", pady=8)
        btn_confirm.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

    def close_overlay(self):
        self.app_state = STATE_DETECT
        self.overlay_frame.place_forget()
        self.switch_tab("dashboard")

    # ── DOWNLOAD FLOW PROCESS ──
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
                        self.update_progress(percent, "Downloading patch archive...")

    def async_download_flow(self, appid):
        try:
            self.update_progress(5, "Resolving download APIs...")
            time.sleep(0.3)
            
            available_urls = self.get_urls_for_appid(appid)
            found_url = None
            
            # Step 1: Query head response on available APIs
            for item in available_urls:
                name = item["name"]
                url = item["url"]
                expected = item["success_code"]
                
                self.update_api_status(name, "Checking...", CAT_BLUE)
                
                if self.check_url_available(url, expected):
                    self.update_api_status(name, "Found Fix!", CAT_GREEN)
                    found_url = url
                    break
                else:
                    self.update_api_status(name, "Not Found", CAT_RED)
                    
            if not found_url:
                raise Exception("No active fixes found for this game in the API list.")
                
            self.update_progress(10, "Starting download...")
            
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
                self.root.after(0, self.show_success_overlay)
            else:
                self.update_progress(100, "Success (Manifest Only)!")
                time.sleep(0.5)
                self.root.after(0, self.show_success_overlay)
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Download Error", f"Failed to download/install: {e}"))
            self.root.after(0, self.close_overlay)
        finally:
            if 'zip_path' in locals() and os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except Exception:
                    pass
            if 'extract_dir' in locals() and os.path.exists(extract_dir):
                try:
                    shutil.rmtree(extract_dir)
                except Exception:
                    pass

    # ── STEAM CLOSING & RESTART LOGIC ──
    def restart_steam_bottle(self):
        try:
            self.update_progress(50, "Restarting Steam...")
            os.system("pkill -9 -f steam.exe")
            os.system("pkill -9 -f steamwebhelper.exe")
            os.system("pkill -9 -f Steam.app")
            time.sleep(2.0)
        except Exception as e:
            print(f"Error terminating Steam: {e}")
            
        try:
            launcher_path = "/Users/Vedant/Applications/CrossOver/Steam/Steam.app"
            if os.path.exists(launcher_path):
                os.system(f'open "{launcher_path}"')
                self.root.after(0, self.close_overlay)
            else:
                messagebox.showinfo("Steam Closed", "Steam has been closed. Please launch Steam manually from CrossOver.")
                self.root.after(0, self.close_overlay)
        except Exception as e:
            print(f"Error relaunching Steam: {e}")
            self.root.after(0, self.close_overlay)

    # ── PULSING LIGHT & STEAM MONITORING ──
    def animate_pulse_loop(self):
        if not self.running:
            return
            
        self.pulse_phase = not self.pulse_phase
        
        if hasattr(self, 'pulse_canvas') and self.pulse_canvas.winfo_exists():
            is_active = (self.active_running_appid > 0 or self.last_detected_store_appid > 0)
            if is_active:
                color = CAT_GREEN if self.pulse_phase else "#1f5e2b"
                self.status_lbl.configure(text=f"Steam Activity: Connected ({self.active_running_name if self.active_running_appid > 0 else self.last_detected_store_name})", fg=CAT_GREEN)
            else:
                color = CAT_BLUE if self.pulse_phase else "#1e375a"
                self.status_lbl.configure(text="Steam Activity: Listening (Waiting for pages)...", fg=CAT_TEXT)
            self.pulse_canvas.itemconfig(self.pulse_circle, fill=color)
            
        self.root.after(800, self.animate_pulse_loop)

    def steam_monitor_loop(self):
        while self.running:
            try:
                time.sleep(0.2) # Fast 0.2s ultra real-time scanning
                self.check_cef_logs()
                self.check_history_db()
            except Exception as e:
                print(f"Error in monitor thread: {e}")

    def check_cef_logs(self):
        # 1. Support both 'cef_log.txt' and 'cef.log' formats
        log_path = os.path.join(self.steam_path, "logs/cef_log.txt")
        if not os.path.exists(log_path):
            log_path = os.path.join(self.steam_path, "logs/cef.log")
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(0, 2)
                    size = f.tell()
                    if size < self.cef_log_position:
                        self.cef_log_position = 0
                    f.seek(self.cef_log_position)
                    
                    lines = f.readlines()
                    self.cef_log_position = f.tell()
                    
                    for line in lines:
                        self.parse_log_line(line)
            except Exception:
                pass

        # 2. Support 'webhelper_js.txt' for instant navigation log output
        js_log_path = os.path.join(self.steam_path, "logs/webhelper_js.txt")
        if os.path.exists(js_log_path):
            try:
                with open(js_log_path, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(0, 2)
                    size = f.tell()
                    if size < self.js_log_position:
                        self.js_log_position = 0
                    f.seek(self.js_log_position)
                    
                    lines = f.readlines()
                    self.js_log_position = f.tell()
                    
                    for line in lines:
                        self.parse_log_line(line)
            except Exception:
                pass

    def parse_log_line(self, line):
        match = re.search(r'store\.steampowered\.com/app/(\d+)', line)
        if match:
            appid = int(match.group(1))
            if appid == 228980: 
                return
            name = self.installed_games.get(appid, self.game_name_cache.get(appid, f"Game {appid}"))
            if appid != self.last_detected_store_appid:
                self.last_detected_store_appid = appid
                self.last_detected_store_name = name
                self.root.after(0, lambda: self.handle_new_store_game_detected(appid, name))

    def check_history_db(self):
        bottle_root = os.path.dirname(os.path.dirname(os.path.dirname(self.steam_path)))
        history_path = os.path.join(bottle_root, "drive_c/users/crossover/AppData/Local/Steam/htmlcache/Default/History")
        if not os.path.exists(history_path):
            return
        
        temp_copy = os.path.join(DEFAULT_TEMP_DIR, "History_check_temp")
        try:
            # Copy to temp file to bypass filesystem caching and lock delays
            import shutil
            shutil.copy2(history_path, temp_copy)
            conn = sqlite3.connect(temp_copy)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(last_visit_time) FROM urls WHERE url LIKE '%store.steampowered.com/app/%'")
            row = cursor.fetchone()
            conn.close()
            
            if row and row[0]:
                latest_time = row[0]
                if latest_time > self.last_user_reg_mtime:
                    self.last_user_reg_mtime = latest_time
                    self.root.after(0, self.refresh_lists_and_dropdown)
        except Exception:
            pass
        finally:
            if os.path.exists(temp_copy):
                try:
                    os.remove(temp_copy)
                except Exception:
                    pass

    def handle_new_store_game_detected(self, appid, name):
        self.set_selected_game(appid, name)
        if hasattr(self, 'scanned_dropdown'):
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

        if self.active_running_appid > 0:
            name = self.installed_games.get(self.active_running_appid, self.game_name_cache.get(self.active_running_appid, self.active_running_name))
            detected_games.append((self.active_running_appid, name, "Running"))
            seen_appids.add(self.active_running_appid)

        if self.last_detected_store_appid > 0 and self.last_detected_store_appid not in seen_appids:
            name = self.installed_games.get(self.last_detected_store_appid, self.game_name_cache.get(self.last_detected_store_appid, self.last_detected_store_name))
            detected_games.append((self.last_detected_store_appid, name, "Active Store Page"))
            seen_appids.add(self.last_detected_store_appid)

        bottle_root = os.path.dirname(os.path.dirname(os.path.dirname(self.steam_path)))
        history_path = os.path.join(bottle_root, "drive_c/users/crossover/AppData/Local/Steam/htmlcache/Default/History")
        if os.path.exists(history_path):
            temp_copy = os.path.join(DEFAULT_TEMP_DIR, "History_scan_temp")
            try:
                # Copy to temp file to bypass filesystem caching and lock delays
                import shutil
                shutil.copy2(history_path, temp_copy)
                conn = sqlite3.connect(temp_copy)
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
                            if not name and title:
                                name = title.replace(" on Steam", "").strip()
                            if not name:
                                name = f"Game {appid}"
                            detected_games.append((appid, name, "Store History"))
                            seen_appids.add(appid)
                conn.close()
            except Exception as e:
                print(f"Error checking History in monitor loop: {e}")
            finally:
                if os.path.exists(temp_copy):
                    try:
                        os.remove(temp_copy)
                    except Exception:
                        pass

        # Scan installed directory as fallback
        for appid, name in self.installed_games.items():
            if appid not in seen_appids:
                detected_games.append((appid, name, "Installed"))
        return detected_games

    def get_scanned_dropdown_options(self):
        detected = self.scan_steam_activity()
        options = []
        for appid, name, source in detected:
            options.append(f"{name} ({source} - App ID: {appid})")
        if not options:
            options.append("No activity detected (Empty)")
        return options

    def on_dropdown_game_selected(self, option):
        match = re.search(r'App ID: (\d+)', option)
        if match:
            appid = int(match.group(1))
            name = option.split(" (")[0]
            self.set_selected_game(appid, name)
        else:
            self.set_selected_game(0, "")

    def on_add_clicked(self):
        if self.selected_appid > 0:
            self.start_download_flow(self.selected_appid)

    def resolve_game_name(self, appid):
        if appid in self.installed_games or appid in self.game_name_cache:
            return
        threading.Thread(target=self.async_resolve_game_name, args=(appid,), daemon=True).start()

    def async_resolve_game_name(self, appid):
        try:
            url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
            req.add_header('Accept-Language', 'en-US,en;q=0.9')
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                if str(appid) in data and data[str(appid)].get('success'):
                    game_name = data[str(appid)]['data'].get('name', f"Game {appid}")
                    self.game_name_cache[appid] = game_name
                    # Update name label directly in UI
                    if appid in self.name_labels and self.name_labels[appid].winfo_exists():
                        self.root.after(0, lambda: self.name_labels[appid].configure(text=game_name))
        except Exception:
            pass

    def refresh_lists_and_dropdown(self):
        if self.current_tab == "dashboard":
            opts = self.get_scanned_dropdown_options()
            if not opts:
                return
                
            self.scanned_dropdown.update_options(opts)
            
            # Parse the App ID of the latest detected activity (first option)
            latest_opt = opts[0]
            latest_appid = 0
            match = re.search(r'App ID: (\d+)', latest_opt)
            if match:
                latest_appid = int(match.group(1))
                
            # If we detected a new game page, auto-select and display it
            if latest_appid > 0 and latest_appid != self.last_auto_selected_appid:
                self.last_auto_selected_appid = latest_appid
                self.scanned_dropdown.set(latest_opt)
                self.on_dropdown_game_selected(latest_opt)
            else:
                # Keep the user's current selection
                current_opt = self.scanned_dropdown.get()
                current_appid = 0
                match_curr = re.search(r'App ID: (\d+)', current_opt)
                if match_curr:
                    current_appid = int(match_curr.group(1))
                    
                matching_opt = None
                for opt in opts:
                    if f"App ID: {current_appid}" in opt:
                        matching_opt = opt
                        break
                        
                if matching_opt:
                    self.scanned_dropdown.set(matching_opt)
                    self.on_dropdown_game_selected(matching_opt)
                else:
                    self.scanned_dropdown.set(opts[0])
                    self.on_dropdown_game_selected(opts[0])


if __name__ == "__main__":
    # Launch main application
    root = tk.Tk()
    app = LuaToolsHelperApp(root)
    
    # Simple clean close handler
    def on_closing():
        app.running = False
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    root.mainloop()
