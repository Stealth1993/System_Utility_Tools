#!/usr/bin/env python3
# magic-wormhole file-transfer GUI
# Optimised + bug-fixed edition - 23 Jul 2025

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import threading, queue, subprocess, os, time
import qrcode
from PIL import Image, ImageTk

# ----------  Appearance  ----------
BG          = "#050608"
FG_TITLE    = "#f00487"       # pink
FG_BTN      = "#150303"       # button text
BTN_BG      = "#A4C639"       # lime
FG_STATUS   = "#DADE74"       # yellow-green
FG_CODE     = "#FF6B6B"       # salmon highlight
FONT        = ("Arial", 11)

root = tk.Tk()
root.title("Magic-Wormhole Transfer")
root.configure(bg=BG)
root.geometry("720x560")

# ----------  Layout skeleton ----------
canvas      = tk.Canvas(root, bg=BG, highlightthickness=0)
scroll      = tk.Scrollbar(root, command=canvas.yview)
holder      = tk.Frame(canvas, bg=BG)
holder.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0,0), window=holder, anchor="nw")
canvas.configure(yscrollcommand=scroll.set)
canvas.pack(side="left", fill="both", expand=True)
scroll.pack(side="right", fill="y")

# ----------  Widgets ----------
tk.Label(holder, text="Magic-Wormhole File Transfer",
         font=("Arial", 18, "bold"), bg=BG, fg=FG_TITLE).pack(pady=12)

btn_bar = tk.Frame(holder, bg=BG); btn_bar.pack(pady=8)

send_file_btn = tk.Button(btn_bar, text="Send File",     width=10, bg=BTN_BG, fg=FG_BTN)
send_text_btn = tk.Button(btn_bar, text="Send Message",  width=12, bg=BTN_BG, fg=FG_BTN)
recv_btn      = tk.Button(btn_bar, text="Receive",       width=10, bg=BTN_BG, fg=FG_BTN)
cancel_btn    = tk.Button(btn_bar, text="Cancel",        width=10, bg="#FF4444",
                          fg="white", state=tk.DISABLED)
for i,b in enumerate((send_file_btn, send_text_btn, recv_btn, cancel_btn)):
    b.grid(row=0, column=i, padx=6, pady=4)

status_var  = tk.StringVar(value="Ready")
tk.Label(holder, textvariable=status_var, font=FONT, bg=BG, fg=FG_STATUS).pack()

progress_var = tk.StringVar()
progress_lab = tk.Label(holder, textvariable=progress_var, font=("Courier",10),
                       bg=BG, fg=FG_STATUS)

# code display
code_frame   = tk.Frame(holder, bg=BG)
tk.Label(code_frame, text="🔑 Code (to share):", font=("Arial",12,"bold"),
         bg=BG, fg=FG_TITLE).pack(side="left", padx=(0,4))
code_entry   = tk.Entry(code_frame, width=28, font=("Courier", 14, "bold"),
                        bg="#1a1a1a", fg=FG_CODE, justify="center",
                        relief="flat", state="readonly")
copy_btn     = tk.Button(code_frame, text="Copy", bg="#4CAF50", fg="white")
qr_label     = tk.Label(holder, bg=BG)

# message/history box
msg_box = tk.Text(holder, height=6, wrap=tk.WORD, bg="#1a1a1a",
                  fg=FG_STATUS, font=FONT, state=tk.DISABLED)
msg_box.pack(padx=12, pady=10, fill="both", expand=True)

exit_btn = tk.Button(holder, text="Exit", bg="#FF6B6B", fg="white",
                     width=10, command=root.quit)
exit_btn.pack(pady=10)

# ----------  Globals ----------
q   = queue.Queue()
proc: subprocess.Popen | None = None

# ----------  Helpers ----------
def log(msg:str, kind:str="info"):
    """Append timestamped line to history pane."""
    msg_box.config(state=tk.NORMAL)
    tag = "err" if kind=="err" else "ok"
    msg_box.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n", tag)
    msg_box.tag_config("err", foreground="#FF6B6B")
    msg_box.tag_config("ok",  foreground="#4CAF50")
    msg_box.config(state=tk.DISABLED)
    msg_box.see(tk.END)

def set_buttons(work:bool):
    """Enable/disable buttons depending on ongoing work."""
    state = tk.DISABLED if work else tk.NORMAL
    for b in (send_file_btn, send_text_btn, recv_btn):
        b.config(state=state)
    cancel_btn.config(state=tk.NORMAL if work else tk.DISABLED)

def show_code(code:str):
    """Show code, copy button, and QR."""
    code_entry.config(state=tk.NORMAL)
    code_entry.delete(0, tk.END)
    code_entry.insert(0, code)
    code_entry.config(state="readonly")
    code_frame.pack(pady=8)
    code_entry.pack(side="left")
    copy_btn.pack(side="left", padx=6)
    # QR generation
    img = qrcode.make(code).resize((190,190), Image.Resampling.LANCZOS)
    qr_label.img = ImageTk.PhotoImage(img)
    qr_label.config(image=qr_label.img)
    qr_label.pack(pady=4)

