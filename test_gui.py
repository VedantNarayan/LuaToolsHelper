import tkinter as tk
import time

print("Launching test GUI...")
r = tk.Tk()
r.title("Test GUI")
r.geometry("400x300")
r.configure(bg="blue")

l = tk.Label(r, text="Tkinter is Working!", font=("Helvetica", 16, "bold"), bg="blue", fg="white")
l.pack(pady=100)

print("Main loop started.")
r.mainloop()
print("Main loop ended.")
