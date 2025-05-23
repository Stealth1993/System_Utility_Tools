import psutil
import platform
import wmi
import re
import subprocess
import os
import json
import winreg

# Helper Functions
def get_memory_type(memory_type_code):
    """Decode SMBIOS memory type code into DDR type."""
    memory_types = {
        21: "DDR3",
        24: "DDR4",
        26: "DDR5"
    }
    return memory_types.get(memory_type_code, f"Unknown (Type Code: {memory_type_code})")

def get_cpu_generation(cpu_name):
    """Estimate CPU generation based on name."""
    if "Intel" in cpu_name:
        match = re.search(r"i[3579]-(\d)", cpu_name)
        if match:
            gen = int(match.group(1))
            generations = {
                7: "7th Gen (Kaby Lake)",
                8: "8th Gen (Coffee Lake)",
                9: "9th Gen (Coffee Lake Refresh)",
                10: "10th Gen (Comet Lake/Ice Lake)",
                11: "11th Gen (Tiger Lake)",
                12: "12th Gen (Alder Lake)",
                13: "13th Gen (Raptor Lake)"
            }
            return generations.get(gen, f"Generation {gen} (Look up for exact architecture)")
    elif "Ryzen" in cpu_name:
        match = re.search(r"Ryzen.*(\d{4})", cpu_name)
        if match:
            series = match.group(1)
            series_map = {
                "1000": "Ryzen 1000 Series (Zen)",
                "2000": "Ryzen 2000 Series (Zen+)",
                "3000": "Ryzen 3000 Series (Zen 2)",
                "5000": "Ryzen 5000 Series (Zen 3)",
                "7000": "Ryzen 7000 Series (Zen 4)"
            }
            return series_map.get(series, f"Ryzen Series {series} (Look up for exact architecture)")
    return "Unknown Generation"

def bytes_to_gb(bytes):
    """Convert bytes to GB with 2 decimal places."""
    if not bytes:
        return "0 GB"
    return f"{bytes / (1024**3):.2f} GB"

def estimate_camera_megapixels(camera_name):
    """Estimate camera megapixels based on name."""
    if not camera_name:
        return "N/A"
    camera_name = camera_name.lower()
    if "hd" in camera_name or "720p" in camera_name:
        return "Approx. 1 MP (720p HD)"
    elif "1080p" in camera_name or "full hd" in camera_name:
        return "Approx. 2 MP (1080p Full HD)"
    elif "4k" in camera_name or "uhd" in camera_name:
        return "Approx. 8 MP (4K UHD)"
    return "Unknown (Megapixels not directly available)"

def wh_to_mah(watt_hours, voltage):
    """Convert watt-hours to milliamp-hours."""
    if not watt_hours or not voltage:
        return "N/A (Voltage or capacity data unavailable)"
    try:
        return round((watt_hours * 1000) / voltage)
    except (TypeError, ValueError):
        return "N/A (Invalid data)"

# Initialize WMI
try:
    wmi_obj = wmi.WMI()
except Exception as e:
    print(f"Error initializing WMI: {e}")
    wmi_obj = None

# Gather CPU Information
cpu_info = {}
try:
    cpu = wmi_obj.Win32_Processor()[0] if wmi_obj else None
    cpu_info = {
        "name": cpu.Name.strip() if cpu and cpu.Name else "Unknown",
        "manufacturer": cpu.Manufacturer if cpu and cpu.Manufacturer else "Unknown",
        "cores": cpu.NumberOfCores if cpu and cpu.NumberOfCores else "Unknown",
        "threads": cpu.NumberOfLogicalProcessors if cpu and cpu.NumberOfLogicalProcessors else "Unknown",
        "speed": f"{cpu.CurrentClockSpeed / 1000:.2f}" if cpu and cpu.CurrentClockSpeed else "Unknown",
        "max_speed": f"{cpu.MaxClockSpeed / 1000:.2f}" if cpu and cpu.MaxClockSpeed else "Unknown",
        "l1_cache": cpu.L1CacheSize / 1024 if cpu and hasattr(cpu, 'L1CacheSize') and cpu.L1CacheSize else "Unknown",
        "l2_cache": cpu.L2CacheSize / 1024 if cpu and hasattr(cpu, 'L2CacheSize') and cpu.L2CacheSize else "Unknown",
        "l3_cache": cpu.L3CacheSize / 1024 if cpu and hasattr(cpu, 'L3CacheSize') and cpu.L3CacheSize else "Unknown",
        "family": cpu.Caption if cpu and cpu.Caption else "Unknown",
        "generation": get_cpu_generation(cpu.Name if cpu and cpu.Name else "")
    }
