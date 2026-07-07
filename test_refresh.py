import sys
import os
import tkinter as tk

# Add the project folder to python path
sys.path.insert(0, "/Volumes/Mac_EXT/Steam break")

from luatools_helper import LuaToolsHelperApp, CAT_BASE

root = tk.Tk()
app = LuaToolsHelperApp(root)
app.switch_state(4) # Switch to STATE_MANAGE

# Let it process events
root.update()

print("scrollable_frame children:", app.scroll_frame.scrollable_frame.winfo_children())
for child in app.scroll_frame.scrollable_frame.winfo_children():
    print("Child frame:", child, "children:", child.winfo_children())
