# PowerShell script to gather and display detailed system information in a human-readable format

# Function to decode MemoryType into DDR type
function Get-MemoryType {
    param (
        [Parameter(Mandatory=$false)]
        [int]$MemoryType
    )
    switch ($MemoryType) {
        21 { return "DDR3" }
        24 { return "DDR4" }
        26 { return "DDR5" }
        default { return "Unknown (Type Code: $MemoryType)" }
    }
}

# Function to decode CPU Family and Model into generation
function Get-CpuGeneration {
    param (
        [Parameter(Mandatory=$true)]
        [string]$CpuName,
        [string]$Model
    )
    if ($CpuName -match "Intel") {
        if ($CpuName -match "i[3|5|7|9]-(\d)") {
            $gen = $matches[1]
            switch ($gen) {
                7 { return "7th Gen (Kaby Lake)" }
                8 { return "8th Gen (Coffee Lake)" }
                9 { return "9th Gen (Coffee Lake Refresh)" }
                10 { return "10th Gen (Comet Lake/Ice Lake)" }
                11 { return "11th Gen (Tiger Lake)" }
                12 { return "12th Gen (Alder Lake)" }
                13 { return "13th Gen (Raptor Lake)" }
                default { return "Generation $gen (Look up for exact architecture)" }
            }
        }
    }
    elseif ($CpuName -match "Ryzen") {
        if ($CpuName -match "Ryzen.*(\d{4})") {
            $series = $matches[1]
            switch ($series) {
                "1000" { return "Ryzen 1000 Series (Zen)" }
                "2000" { return "Ryzen 2000 Series (Zen+)" }
                "3000" { return "Ryzen 3000 Series (Zen 2)" }
                "5000" { return "Ryzen 5000 Series (Zen 3)" }
                "7000" { return "Ryzen 7000 Series (Zen 4)" }
                default { return "Ryzen Series $series (Look up for exact architecture)" }
            }
        }
    }
    return "Unknown Generation (Model: $Model)"
}

# Function to convert bytes to GB
function Convert-BytesToGB {
    param (
        [Parameter(Mandatory=$false)]
        [double]$Bytes
    )
    if (-not $Bytes -or $Bytes -eq 0) { return "0 GB" }
    return "{0:N2} GB" -f ($Bytes / 1GB)
}

# Function to estimate camera megapixels (simplified heuristic based on name)
function Get-CameraMegapixels {
    param (
        [Parameter(Mandatory=$false)]
        [string]$CameraName
    )
    if (-not $CameraName) { return "N/A" }
    if ($CameraName -match "HD" -or $CameraName -match "720p") {
        return "Approx. 1 MP (720p HD)"
    }
    elseif ($CameraName -match "1080p" -or $CameraName -match "Full HD") {
        return "Approx. 2 MP (1080p Full HD)"
    }
    elseif ($CameraName -match "4K" -or $CameraName -match "UHD") {
        return "Approx. 8 MP (4K UHD)"
    }
    else {
        return "Unknown (Megapixels not directly available via PowerShell)"
    }
}

# Function to convert Wh to mAh (requires voltage)
function Convert-WhToMAh {
    param (
        [Parameter(Mandatory=$false)]
        [double]$WattHours,
        [Parameter(Mandatory=$false)]
        [double]$Voltage
    )
    if (-not $WattHours -or -not $Voltage -or $WattHours -eq "N/A" -or $Voltage -eq 0) {
        return "N/A (Voltage or capacity data unavailable)"
    }
    $mAh = ($WattHours * 1000) / $Voltage
    return [math]::Round($mAh, 0)
}

