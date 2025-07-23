#!/usr/bin/env python3
# magic-wormhole file-transfer GUI — multiple file support with hidden subprocess and multi-share
# Date: July 23, 2025
# Author: Santosh Jha (github: Stealth1993)

import os
import re
import time
import queue
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

# ---------- Appearance (Optimized for Readability) ----------
BG        = "#F5F5F5"
FG_TITLE  = "#2C3E50"
FG_BTN    = "#FFFFFF"
BTN_BG    = "#3498DB"
FG_STATUS = "#27AE60"
FG_CODE   = "#E74C3C"
FONT      = ("Arial", 12)

# ---------- Main window setup (Optimized Geometry) ----------
root = tk.Tk()
root.title("Magic-Wormhole Transfer")
root.configure(bg=BG)
root.geometry("760x600")

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
send_file_btn = tk.Button(btn_bar, text="Send Files", width=10, bg=BTN_BG, fg=FG_BTN, font=("Arial", 12, "bold"))
send_text_btn = tk.Button(btn_bar, text="Send Message", width=12, bg=BTN_BG, fg=FG_BTN, font=("Arial", 12, "bold"))
recv_btn      = tk.Button(btn_bar, text="Receive", width=10, bg=BTN_BG, fg=FG_BTN, font=("Arial", 12, "bold"))
cancel_btn    = tk.Button(btn_bar, text="Cancel", width=10, bg="#E74C3C", fg="white", state=tk.DISABLED, font=("Arial", 12, "bold"))
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
                     width=10, command=root.quit, font=("Arial", 12, "bold"))
exit_btn.pack(pady=8)

# ---------- Footer ----------
footer_frame = tk.Frame(holder, bg=BG)
footer_frame.pack(fill="x", pady=5)
version_label = tk.Label(footer_frame, text="V1.0.2", font=("Arial", 10), bg=BG, fg=FG_TITLE)
version_label.pack(side="left", padx=10)
dev_label = tk.Label(footer_frame, text="Dev: Santosh Jha (GitHub: Stealth1993)", font=("Arial", 10), bg=BG, fg=FG_TITLE)
dev_label.pack(side="right", padx=10)

# ---------- Globals ----------
q = queue.Queue(maxsize=10)
proc = None
temp_dir_to_clean = None
temp_receive_dir = None
current_paths = None  # Store original paths for multi-share
current_text = None   # Store text for multi-share
share_in_progress = False

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
    import qrcode
    from PIL import Image, ImageTk
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
    code_entry.config(state=tk.NORMAL)
    code_entry.delete(0, tk.END)
    code_entry.config(state="readonly")

def copy_code():
    txt = code_entry.get()
    if not txt: return
    root.clipboard_clear()
    root.clipboard_append(txt)
    copy_btn.config(text="✓ Copied", bg="#27AE60")
    root.after(1500, lambda: copy_btn.config(text="Copy", bg="#2ECC71"))
    log("Code copied to clipboard")

copy_btn.config(command=copy_code)

def prompt_share_again():
    return messagebox.askyesno("Share Again", "Do you want to share with another person?")

# ---------- Subprocess I/O (Optimized with Hidden Console) ----------
def run_cmd(cmd, mode, downloads=None):
    global proc, share_in_progress, temp_receive_dir
    share_in_progress = True
    try:
        flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0  # Hide console on Windows
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=8192,
            creationflags=flags  # Apply the flag to hide the console
        )
    except FileNotFoundError:
        q.put(("err", "magic-wormhole not installed (pip install magic-wormhole)"))
        share_in_progress = False
        return

    q.put(("status","Connecting…"))
    for line in proc.stdout:
        ln = line.rstrip()
        if not ln: continue
        low = ln.lower()

        if "wormhole code" in low and share_in_progress:
            code = ln.split(":",1)[1].strip()
            q.put(("code", code)); continue

        if any(tok in low for tok in ("%","sending","bytes","progress")):
            q.put(("prog", ln)); continue

        q.put(("dbg", ln))

    rc = proc.wait()
    share_in_progress = False
    if mode == "recv":
        if rc == 0 and temp_receive_dir:
            import shutil
            for item in os.listdir(temp_receive_dir):
                source = os.path.join(temp_receive_dir, item)
                dest = os.path.join(downloads, item)
                if os.path.isfile(source):
                    # For single files, overwrite if exists
                    if os.path.exists(dest):
                        os.remove(dest)
                    shutil.move(source, dest)
                    q.put(("status", f"Saved to: {dest}"))
                else:
                    # For bundles (directories), rename with _ddmmyyyy_HHMM if exists
                    base = item
                    if os.path.exists(dest):
                        timestamp = time.strftime("%d%m%Y_%H%M")
                        dest = os.path.join(downloads, f"{base}_{timestamp}")
                    shutil.move(source, dest)
                    q.put(("status", f"Saved to: {dest}"))
            shutil.rmtree(temp_receive_dir)
            temp_receive_dir = None
            q.put(("dbg", "Download complete."))
        elif temp_receive_dir:
            import shutil
            shutil.rmtree(temp_receive_dir)
            temp_receive_dir = None
    q.put(("done", f"{'Success' if rc==0 else f'Failed (exit {rc})'}"))

