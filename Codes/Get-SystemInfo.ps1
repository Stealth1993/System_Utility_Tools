# PowerShell script to gather and display detailed system information in a human-readable format

# Function to decode MemoryType into DDR type
function Get-MemoryType ($memoryType) {
    switch ($memoryType) {
        21 { return "DDR3" }
        24 { return "DDR4" }
        26 { return "DDR5" }
        default { return "Unknown (Type Code: $memoryType)" }
    }
}

# Function to decode CPU Family and Model into generation (simplified)
function Get-CpuGeneration ($cpuName, $model) {
    if ($cpuName -match "Intel") {
        # Extract generation from model name (e.g., i5-7300U -> 7th Gen)
        if ($cpuName -match "i[3|5|7|9]-(\d)") {
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
    } elseif ($cpuName -match "Ryzen") {
        # Extract Ryzen series (e.g., Ryzen 5 5600X -> 5000 series)
        if ($cpuName -match "Ryzen.*(\d{4})") {
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
    return "Unknown Generation (Model: $model)"
}

# Gather CPU Information
$cpu = Get-CimInstance Win32_Processor
$cpuName = $cpu.Name
$cpuSpeed = $cpu.CurrentClockSpeed / 1000  # Convert MHz to GHz
$cpuMaxSpeed = $cpu.MaxClockSpeed / 1000   # Convert MHz to GHz
$cpuCores = $cpu.NumberOfCores
$cpuThreads = $cpu.NumberOfLogicalProcessors
$cpuL1Cache = ($cpu.L1CacheSize / 1024)  # Convert bytes to KB
$cpuL2Cache = ($cpu.L2CacheSize / 1024)  # Convert bytes to KB
$cpuL3Cache = ($cpu.L3CacheSize / 1024)  # Convert bytes to KB
$cpuFamily = $cpu.Caption
$cpuGeneration = Get-CpuGeneration -cpuName $cpuName -model $cpu.Model

# Gather RAM Information
$ram = Get-CimInstance Win32_PhysicalMemory
$totalRam = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB  # Convert bytes to GB
$ramType = Get-MemoryType -memoryType $ram[0].MemoryType
$ramSpeed = $ram[0].Speed  # In MHz
$ramManufacturer = $ram[0].Manufacturer
$ramPartNumber = $ram[0].PartNumber

# Gather OS Information
$os = Get-CimInstance Win32_OperatingSystem
$osVersion = $os.Caption
$osBuild = $os.BuildNumber

# Gather Motherboard Information
$motherboard = Get-CimInstance Win32_BaseBoard
$mbManufacturer = $motherboard.Manufacturer
$mbModel = $motherboard.Product

# Display Results in Human-Readable Format
Write-Host "===== System Information Report =====" -ForegroundColor Cyan
Write-Host "----- Processor Details -----" -ForegroundColor Green
Write-Host "Processor Type: $cpuName"
Write-Host "Generation: $cpuGeneration"
Write-Host "Current Speed: $cpuSpeed GHz"
Write-Host "Max Speed: $cpuMaxSpeed GHz"
Write-Host "Cores: $cpuCores"
Write-Host "Threads: $cpuThreads"
Write-Host "L1 Cache: $cpuL1Cache KB"
Write-Host "L2 Cache: $cpuL2Cache KB"
Write-Host "L3 Cache: $cpuL3Cache KB"
Write-Host "Family (Decoded): $cpuFamily"

Write-Host "----- RAM Details -----" -ForegroundColor Green
Write-Host "Total RAM: $totalRam GB"
Write-Host "RAM Type: $ramType"
Write-Host "RAM Speed: $ramSpeed MHz"
Write-Host "RAM Manufacturer: $ramManufacturer"
Write-Host "RAM Part Number: $ramPartNumber"

Write-Host "----- Motherboard Details -----" -ForegroundColor Green
Write-Host "Manufacturer: $mbManufacturer"
Write-Host "Model: $mbModel"

Write-Host "----- Operating System Details -----" -ForegroundColor Green
Write-Host "OS: $osVersion"
Write-Host "Build: $osBuild"

Write-Host "===== End of Report =====" -ForegroundColor Cyan