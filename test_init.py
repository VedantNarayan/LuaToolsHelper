import os
import sys
import time
import shutil
import sqlite3
import re

print("Starting init diagnosis...")

DEFAULT_STEAM_PATH = "/Volumes/Mac_EXT/CrossOverData/CrossOver/Bottles/Steam/drive_c/Program Files (x86)/Steam"
print("Steam path exists:", os.path.exists(DEFAULT_STEAM_PATH))

# 1. Test ACF scanning
print("Scanning ACF games...")
t0 = time.time()
installed_games = {}
steamapps_dir = os.path.join(DEFAULT_STEAM_PATH, "steamapps")
if os.path.exists(steamapps_dir):
    for file in os.listdir(steamapps_dir):
        if file.startswith("appmanifest_") and file.endswith(".acf"):
            filepath = os.path.join(steamapps_dir, file)
            # parse
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
            if appid and name:
                installed_games[appid] = name
print(f"Scanned {len(installed_games)} games in {time.time()-t0:.4f}s")

# 2. Test History scanning
print("Scanning History...")
t0 = time.time()
bottle_root = os.path.dirname(os.path.dirname(os.path.dirname(DEFAULT_STEAM_PATH)))
history_path = os.path.join(bottle_root, "drive_c/users/crossover/AppData/Local/Steam/htmlcache/Default/History")
print("History path exists:", os.path.exists(history_path))

if os.path.exists(history_path):
    temp_history = "/tmp/steam_history_temp_test"
    try:
        print("Copying History database...")
        shutil.copy2(history_path, temp_history)
        print("Connecting to sqlite3 database...")
        conn = sqlite3.connect(temp_history)
        cursor = conn.cursor()
        print("Executing query...")
        cursor.execute(
            "SELECT url, title FROM urls "
            "WHERE url LIKE '%store.steampowered.com/app/%' OR url LIKE '%store.steampowered.com/cart%' "
            "ORDER BY last_visit_time DESC LIMIT 15"
        )
        rows = cursor.fetchall()
        print(f"Query returned {len(rows)} rows.")
        conn.close()
    except Exception as e:
        print("Error during history scan:", e)
    finally:
        if os.path.exists(temp_history):
            os.remove(temp_history)
print(f"History scan completed in {time.time()-t0:.4f}s")

print("Diagnosis completed successfully!")
