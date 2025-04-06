import wmi
import tkinter as tk
from tkinter import ttk

def fetch_os_details():
    os_info = c.Win32_OperatingSystem()[0]
    details = f"""
OS Name: {os_info.Name.split('|')[0]}
Version: {os_info.Version}
Manufacturer: {os_info.Manufacturer}
Architecture: {os_info.OSArchitecture}
Boot Device: {os_info.BootDevice}
System Drive: {os_info.SystemDrive}
Total Visible Memory: {int(os_info.TotalVisibleMemorySize) // 1024} MB
Free Physical Memory: {int(os_info.FreePhysicalMemory) // 1024} MB
Windows Directory: {os_info.WindowsDirectory}
"""
    return details.strip()

def fetch_hw_details():
    computer_info = c.Win32_ComputerSystem()[0]
    bios_info = c.Win32_BIOS()[0]
    
    # Getting disk information
    disk_details = get_disk_info()

    details = f"""
Manufacturer: {computer_info.Manufacturer}
Model: {computer_info.Model}
Serial Number: {bios_info.SerialNumber}
Number of Processors: {computer_info.NumberOfProcessors}
System Type: {computer_info.SystemType}
BIOS Version: {bios_info.SMBIOSBIOSVersion}
Total Physical Memory: {int(computer_info.TotalPhysicalMemory) // (1024**2)} MB
Domain Name: {computer_info.Domain}
{disk_details}
"""
    return details.strip()

def get_disk_info():
    # Initialize WMI to fetch disk data
    disk_info = ""
    for disk in c.Win32_LogicalDisk(DriveType=3):  # DriveType 3 corresponds to local disks
        total_size = int(disk.Size) // (1024**3)  # Convert to GB
        free_space = int(disk.FreeSpace) // (1024**3)  # Convert to GB
        disk_info += f"\nDisk {disk.DeviceID} ({disk.MediaType}):\n"
        disk_info += f"  Total Size: {total_size} GB\n"
        disk_info += f"  Free Space: {free_space} GB\n"
    
    return disk_info.strip()

def display_details(details, title):
    # Create a new window to display the information
    info_window = tk.Toplevel(root)
    info_window.title(title)

    # Display details
    text_widget = tk.Text(info_window, wrap=tk.WORD, height=20, width=60)
    text_widget.insert(tk.END, details)
    text_widget.config(state=tk.DISABLED)
    text_widget.pack(padx=10, pady=10)

    # Add a copy button
    def copy_to_clipboard():
        root.clipboard_clear()
        root.clipboard_append(details)
        root.update()  # Ensures the clipboard is updated

    copy_btn = ttk.Button(info_window, text="Copy to Clipboard", command=copy_to_clipboard)
    copy_btn.pack(pady=10)

# Create the WMI object
c = wmi.WMI()

# Main GUI window
root = tk.Tk()
root.title("System Information")
root.geometry("300x250")

# Button for OS information
btn_os = ttk.Button(root, text="OS Information", command=lambda: display_details(fetch_os_details(), "OS Information"))
btn_os.pack(expand=True, pady=10)

# Button for System (Hardware) information
btn_sys = ttk.Button(root, text="System Information", command=lambda: display_details(fetch_hw_details(), "System Information"))
btn_sys.pack(expand=True, pady=10)

root.mainloop()



#pip install pyinstaller
#pyinstaller --onefile --noconsole --icon=icon.ico your_script_name.py
