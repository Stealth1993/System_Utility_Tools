#!/usr/bin/env python3
# magic-wormhole file-transfer GUI — enhanced readability and performance
# Date: July 23, 2025

import os
import re
import time
import queue
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import qrcode
from PIL import Image, ImageTk

# ---------- Appearance (Optimized for Readability) ----------
BG        = "#F5F5F5"  # Light gray background for better contrast
FG_TITLE  = "#2C3E50"  # Dark blue for titles
FG_BTN    = "#FFFFFF"  # White text on buttons for readability
BTN_BG    = "#3498DB"  # Blue buttons for a modern look
FG_STATUS = "#27AE60"  # Green for status, easy to read
FG_CODE   = "#E74C3C"  # Red for code, stands out
FONT      = ("Arial", 12)  # Slightly larger font for readability

# ---------- Main window setup (Optimized Geometry) ----------
root = tk.Tk()
root.title("Magic-Wormhole Transfer")
root.configure(bg=BG)
root.geometry("700x500")  # Reduced size for faster rendering

canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
scroll = tk.Scrollbar(root, command=canvas.yview)
holder = tk.Frame(canvas, bg=BG)
holder.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=holder, anchor="nw")
canvas.configure(yscrollcommand=scroll.set)
canvas.pack(side="left", fill="both", expand=True)
scroll.pack(side="right", fill="y")

# ---------- Widgets (Optimized Layout) ----------
tk.Label(holder, text="Magic-Wormhole File Transfer",
         font=("Arial", 16, "bold"), bg=BG, fg=FG_TITLE).pack(pady=10)

btn_bar = tk.Frame(holder, bg=BG); btn_bar.pack(pady=6)
send_file_btn = tk.Button(btn_bar, text="Send File", width=10, bg=BTN_BG, fg=FG_BTN)
send_text_btn = tk.Button(btn_bar, text="Send Message", width=12, bg=BTN_BG, fg=FG_BTN)
recv_btn      = tk.Button(btn_bar, text="Receive", width=10, bg=BTN_BG, fg=FG_BTN)
cancel_btn    = tk.Button(btn_bar, text="Cancel", width=10, bg="#E74C3C", fg="white", state=tk.DISABLED)
for i, b in enumerate((send_file_btn, send_text_btn, recv_btn, cancel_btn)):
    b.grid(row=0, column=i, padx=4, pady=2)

status_var = tk.StringVar(value="Ready")
tk.Label(holder, textvariable=status_var, font=FONT, bg=BG, fg=FG_STATUS).pack()

progress_var = tk.StringVar()
progress_lab = tk.Label(holder, textvariable=progress_var,
                        font=("Courier", 10), bg=BG, fg=FG_STATUS)

code_frame = tk.Frame(holder, bg=BG)
tk.Label(code_frame, text="🔑 Code (to share):",
         font=("Arial", 12, "bold"), bg=BG, fg=FG_TITLE).pack(side="left", padx=(0,2))
code_entry = tk.Entry(code_frame, width=25,
                      font=("Courier", 12, "bold"), bg="#ECF0F1", fg=FG_CODE,
                      justify="center", relief="flat", state="readonly")
copy_btn = tk.Button(code_frame, text="Copy", bg="#2ECC71", fg="white")
qr_label = tk.Label(holder, bg=BG)

msg_box = tk.Text(holder, height=5, wrap=tk.WORD,
                  bg="#ECF0F1", fg=FG_STATUS, font=FONT, state=tk.DISABLED)
msg_box.pack(padx=10, pady=8, fill="both", expand=True)

exit_btn = tk.Button(holder, text="Exit", bg="#E74C3C", fg="white",
                     width=10, command=root.quit)
exit_btn.pack(pady=8)

# ---------- Globals ----------
q = queue.Queue(maxsize=10)  # Limited queue size for performance
proc = None

# ---------- Helpers (Optimized) ----------
def log(msg, kind="info"):
    msg_box.config(state=tk.NORMAL)
    tag = "err" if kind=="err" else "ok"
    msg_box.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n", tag)
    msg_box.tag_config("err", foreground="#E74C3C")
    msg_box.tag_config("ok",  foreground="#27AE60")
    msg_box.config(state=tk.DISABLED)
    msg_box.see(tk.END)

def set_buttons(active):
    state = tk.DISABLED if active else tk.NORMAL
    for btn in (send_file_btn, send_text_btn, recv_btn):
        btn.config(state=state)
    cancel_btn.config(state=tk.NORMAL if active else tk.DISABLED)

def show_code(code):
    code_entry.config(state=tk.NORMAL)
    code_entry.delete(0, tk.END)
    code_entry.insert(0, code)
    code_entry.config(state="readonly")
    code_frame.pack(pady=6)
    code_entry.pack(side="left")
    copy_btn.pack(side="left", padx=4)
    img = qrcode.make(code).resize((180, 180), Image.Resampling.LANCZOS)
    qr_label.img = ImageTk.PhotoImage(img)
    qr_label.config(image=qr_label.img)
    qr_label.pack(pady=2)