except Exception as e:
    cpu_info = {key: f"Error: {e}" for key in ["name", "manufacturer", "cores", "threads", "speed", "max_speed", "l1_cache", "l2_cache", "l3_cache", "family", "generation"]}

# Gather RAM Information
ram_info = {}
try:
    ram = wmi_obj.Win32_PhysicalMemory() if wmi_obj else []
    total_ram = psutil.virtual_memory().total if hasattr(psutil, 'virtual_memory') else 0
    first_ram = ram[0] if ram else None
    ram_info = {
        "total": bytes_to_gb(total_ram),
        "type": get_memory_type(first_ram.SMBIOSMemoryType if first_ram and hasattr(first_ram, 'SMBIOSMemoryType') else 0),
        "speed": f"{first_ram.Speed} MHz" if first_ram and first_ram.Speed else "Unknown",
        "manufacturer": first_ram.Manufacturer if first_ram and first_ram.Manufacturer else "Unknown",
        "part_number": first_ram.PartNumber.strip() if first_ram and first_ram.PartNumber else "Unknown",
        "serial_number": first_ram.SerialNumber.strip() if first_ram and first_ram.SerialNumber else "Unknown"
    }
except Exception as e:
    ram_info = {key: f"Error: {e}" for key in ["total", "type", "speed", "manufacturer", "part_number", "serial_number"]}

# Gather Motherboard Information
mb_info = {}
try:
    mb = wmi_obj.Win32_BaseBoard()[0] if wmi_obj else None
    mb_info = {
        "manufacturer": mb.Manufacturer if mb and mb.Manufacturer else "Unknown",
        "model": mb.Product if mb and mb.Product else "Unknown",
        "serial_number": mb.SerialNumber.strip() if mb and mb.SerialNumber else "Unknown"
    }
except Exception as e:
    mb_info = {key: f"Error: {e}" for key in ["manufacturer", "model", "serial_number"]}

# Gather OS Information
os_info = {}
try:
    os_info = {
        "version": f"{platform.system()} {platform.release()}",
        "build": platform.version()
    }
except Exception as e:
    os_info = {key: f"Error: {e}" for key in ["version", "build"]}

# Gather Battery Information
battery_info = {}
try:
    battery = psutil.sensors_battery() if hasattr(psutil, 'sensors_battery') else None
    if battery and wmi_obj:
        battery_static = wmi_obj.Win32_Battery()[0] if wmi_obj.Win32_Battery() else None
        design_capacity = battery_static.DesignCapacity / 1000 if battery_static and battery_static.DesignCapacity else None  # mWh to Wh
        full_capacity = battery_static.FullChargeCapacity / 1000 if battery_static and battery_static.FullChargeCapacity else None
        voltage = battery_static.DesignVoltage / 1000 if battery_static and battery_static.DesignVoltage else 3.7  # mV to V, default 3.7V
        health = round((full_capacity / design_capacity) * 100, 2) if design_capacity and full_capacity and design_capacity != 0 else "Unknown"
        battery_info = {
            "name": battery_static.Name if battery_static and battery_static.Name else "Battery",
            "manufacturer": battery_static.Manufacturer if battery_static and battery_static.Manufacturer else "Unknown",
            "chemistry": battery_static.Chemistry if battery_static and battery_static.Chemistry else "Unknown",
            "design_capacity_wh": f"{design_capacity:.2f} Wh" if design_capacity else "Unknown",
            "full_capacity_wh": f"{full_capacity:.2f} Wh" if full_capacity else "Unknown",
            "design_capacity_mah": wh_to_mah(design_capacity, voltage) if design_capacity else "N/A",
            "full_capacity_mah": wh_to_mah(full_capacity, voltage) if full_capacity else "N/A",
            "health": f"{health} %" if health != "Unknown" else "Unknown"
        }
    else:
        battery_info = {key: "N/A" for key in ["name", "manufacturer", "chemistry", "design_capacity_wh", "full_capacity_wh", "design_capacity_mah", "full_capacity_mah", "health"]}
        battery_info["name"] = "No battery detected"
except Exception as e:
    battery_info = {key: f"Error: {e}" for key in ["name", "manufacturer", "chemistry", "design_capacity_wh", "full_capacity_wh", "design_capacity_mah", "full_capacity_mah", "health"]}

