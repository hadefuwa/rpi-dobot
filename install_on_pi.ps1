# PowerShell script to SSH into Pi and install dependencies
$hostname = "rpi"
$username = "pi"
$password = "1"

# Create SSH command
$sshCommand = @"
cd ~/rpi-dobot/pwa-dobot-plc/backend
python3 -m pip install --upgrade pip
pip3 install opencv-python>=4.8.0 numpy>=1.24.0
echo 'Installation complete!'
"@

# Try using plink if available
$plinkPath = Get-Command plink -ErrorAction SilentlyContinue
if ($plinkPath) {
    Write-Host "Using plink to connect..."
    $sshCommand | & plink -ssh "$username@$hostname" -pw $password
} else {
    Write-Host "plink not found. Trying SSH with key-based auth or manual connection..."
    Write-Host "Please run the following commands manually on the Pi:"
    Write-Host ""
    Write-Host "cd ~/rpi-dobot/pwa-dobot-plc/backend"
    Write-Host "python3 -m pip install --upgrade pip"
    Write-Host "pip3 install opencv-python>=4.8.0 numpy>=1.24.0"
}