# Gather CPU Information
$cpuInfo = @{}
try {
    $cpu = Get-CimInstance -ClassName Win32_Processor -ErrorAction Stop
    $cpuInfo = @{
        Name = $cpu.Name.Trim()
        Manufacturer = $cpu.Manufacturer
        Speed = "{0:N2}" -f ($cpu.CurrentClockSpeed / 1000)  # Convert MHz to GHz
        MaxSpeed = "{0:N2}" -f ($cpu.MaxClockSpeed / 1000)   # Convert MHz to GHz
        Cores = $cpu.NumberOfCores
        Threads = $cpu.NumberOfLogicalProcessors
        L1Cache = if ($cpu.L1CacheSize) { $cpu.L1CacheSize / 1024 } else { "Unknown" }  # Convert bytes to KB
        L2Cache = if ($cpu.L2CacheSize) { $cpu.L2CacheSize / 1024 } else { "Unknown" }
        L3Cache = if ($cpu.L3CacheSize) { $cpu.L3CacheSize / 1024 } else { "Unknown" }
        Family = $cpu.Caption
        Model = $cpu.ProcessorId
    }
    $cpuInfo.Generation = Get-CpuGeneration -CpuName $cpuInfo.Name -Model $cpuInfo.Model
}
catch {
    $cpuInfo = @{
        Name = "Error: $($_.Exception.Message)"
        Manufacturer = "N/A"
        Speed = "N/A"
        MaxSpeed = "N/A"
        Cores = "N/A"
        Threads = "N/A"
        L1Cache = "N/A"
        L2Cache = "N/A"
        L3Cache = "N/A"
        Family = "N/A"
        Model = "N/A"
        Generation = "N/A"
    }
}

# Gather RAM Information
$ramInfo = @{}
try {
    $ram = Get-CimInstance -ClassName Win32_PhysicalMemory -ErrorAction Stop
    $totalRamBytes = (Get-CimInstance -ClassName Win32_ComputerSystem).TotalPhysicalMemory
    $firstRamModule = $ram | Select-Object -First 1
    $ramInfo = @{
        Total = Convert-BytesToGB -Bytes $totalRamBytes
        Type = if ($firstRamModule) { Get-MemoryType -MemoryType $firstRamModule.SMBIOSMemoryType } else { "Unknown" }
        Speed = if ($firstRamModule -and $firstRamModule.Speed) { "$($firstRamModule.Speed) MHz" } else { "Unknown" }
        Manufacturer = if ($firstRamModule) { $firstRamModule.Manufacturer } else { "Unknown" }
        PartNumber = if ($firstRamModule) { $firstRamModule.PartNumber.Trim() } else { "Unknown" }
        SerialNumber = if ($firstRamModule) { $firstRamModule.SerialNumber.Trim() } else { "Unknown" }
    }
}
catch {
    $ramInfo = @{
        Total = "Error: $($_.Exception.Message)"
        Type = "N/A"
        Speed = "N/A"
        Manufacturer = "N/A"
        PartNumber = "N/A"
        SerialNumber = "N/A"
    }
}

# Gather Motherboard Information
$mbInfo = @{}
try {
    $motherboard = Get-CimInstance -ClassName Win32_BaseBoard -ErrorAction Stop
    $mbInfo = @{
        Manufacturer = $motherboard.Manufacturer
        Model = $motherboard.Product
        SerialNumber = $motherboard.SerialNumber.Trim()
    }
}
catch {
    $mbInfo = @{
        Manufacturer = "Error: $($_.Exception.Message)"
        Model = "N/A"
        SerialNumber = "N/A"
    }
}

# Gather OS Information
$osInfo = @{}
try {
    $os = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction Stop
    $osInfo = @{
        Version = $os.Caption
        Build = $os.BuildNumber
    }
}
catch {
    $osInfo = @{
        Version = "Error: $($_.Exception.Message)"
        Build = "N/A"
    }
}