# Gather Camera Information
camera_info = {}
try:
    if wmi_obj:
        cameras = [dev for dev in wmi_obj.Win32_PnPEntity() if getattr(dev, 'PNPClass', None) in ["Image", "Camera"]]
        if cameras:
            camera = cameras[0]
            camera_info = {
                "name": camera.Name if camera.Name else "Unknown",
                "manufacturer": camera.Manufacturer if camera.Manufacturer else "Unknown",
                "device_id": camera.DeviceID if camera.DeviceID else "Unknown",
                "megapixels": estimate_camera_megapixels(camera.Name if camera.Name else "")
            }
        else:
            camera_info = {"name": "No camera detected", "manufacturer": "N/A", "device_id": "N/A", "megapixels": "N/A"}
    else:
        camera_info = {"name": "No camera detected", "manufacturer": "N/A", "device_id": "N/A", "megapixels": "N/A"}
except Exception as e:
    camera_info = {key: f"Error: {e}" for key in ["name", "manufacturer", "device_id", "megapixels"]}

# Gather SSD Information
ssd_details = []
try:
    if wmi_obj:
        disks = wmi_obj.Win32_DiskDrive()
        for disk in disks:
            media_type = getattr(disk, 'MediaType', '').lower()
            model = disk.Model.lower() if disk.Model else ""
            if "ssd" in media_type or "ssd" in model:
                ssd_details.append(
                    f"Model: {disk.Model}, Manufacturer: {disk.Manufacturer if disk.Manufacturer else 'Unknown'}, "
                    f"Size: {bytes_to_gb(int(disk.Size) if disk.Size else 0)}, Interface: {disk.InterfaceType if disk.InterfaceType else 'Unknown'}, "
                    f"Serial Number: {disk.SerialNumber.strip() if disk.SerialNumber else 'Unknown'}"
                )
        if not ssd_details:
            ssd_details.append("No SSD detected")
    else:
        ssd_details.append("No SSD detected")
except Exception as e:
    ssd_details = [f"Error: {e}"]

# Gather TPM Information
tpm_info = {}
try:
    tpm_output = subprocess.check_output(["powershell", "-Command", "Get-Tpm | ConvertTo-Json"], text=True, stderr=subprocess.STDOUT)
    tpm_data = json.loads(tpm_output)
    tpm_info = {
        "present": str(tpm_data.get("TpmPresent", False)),
        "ready": str(tpm_data.get("TpmReady", False)),
        "version": tpm_data.get("ManufacturerVersion", "Unknown"),
        "status": "Enabled and Ready" if tpm_data.get("TpmPresent") and tpm_data.get("TpmReady") else "Not Ready or Disabled"
    }
except subprocess.CalledProcessError:
    tpm_info = {"present": "False", "ready": "False", "version": "N/A", "status": "No TPM detected"}
except Exception as e:
    tpm_info = {key: f"Error: {e}" for key in ["present", "ready", "version", "status"]}

# Gather UEFI Status
uefi_info = {}
try:
    systeminfo = subprocess.check_output("systeminfo", text=True)
    if "BIOS Mode: UEFI" in systeminfo:
        try:
            secure_boot = subprocess.check_output(["powershell", "-Command", "Confirm-SecureBootUEFI"], text=True).strip()
            uefi_info["status"] = "Enabled (UEFI Mode with Secure Boot)" if secure_boot == "True" else "Enabled (UEFI Mode without Secure Boot)"
            uefi_info["secure_boot"] = "Enabled" if secure_boot == "True" else "Disabled"
        except subprocess.CalledProcessError:
            uefi_info["status"] = "Enabled (UEFI Mode, Secure Boot status unknown)"
            uefi_info["secure_boot"] = "Unknown"
    else:
        uefi_info["status"] = "Disabled (Legacy/BIOS Mode)"
        uefi_info["secure_boot"] = "N/A"
except Exception as e:
    uefi_info = {"status": f"Error: {e}", "secure_boot": "Unknown"}

