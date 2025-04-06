import wmi
import wx
import wx.lib.agw.shapedbutton as SB

class SystemInfoFrame(wx.Frame):
    def __init__(self):
        if not wx.GetApp():
            self.app = wx.App(False)
        else:
            self.app = wx.GetApp()

        super().__init__(None, title="System Information", size=(500, 500))
        
        self.c = wmi.WMI()
        panel = wx.Panel(self)
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Custom shaped buttons with different colors
        os_button = SB.SButton(panel, label="OS Info", size=(100, 50))
        os_button.Refresh()
        os_button.Bind(wx.EVT_BUTTON, self.on_os_info)

        sys_button = SB.SButton(panel, label="System Info", size=(100, 50))
        sys_button.Refresh()
        sys_button.Bind(wx.EVT_BUTTON, self.on_sys_info)

        cpu_button = SB.SButton(panel, label="CPU Info", size=(100, 50))
        cpu_button.Refresh()
        cpu_button.Bind(wx.EVT_BUTTON, self.on_cpu_info)

        network_button = SB.SButton(panel, label="Network Info", size=(100, 50))
        network_button.Refresh()
        network_button.Bind(wx.EVT_BUTTON, self.on_network_info)

        button_sizer.Add(os_button, 0, wx.ALL, 5)
        button_sizer.Add(sys_button, 0, wx.ALL, 5)
        button_sizer.Add(cpu_button, 0, wx.ALL, 5)
        button_sizer.Add(network_button, 0, wx.ALL, 5)

        main_sizer.Add(button_sizer, 0, wx.CENTER)
        
        # Decorative elements
        static_line = wx.StaticLine(panel)
        main_sizer.Add(static_line, 0, wx.EXPAND | wx.ALL, 5)
        
        # Static text for instructions
        instructions = wx.StaticText(panel, label="Click buttons to get system details:")
        main_sizer.Add(instructions, 0, wx.ALL | wx.CENTER, 5)

        panel.SetSizer(main_sizer)
        
        self.SetBackgroundColour(wx.Colour(240, 240, 255))  # Soft blue background

    def on_os_info(self, event):
        details = self.fetch_os_details()
        self.show_details("OS Information", details)

    def on_sys_info(self, event):
        details = self.fetch_hw_details()
        self.show_details("System Information", details)

    def on_cpu_info(self, event):
        details = self.fetch_cpu_details()
        self.show_details("CPU Information", details)

    def on_network_info(self, event):
        details = self.fetch_network_details()
        self.show_details("Network Information", details)

    def fetch_os_details(self):
        os_info = self.c.Win32_OperatingSystem()[0]
        return f"""
OS Name: {os_info.Name.split('|')[0]}
Version: {os_info.Version}
Manufacturer: {os_info.Manufacturer}
Architecture: {os_info.OSArchitecture}
Boot Device: {os_info.BootDevice}
System Drive: {os_info.SystemDrive}
Total Visible Memory: {int(os_info.TotalVisibleMemorySize) // 1024} MB
Free Physical Memory: {int(os_info.FreePhysicalMemory) // 1024} MB
Windows Directory: {os_info.WindowsDirectory}
""".strip()

    def fetch_hw_details(self):
        computer_info = self.c.Win32_ComputerSystem()[0]
        bios_info = self.c.Win32_BIOS()[0]
        
        disk_details = self.get_disk_info()
        
        return f"""
Manufacturer: {computer_info.Manufacturer}
Model: {computer_info.Model}
Serial Number: {bios_info.SerialNumber}
Number of Processors: {computer_info.NumberOfProcessors}
System Type: {computer_info.SystemType}
BIOS Version: {bios_info.SMBIOSBIOSVersion}
Total Physical Memory: {int(computer_info.TotalPhysicalMemory) // (1024**2)} MB
Domain Name: {computer_info.Domain}
{disk_details}
""".strip()

    def get_disk_info(self):
        disk_info = ""
        for disk in self.c.Win32_LogicalDisk(DriveType=3):  # DriveType 3 corresponds to local disks
            total_size = int(disk.Size) // (1024**3)  # Convert to GB
            free_space = int(disk.FreeSpace) // (1024**3)  # Convert to GB
            disk_info += f"\nDisk {disk.DeviceID} ({disk.MediaType}):\n"
            disk_info += f"  Total Size: {total_size} GB\n"
            disk_info += f"  Free Space: {free_space} GB\n"
        
        return disk_info.strip()

    def fetch_cpu_details(self):
        cpu_info = self.c.Win32_Processor()[0]
        return f"""
CPU Name: {cpu_info.Name}
Number of Cores: {cpu_info.NumberOfCores}
Number of Logical Processors: {cpu_info.NumberOfLogicalProcessors}
Current Clock Speed: {cpu_info.CurrentClockSpeed} MHz
Max Clock Speed: {cpu_info.MaxClockSpeed} MHz
L2 Cache Size: {cpu_info.L2CacheSize} KB
""".strip()

    def fetch_network_details(self):
        network_info = ""
        for adapter in self.c.Win32_NetworkAdapterConfiguration(IPEnabled=True):
            network_info += f"""
Network Adapter: {adapter.Description}
MAC Address: {adapter.MACAddress}
IP Address: {', '.join(adapter.IPAddress) if adapter.IPAddress else 'None'}
Subnet Mask: {adapter.IPSubnet[0] if adapter.IPSubnet else 'None'}
Default Gateway: {', '.join(adapter.DefaultIPGateway) if adapter.DefaultIPGateway else 'None'}
DNS Servers: {', '.join(adapter.DNSServerSearchOrder) if adapter.DNSServerSearchOrder else 'None'}
"""
        return network_info.strip()

    def show_details(self, title, details):
        info_frame = wx.Frame(self, title=title, size=(400, 300))
        text_ctrl = wx.TextCtrl(info_frame, style=wx.TE_MULTILINE|wx.TE_READONLY)
        text_ctrl.SetValue(details)
        
        copy_button = wx.Button(info_frame, label="Copy to Clipboard")
        copy_button.Bind(wx.EVT_BUTTON, lambda e: wx.TheClipboard.SetData(wx.TextDataObject(details)))
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(text_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(copy_button, 0, wx.ALL | wx.CENTER, 5)
        
        info_frame.SetSizer(sizer)
        info_frame.Show()

def main():
    if not wx.GetApp():
        app = wx.App(False)
    else:
        app = wx.GetApp()
    
    frame = SystemInfoFrame()
    frame.Show()
    app.MainLoop()

if __name__ == "__main__":
    main()

#pip install wxPython
#pip install pyinstaller
#pyinstaller --noconfirm --onefile --windowed your_script_name.py
#pyinstaller --noconfirm --onefile --windowed --icon=blank_green.ico sysinfo_v2.py