def hide_code():
    code_frame.pack_forget()
    qr_label.pack_forget()

def copy_code():
    text = code_entry.get()
    if text:
        root.clipboard_clear()
        root.clipboard_append(text)
        copy_btn.config(text="✓ Copied", bg="#2E7D32")
        root.after(2000, lambda: copy_btn.config(text="Copy", bg="#4CAF50"))
        log("Code copied to clipboard")

copy_btn.config(command=copy_code)

# ----------  Process I/O threads ----------
def run_cmd(cmd:list[str], mode:str, extra=None):
    """Start wormhole subprocess and stream combined output to queue."""
    global proc
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,   # <= critical fix: capture *everything*
            text=True,
            bufsize=1,
            universal_newlines=True
        )
    except FileNotFoundError:
        q.put(("err", "magic-wormhole is not installed (pip install magic-wormhole)"))
        return
    q.put(("status", f"Connecting…"))
    for line in proc.stdout:
        ln = line.strip()
        if not ln:
            continue
        # Detect code (case-insensitive, handles “is:” or just “code:”)
        if "wormhole code" in ln.lower():
            # Take text after ':' if present, else last token
            code = ln.split(":",1)[1].strip() if ':' in ln else ln.split()[-1]
            q.put(("code", code))
            continue
        # Progress heuristics
        if any(x in ln.lower() for x in ("%","sending","bytes","waiting","progress")):
            q.put(("prog", ln))
        elif mode=="recv" and any(x in ln.lower() for x in ("ok?","overwrite")):
            proc.stdin.write("y\n"); proc.stdin.flush()
            q.put(("prog","Answering Y to prompt"))
        elif mode=="recv" and ln.startswith("Message:"):
            q.put(("msg", ln[len("Message:"):].strip()))
        else:
            # General status
            q.put(("dbg", ln))
    rc = proc.wait()
    q.put(("done", f"{'Success' if rc==0 else 'Failed'} (exit {rc})"))

# ----------  Button actions ----------
def send_file():
    path = filedialog.askopenfilename()
    if not path: return
    status_var.set(f"Preparing: {os.path.basename(path)}")
    log(f"Sending file: {os.path.basename(path)} ({os.path.getsize(path):,} bytes)")
    set_buttons(True); hide_code(); progress_var.set("")
    threading.Thread(target=run_cmd,
                     args=(["wormhole","send",path],"send"),
                     daemon=True).start()

def send_message():
    txt = simpledialog.askstring("Send Message","Enter message to send:", parent=root)
    if not txt: return
    status_var.set("Preparing message…")
    log(f"Sending message: {txt[:60]}{'…' if len(txt)>60 else ''}")
    set_buttons(True); hide_code(); progress_var.set("")
    threading.Thread(target=run_cmd,
                     args=(["wormhole","send","--text",txt],"send"),
                     daemon=True).start()

def recv():
    code = simpledialog.askstring("Receive","Enter wormhole code:", parent=root)
    if not code: return
    status_var.set("Connecting to receive…")
    log(f"Receiving using code: {code}")
    set_buttons(True); hide_code(); progress_var.set("")
    threading.Thread(target=run_cmd,
                     args=(["wormhole","receive",code],"recv"),
                     daemon=True).start()

def cancel():
    global proc
    if proc and proc.poll() is None:
        proc.terminate()
        try: proc.wait(3)
        except subprocess.TimeoutExpired: proc.kill()
    q.put(("err","Operation cancelled by user"))

# ----------  Queue→GUI pump ----------
def ui_pump():
    try:
        while True:
            kind, payload = q.get_nowait()
            if kind=="code":
                show_code(payload)
                status_var.set("Share this code with recipient")
                log(f"Generated code: {payload}")
            elif kind=="prog":
                progress_var.set(payload)
                if not progress_lab.winfo_ismapped():
                    progress_lab.pack()
            elif kind=="status":
                status_var.set(payload)
            elif kind=="msg":
                log(f"✉ Received message: {payload}")
            elif kind=="err":
                status_var.set("Error")
                log(payload, "err")
                messagebox.showerror("Error", payload)
                set_buttons(False); progress_lab.pack_forget()
            elif kind=="done":
                status_var.set(payload)
                log(payload, "ok" if payload.startswith("Success") else "err")
                set_buttons(False); progress_lab.pack_forget()
            elif kind=="dbg":
                # optional: comment out to silence
                log(payload)
    except queue.Empty:
        pass
    root.after(80, ui_pump)

# ----------  Wire up ----------
send_file_btn.config(command=send_file)
send_text_btn.config(command=send_message)
recv_btn.config(command=recv)
cancel_btn.config(command=cancel)

root.bind('<Control-s>', lambda e: send_file())
root.bind('<Control-m>', lambda e: send_message())
root.bind('<Control-r>', lambda e: recv())
root.bind('<Escape>',   lambda e: cancel() if cancel_btn['state']==tk.NORMAL else None)

root.after(100, ui_pump)
root.protocol("WM_DELETE_WINDOW", root.quit)
root.mainloop()