# Gather Microsoft Office Details
def get_office_details():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Office\ClickToRun\Configuration")
        office_version = winreg.QueryValueEx(key, "ProductReleaseIds")[0]
        office_edition = office_version
        winreg.CloseKey(key)
        ospp_path = None
        for base_path in [os.environ.get("ProgramFiles", "C:\\Program Files"), os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")]:
            for ver in ["Office16", "Office15", "Office14"]:
                path = os.path.join(base_path, "Microsoft Office", ver, "ospp.vbs")
                if os.path.exists(path):
                    ospp_path = path
                    break
            if ospp_path:
                break
        if ospp_path:
            license_output = subprocess.check_output(f'cscript //nologo "{ospp_path}" /dstatus', text=True)
            license_status = "Unknown"
            if "LICENSE STATUS:  ---LICENSED---" in license_output:
                license_status = "Activated"
            elif "LICENSE STATUS:  ---UNLICENSED---" in license_output:
                license_status = "Not Activated"
            elif "LICENSE STATUS:  ---GRACE---" in license_output:
                license_status = "In Grace Period (Trial or Expired)"
            match = re.search(r"Last 5 characters of installed product key: (\w{5})", license_output)
            if match:
                return f"Version: {office_version}, Edition: {office_edition}, License Status: {license_status}, Product Key (Last 5 chars): {match.group(1)}"
            return f"Version: {office_version}, Edition: {office_edition}, License Status: {license_status}"
        return f"Version: {office_version}, Edition: {office_edition}, License Status: Unable to verify (ospp.vbs not found)"
    except FileNotFoundError:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Office")
            subkeys = [winreg.EnumKey(key, i) for i in range(winreg.QueryInfoKey(key)[0]) if re.match(r"^\d+\.\d+$", winreg.EnumKey(key, i))]
            winreg.CloseKey(key)
            if subkeys:
                office_version = max(subkeys)
                return f"Version: {office_version}, Edition: Legacy Installation (Check Programs and Features for details), License Status: Unknown (Legacy installation; use ospp.vbs manually)"
            return "No Microsoft Office detected"
        except:
            return "No Microsoft Office detected"
    except Exception as e:
        return f"Error retrieving Microsoft Office details: {str(e)}"

office_details = get_office_details()

# Print Report
print("===== System Information Report =====")
print("----- Processor Details -----")
print(f"Processor Type: {cpu_info['name']}")
print(f"Manufacturer: {cpu_info['manufacturer']}")
print(f"Generation: {cpu_info['generation']}")
print(f"Current Speed: {cpu_info['speed']} GHz")
print(f"Max Speed: {cpu_info['max_speed']} GHz")
print(f"Cores: {cpu_info['cores']}")
print(f"Threads: {cpu_info['threads']}")
print(f"L1 Cache: {cpu_info['l1_cache']} KB")
print(f"L2 Cache: {cpu_info['l2_cache']} KB")
print(f"L3 Cache: {cpu_info['l3_cache']} KB")
print(f"Family (Decoded): {cpu_info['family']}")

print("\n----- RAM Details -----")
print(f"Total RAM: {ram_info['total']}")
print(f"RAM Type: {ram_info['type']}")
print(f"RAM Speed: {ram_info['speed']}")
print(f"RAM Manufacturer: {ram_info['manufacturer']}")
print(f"RAM Part Number: {ram_info['part_number']}")
print(f"RAM Serial Number: {ram_info['serial_number']}")

print("\n----- Motherboard Details -----")
print(f"Manufacturer: {mb_info['manufacturer']}")
print(f"Model: {mb_info['model']}")
print(f"Serial Number: {mb_info['serial_number']}")

print("\n----- Battery Details -----")
print(f"Battery Name: {battery_info['name']}")
print(f"Manufacturer: {battery_info['manufacturer']}")
print(f"Chemistry: {battery_info['chemistry']}")
print(f"Design Capacity: {battery_info['design_capacity_wh']} ({battery_info['design_capacity_mah']} mAh)")
print(f"Full Charge Capacity: {battery_info['full_capacity_wh']} ({battery_info['full_capacity_mah']} mAh)")
print(f"Battery Health: {battery_info['health']}")

print("\n----- Camera Details -----")
print(f"Camera Name: {camera_info['name']}")
print(f"Manufacturer: {camera_info['manufacturer']}")
print(f"Device ID: {camera_info['device_id']}")
print(f"Megapixels: {camera_info['megapixels']}")

print("\n----- SSD Details -----")
for ssd in ssd_details:
    print(ssd)

print("\n----- TPM Details -----")
print(f"TPM Present: {tpm_info['present']}")
print(f"TPM Version: {tpm_info['version']}")
print(f"TPM Status: {tpm_info['status']}")

print("\n----- UEFI Details -----")
print(f"UEFI Status: {uefi_info['status']}")
print(f"Secure Boot: {uefi_info['secure_boot']}")

print("\n----- Microsoft Office Details -----")
print(office_details)

print("\n----- Operating System Details -----")
print(f"OS: {os_info['version']}")
print(f"Build: {os_info['build']}")

print("===== End of Report =====")