# ---------- Button actions (Optimized Calls) ----------
def send_files():
    import shutil
    import tempfile
    global temp_dir_to_clean, current_paths
    paths = filedialog.askopenfilenames()
    if not paths: return
    current_paths = paths  # Store paths for multi-share
    total_size = sum(os.path.getsize(p) for p in paths)
    file_names = [os.path.basename(p) for p in paths]
    if len(paths) == 1:
        cmd = ["wormhole", "send", paths[0]]
        status_var.set(f"Preparing: {file_names[0]}")
        log(f"Sending file: {file_names[0]} ({total_size:,} bytes)")
    else:
        temp_parent = tempfile.mkdtemp()
        bundle_dir = os.path.join(temp_parent, "wormhole-bundle")
        os.mkdir(bundle_dir)
        for path in paths:
            shutil.copy(path, bundle_dir)
        cmd = ["wormhole", "send", bundle_dir]
        temp_dir_to_clean = temp_parent
        status_var.set(f"Preparing bundle of {len(paths)} files")
        log(f"Sending bundle: {', '.join(file_names[:3])}{'...' if len(file_names) > 3 else ''} (Total: {total_size:,} bytes)")
    set_buttons(True); hide_code(); progress_var.set("")
    threading.Thread(target=lambda: run_cmd(cmd, "send"), daemon=True).start()

def send_message():
    global current_text
    txt = simpledialog.askstring("Send Message", "Enter message to send:", parent=root)
    if not txt: return
    current_text = txt  # Store text for multi-share
    status_var.set("Preparing message…")
    log(f"Sending message: {txt[:60]}{'…' if len(txt)>60 else ''}")
    set_buttons(True); hide_code(); progress_var.set("")
    cmd = ["wormhole", "send", "--text", txt.strip()]
    threading.Thread(target=lambda: run_cmd(cmd, "send"), daemon=True).start()

def receive():
    global temp_receive_dir
    code = simpledialog.askstring("Receive", "Enter wormhole code:", parent=root)
    if not code: return
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    os.makedirs(downloads, exist_ok=True)
    import tempfile
    temp_receive_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()

    status_var.set("Connecting to receive…")
    log("Receiving into Downloads folder")
    set_buttons(True); hide_code(); progress_var.set("")

    cmd = ["wormhole","receive","--accept-file",code]

    def run_with_chdir():
        try:
            os.chdir(temp_receive_dir)
            run_cmd(cmd, "recv", downloads=downloads)
        finally:
            os.chdir(original_cwd)

    threading.Thread(target=run_with_chdir, daemon=True).start()

def cancel():
    global proc, temp_dir_to_clean, temp_receive_dir
    if proc and proc.poll() is None:
        proc.terminate()
        try: proc.wait(2)
        except subprocess.TimeoutExpired: proc.kill()
    q.put(("err", "Operation cancelled by user"))
    hide_code()
    if temp_dir_to_clean:
        import shutil
        shutil.rmtree(temp_dir_to_clean)
        temp_dir_to_clean = None
    if temp_receive_dir:
        import shutil
        shutil.rmtree(temp_receive_dir)
        temp_receive_dir = None
    set_buttons(False)

# ---------- UI update loop (Optimized Interval) ----------
def ui_pump():
    global temp_dir_to_clean, current_paths, current_text
    try:
        while True:
            kind, payload = q.get_nowait()
            if kind == "code":
                show_code(payload)
                status_var.set("Share this code with recipient")
                log(f"Generated code: {payload}")
            elif kind == "prog":
                progress_var.set(payload)
                if not progress_lab.winfo_ismapped(): progress_lab.pack()
            elif kind == "status":
                status_var.set(payload)
            elif kind == "err":
                status_var.set("Error")
                log(payload, "err")
                messagebox.showerror("Error", payload)
                set_buttons(False)
                progress_lab.pack_forget()
            elif kind == "done":
                status_var.set(payload)
                log(payload, "ok" if payload.startswith("Success") else "err")
                set_buttons(False)
                progress_lab.pack_forget()
                if payload.startswith("Success") and not share_in_progress:
                    if current_paths or current_text:
                        if prompt_share_again():
                            if current_paths:
                                import shutil
                                import tempfile
                                temp_parent = tempfile.mkdtemp()
                                bundle_dir = os.path.join(temp_parent, "wormhole-bundle")
                                os.mkdir(bundle_dir)
                                for path in current_paths:
                                    shutil.copy(path, bundle_dir)
                                cmd = ["wormhole", "send", bundle_dir]
                                temp_dir_to_clean = temp_parent
                                threading.Thread(target=lambda: run_cmd(cmd, "send"), daemon=True).start()
                            elif current_text:
                                cmd = ["wormhole", "send", "--text", current_text.strip()]
                                threading.Thread(target=lambda: run_cmd(cmd, "send"), daemon=True).start()
                        else:
                            hide_code()
                            current_paths = None
                            current_text = None
                            if temp_dir_to_clean:
                                import shutil
                                shutil.rmtree(temp_dir_to_clean)
                                temp_dir_to_clean = None
            elif kind == "dbg":
                log(payload)
    except queue.Empty:
        pass
    root.after(50, ui_pump)

# ---------- Wire up events ----------
send_file_btn.config(command=send_files)
send_text_btn.config(command=send_message)
recv_btn.config(command=receive)
cancel_btn.config(command=cancel)
root.bind('<Control-s>', lambda e: send_files())
root.bind('<Control-m>', lambda e: send_message())
root.bind('<Control-r>', lambda e: receive())
root.bind('<Escape>', lambda e: cancel() if cancel_btn['state'] == tk.NORMAL else None)

root.after(50, ui_pump)
root.protocol("WM_DELETE_WINDOW", root.quit)
root.mainloop()