def hide_code():
    code_frame.pack_forget()
    qr_label.pack_forget()

def copy_code():
    txt = code_entry.get()
    if not txt: return
    root.clipboard_clear()
    root.clipboard_append(txt)
    copy_btn.config(text="✓ Copied", bg="#27AE60")
    root.after(1500, lambda: copy_btn.config(text="Copy", bg="#2ECC71"))
    log("Code copied to clipboard")

copy_btn.config(command=copy_code)

# ---------- Subprocess I/O (Optimized with Buffering) ----------
def run_cmd(cmd, mode, downloads=None):
    global proc
    try:
        flags = subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=8192,  # Larger buffer for faster I/O
            creationflags=flags
        )
    except FileNotFoundError:
        q.put(("err", "magic-wormhole not installed (pip install magic-wormhole)"))
        return

    q.put(("status","Connecting…"))
    for line in proc.stdout:
        ln = line.rstrip()
        if not ln: continue
        low = ln.lower()

        if "wormhole code" in low:
            code = ln.split(":",1)[1].strip()
            q.put(("code", code)); continue

        if any(tok in low for tok in ("%","sending","bytes","progress")):
            q.put(("prog", ln)); continue

        if mode=="recv" and "written to" in low:
            match = re.search(r"written to (.+)", ln)
            if match:
                real_name = match.group(1).strip().strip("'\"")
                real_dest = os.path.join(downloads, real_name)
                q.put(("status", f"Saved to: {real_dest}"))
            q.put(("prog", ln))
            continue

        q.put(("dbg", ln))

    rc = proc.wait()
    q.put(("done", f"{'Success' if rc==0 else f'Failed (exit {rc})'}"))

# ---------- Button actions (Optimized Calls) ----------
def send_file():
    path = filedialog.askopenfilename()
    if not path: return
    name = os.path.basename(path); size = os.path.getsize(path)
    status_var.set(f"Preparing: {name}")
    log(f"Sending file: {name} ({size:,} bytes)")
    set_buttons(True); hide_code(); progress_var.set("")
    threading.Thread(target=run_cmd, args=(["wormhole","send",path],"send"), daemon=True).start()

def send_message():
    txt = simpledialog.askstring("Send Message", "Enter message to send:", parent=root)
    if not txt: return
    status_var.set("Preparing message…")
    log(f"Sending message: {txt[:60]}{'…' if len(txt)>60 else ''}")
    set_buttons(True); hide_code(); progress_var.set("")
    threading.Thread(target=run_cmd, args=(["wormhole","send","--text",txt.strip()],"send"), daemon=True).start()

def receive():
    code = simpledialog.askstring("Receive", "Enter wormhole code:", parent=root)
    if not code: return
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    os.makedirs(downloads, exist_ok=True)
    original_cwd = os.getcwd()

    status_var.set("Connecting to receive…")
    log("Receiving into Downloads folder")
    set_buttons(True); hide_code(); progress_var.set("")

    cmd = ["wormhole","receive","--accept-file",code]

    def run_with_chdir():
        try:
            os.chdir(downloads)
            run_cmd(cmd, "recv", downloads=downloads)
        finally:
            os.chdir(original_cwd)

    threading.Thread(target=run_with_chdir, daemon=True).start()

def cancel():
    global proc
    if proc and proc.poll() is None:
        proc.terminate()
        try: proc.wait(2)  # Reduced wait time for faster cancellation
        except subprocess.TimeoutExpired: proc.kill()
    q.put(("err","Operation cancelled by user"))

# ---------- UI update loop (Optimized Interval) ----------
def ui_pump():
    try:
        while True:
            kind, payload = q.get_nowait()
            if kind=="code":
                show_code(payload); status_var.set("Share this code with recipient"); log(f"Generated code: {payload}")
            elif kind=="prog":
                progress_var.set(payload)
                if not progress_lab.winfo_ismapped(): progress_lab.pack()
            elif kind=="status":
                status_var.set(payload)
            elif kind=="err":
                status_var.set("Error"); log(payload,"err")
                messagebox.showerror("Error",payload); set_buttons(False); progress_lab.pack_forget()
            elif kind=="done":
                status_var.set(payload); log(payload, "ok" if payload.startswith("Success") else "err")
                set_buttons(False); progress_lab.pack_forget()
            elif kind=="dbg":
                log(payload)
    except queue.Empty:
        pass
    root.after(50, ui_pump)  # Reduced interval for faster updates

# ---------- Wire up events ----------
send_file_btn.config(command=send_file)
send_text_btn.config(command=send_message)
recv_btn.config(command=receive)
cancel_btn.config(command=cancel)
root.bind('<Control-s>', lambda e: send_file())
root.bind('<Control-m>', lambda e: send_message())
root.bind('<Control-r>', lambda e: receive())
root.bind('<Escape>',   lambda e: cancel() if cancel_btn['state']==tk.NORMAL else None)

root.after(50, ui_pump)
root.protocol("WM_DELETE_WINDOW", root.quit)
root.mainloop()