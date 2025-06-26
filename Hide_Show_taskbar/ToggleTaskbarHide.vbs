Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File ""D:\Miscc\Hide_Show_taskbar\ToggleTaskbarHide.ps1""", 0, True