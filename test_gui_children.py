import tkinter as tk
import time
import os
import sys

# Import app class
sys.path.append("/Volumes/Mac_EXT/Steam break")
from luatools_helper import LuaToolsHelperApp

print("Initializing Tkinter root...")
root = tk.Tk()
print("Creating app instance...")
app = LuaToolsHelperApp(root)

print("Updating idle tasks...")
root.update_idletasks()

print("Root children:", root.winfo_children())
container = app.container_frame
print("Container frame children:", container.winfo_children())
for child in container.winfo_children():
    print(f"Child: {child}, Class: {child.winfo_class()}, Geometry: {child.winfo_geometry()}")
    if hasattr(child, 'winfo_children'):
        print(f"  Grandchildren: {child.winfo_children()}")

print("Destroying root...")
root.destroy()
print("Success!")