# Gather Battery Information
$batteryInfo = @{}
try {
    $battery = Get-CimInstance -ClassName Win32_Battery -ErrorAction Stop
    $batteryStatic = Get-CimInstance -ClassName Win32_PortableBattery -ErrorAction Stop
    if ($battery -and $batteryStatic) {
        $designCapacity = $batteryStatic.DesignCapacity / 1000  # Convert mWh to Wh
        $fullCapacity = $batteryStatic.FullChargeCapacity / 1000  # Convert mWh to Wh
        $voltage = if ($batteryStatic.DesignVoltage) { $batteryStatic.DesignVoltage / 1000 } else { 3.7 }  # Convert mV to V, default 3.7V
        $batteryInfo = @{
            Name = $battery.Name
            Manufacturer = $batteryStatic.Manufacturer
            Chemistry = $batteryStatic.Chemistry
            DesignCapacityWh = "{0:N2}" -f $designCapacity
            FullCapacityWh = "{0:N2}" -f $fullCapacity
            DesignCapacityMAh = Convert-WhToMAh -WattHours $designCapacity -Voltage $voltage
            FullCapacityMAh = Convert-WhToMAh -WattHours $fullCapacity -Voltage $voltage
            Health = if ($fullCapacity -and $designCapacity) { [math]::Round(($fullCapacity / $designCapacity) * 100, 2) } else { "Unknown" }
        }
    }
    else {
        $batteryInfo = @{
            Name = "No battery detected"
            Manufacturer = "N/A"
            Chemistry = "N/A"
            DesignCapacityWh = "N/A"
            FullCapacityWh = "N/A"
            DesignCapacityMAh = "N/A"
            FullCapacityMAh = "N/A"
            Health = "N/A"
        }
    }
}
catch {
    $batteryInfo = @{
        Name = "Error: $($_.Exception.Message)"
        Manufacturer = "N/A"
        Chemistry = "N/A"
        DesignCapacityWh = "N/A"
        FullCapacityWh = "N/A"
        DesignCapacityMAh = "N/A"
        FullCapacityMAh = "N/A"
        Health = "N/A"
    }
}

# Gather Camera Information
$cameraInfo = @{}
try {
    $camera = Get-CimInstance -ClassName Win32_PnPEntity | Where-Object { $_.PNPClass -eq "Image" -or $_.PNPClass -eq "Camera" } -ErrorAction Stop
    if ($camera) {
        $firstCamera = $camera | Select-Object -First 1
        $cameraInfo = @{
            Name = $firstCamera.Name
            Manufacturer = $firstCamera.Manufacturer
            DeviceId = $firstCamera.DeviceID
            Megapixels = Get-CameraMegapixels -CameraName $firstCamera.Name
        }
    }
    else {
        $cameraInfo = @{
            Name = "No camera detected"
            Manufacturer = "N/A"
            DeviceId = "N/A"
            Megapixels = "N/A"
        }
    }
}
catch {
    $cameraInfo = @{
        Name = "Error: $($_.Exception.Message)"
        Manufacturer = "N/A"
        DeviceId = "N/A"
        Megapixels = "N/A"
    }
}

# Gather SSD Information
$ssdDetails = @()
try {
    $disks = Get-CimInstance -ClassName Win32_DiskDrive | Where-Object { $_.MediaType -eq "SSD" -or $_.Model -match "SSD" } -ErrorAction Stop
    if ($disks) {
        foreach ($disk in $disks) {
            $ssdDetails += "Model: $($disk.Model), Manufacturer: $($disk.Manufacturer), Size: $(Convert-BytesToGB -Bytes $disk.Size), Interface: $($disk.InterfaceType), Serial Number: $($disk.SerialNumber.Trim())"
        }
    }
    else {
        $ssdDetails = @("No SSD detected")
    }
}
catch {
    $ssdDetails = @("Error: $($_.Exception.Message)")
}

# Gather TPM Information
$tpmInfo = @{}
try {
    $tpm = Get-Tpm -ErrorAction Stop
    $tpmInfo = @{
        Present = $tpm.TpmPresent
        Ready = $tpm.TpmReady
        Version = if ($tpm.ManufacturerVersion) { $tpm.ManufacturerVersion } else { "Unknown" }
        Status = if ($tpm.TpmPresent -and $tpm.TpmReady) { "Enabled and Ready" } else { "Not Ready or Disabled" }
    }
}
catch {
    $tpmInfo = @{
        Present = $false
        Ready = $false
        Version = "N/A"
        Status = "No TPM detected"
    }
}

