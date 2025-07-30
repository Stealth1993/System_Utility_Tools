$p = 'HKCU:SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StuckRects3'
$v = (Get-ItemProperty -Path $p).Settings
if ($v[8] -eq 2) {
    $v[8] = 3  # Enable auto-hide
} else {
    $v[8] = 2  # Disable auto-hide
}
Set-ItemProperty -Path $p -Name Settings -Value $v
Stop-Process -f -ProcessName explorer