# Gather UEFI Status
$uefiInfo = @{}
try {
    $secureBoot = Confirm-SecureBootUEFI -ErrorAction Stop
    if ($secureBoot -eq $true) {
        $uefiInfo = @{
            Status = "Enabled (UEFI Mode with Secure Boot)"
            SecureBoot = "Enabled"
        }
    }
    elseif ($secureBoot -eq $false) {
        $uefiInfo = @{
            Status = "Enabled (UEFI Mode without Secure Boot)"
            SecureBoot = "Disabled"
        }
    }
}
catch {
    try {
        $firmwareType = (Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control" -ErrorAction Stop).SystemStartOptions
        if ($firmwareType -match "firmware=efi") {
            $uefiInfo = @{
                Status = "Enabled (UEFI Mode, Secure Boot status unknown)"
                SecureBoot = "Unknown (Unable to verify Secure Boot)"
            }
        }
        else {
            $uefiInfo = @{
                Status = "Disabled (Legacy/BIOS Mode)"
                SecureBoot = "N/A (Legacy Mode)"
            }
        }
    }
    catch {
        $uefiInfo = @{
            Status = "Error: $($_.Exception.Message)"
            SecureBoot = "Unknown"
        }
    }
}

# Gather Microsoft Office Version and License Details
$officeDetails = "No Microsoft Office detected"
try {
    $officeRegPath = "HKLM:\Software\Microsoft\Office"
    $clickToRunRegPath = "HKLM:\Software\Microsoft\Office\ClickToRun\Configuration"
    if (Test-Path $clickToRunRegPath) {
        $officeConfig = Get-ItemProperty -Path $clickToRunRegPath -ErrorAction Stop
        $officeVersion = $officeConfig.ProductReleaseIds  # e.g., O365ProPlusRetail, ProPlus2019Retail
        $officeEdition = $officeConfig.ProductReleaseIds
        # Check license status using ospp.vbs
        $osppPath = Join-Path $env:ProgramFiles "Microsoft Office\Office*\ospp.vbs"
        if (-not (Test-Path $osppPath)) {
            $osppPath = Join-Path ${env:ProgramFiles(x86)} "Microsoft Office\Office*\ospp.vbs"
        }
        if (Test-Path $osppPath) {
            $licenseOutput = cscript //nologo $osppPath /dstatus | Out-String
            $officeLicenseStatus = "Unknown"
            if ($licenseOutput -match "LICENSE STATUS:  ---LICENSED---") {
                $officeLicenseStatus = "Activated"
            }
            elseif ($licenseOutput -match "LICENSE STATUS:  ---UNLICENSED---") {
                $officeLicenseStatus = "Not Activated"
            }
            elseif ($licenseOutput -match "LICENSE STATUS:  ---GRACE---") {
                $officeLicenseStatus = "In Grace Period (Trial or Expired)"
            }
            if ($licenseOutput -match "Last 5 characters of installed product key: (\w{5})") {
                $officeProductKey = $matches[1]
                $officeDetails = "Version: $officeVersion, Edition: $officeEdition, License Status: $officeLicenseStatus, Product Key (Last 5 chars): $officeProductKey"
            }
            else {
                $officeDetails = "Version: $officeVersion, Edition: $officeEdition, License Status: $officeLicenseStatus"
            }
        }
        else {
            $officeDetails = "Version: $officeVersion, Edition: $officeEdition, License Status: Unable to verify (ospp.vbs not found)"
        }
    }
    elseif (Test-Path $officeRegPath) {
        $officeVersion = (Get-ChildItem $officeRegPath | Where-Object { $_.PSChildName -match "^\d+\.\d+$" } | Sort-Object PSChildName -Descending | Select-Object -First 1).PSChildName
        $officeEdition = "Legacy Installation (Check Programs and Features for details)"
        $officeLicenseStatus = "Unknown (Legacy installation; use ospp.vbs manually)"
        $officeDetails = "Version: $officeVersion, Edition: $officeEdition, License Status: $officeLicenseStatus"
    }
}
catch {
    $officeDetails = "Error retrieving Microsoft Office details: $($_.Exception.Message)"
}

# Display Results in Human-Readable Format
Write-Host "===== System Information Report =====" -ForegroundColor Cyan
Write-Host "----- Processor Details -----" -ForegroundColor Green
Write-Host "Processor Type: $($cpuInfo.Name)"
Write-Host "Manufacturer: $($cpuInfo.Manufacturer)"
Write-Host "Generation: $($cpuInfo.Generation)"
Write-Host "Current Speed: $($cpuInfo.Speed) GHz"
Write-Host "Max Speed: $($cpuInfo.MaxSpeed) GHz"
Write-Host "Cores: $($cpuInfo.Cores)"
Write-Host "Threads: $($cpuInfo.Threads)"
Write-Host "L1 Cache: $($cpuInfo.L1Cache) KB"
Write-Host "L2 Cache: $($cpuInfo.L2Cache) KB"
Write-Host "L3 Cache: $($cpuInfo.L3Cache) KB"
Write-Host "Family (Decoded): $($cpuInfo.Family)"

Write-Host "----- RAM Details -----" -ForegroundColor Green
Write-Host "Total RAM: $($ramInfo.Total)"
Write-Host "RAM Type: $($ramInfo.Type)"
Write-Host "RAM Speed: $($ramInfo.Speed)"
Write-Host "RAM Manufacturer: $($ramInfo.Manufacturer)"
Write-Host "RAM Part Number: $($ramInfo.PartNumber)"
Write-Host "RAM Serial Number: $($ramInfo.SerialNumber)"

Write-Host "----- Motherboard Details -----" -ForegroundColor Green
Write-Host "Manufacturer: $($mbInfo.Manufacturer)"
Write-Host "Model: $($mbInfo.Model)"
Write-Host "Serial Number: $($mbInfo.SerialNumber)"

Write-Host "----- Battery Details -----" -ForegroundColor Green
Write-Host "Battery Name: $($batteryInfo.Name)"
Write-Host "Manufacturer: $($batteryInfo.Manufacturer)"
Write-Host "Chemistry: $($batteryInfo.Chemistry)"
Write-Host "Design Capacity: $($batteryInfo.DesignCapacityWh) Wh ($($batteryInfo.DesignCapacityMAh) mAh)"
Write-Host "Full Charge Capacity: $($batteryInfo.FullCapacityWh) Wh ($($batteryInfo.FullCapacityMAh) mAh)"
Write-Host "Battery Health: $($batteryInfo.Health) %"

Write-Host "----- Camera Details -----" -ForegroundColor Green
Write-Host "Camera Name: $($cameraInfo.Name)"
Write-Host "Manufacturer: $($cameraInfo.Manufacturer)"
Write-Host "Device ID: $($cameraInfo.DeviceId)"
Write-Host "Megapixels: $($cameraInfo.Megapixels)"

Write-Host "----- SSD Details -----" -ForegroundColor Green
foreach ($ssd in $ssdDetails) {
    Write-Host $ssd
}

Write-Host "----- TPM Details -----" -ForegroundColor Green
Write-Host "TPM Present: $($tpmInfo.Present)"
Write-Host "TPM Version: $($tpmInfo.Version)"
Write-Host "TPM Status: $($tpmInfo.Status)"

Write-Host "----- UEFI Details -----" -ForegroundColor Green
Write-Host "UEFI Status: $($uefiInfo.Status)"
Write-Host "Secure Boot: $($uefiInfo.SecureBoot)"

Write-Host "----- Microsoft Office Details -----" -ForegroundColor Green
Write-Host $officeDetails

Write-Host "----- Operating System Details -----" -ForegroundColor Green
Write-Host "OS: $($osInfo.Version)"
Write-Host "Build: $($osInfo.Build)"

Write-Host "===== End of Report =====" -ForegroundColor Cyan