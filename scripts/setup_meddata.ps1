# PowerShell script to set up MedData Azure SQL Database
# This script configures environment variables and runs the Python setup script

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  MedData Azure SQL Database Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8 or later." -ForegroundColor Red
    exit 1
}

# Prompt for required information
Write-Host "`nPlease provide the following information:" -ForegroundColor Yellow
Write-Host ""

$subscriptionId = Read-Host "Azure Subscription ID"
$resourceGroup = Read-Host "Resource Group Name (default: meddata-rg)" 
if ([string]::IsNullOrWhiteSpace($resourceGroup)) { $resourceGroup = "meddata-rg" }

$serverName = Read-Host "SQL Server Name (default: meddata-sql-server)"
if ([string]::IsNullOrWhiteSpace($serverName)) { $serverName = "meddata-sql-server" }

$location = Read-Host "Azure Region (default: eastus)"
if ([string]::IsNullOrWhiteSpace($location)) { $location = "eastus" }

$adminUsername = Read-Host "SQL Admin Username (default: sqladmin)"
if ([string]::IsNullOrWhiteSpace($adminUsername)) { $adminUsername = "sqladmin" }

$securePassword = Read-Host "SQL Admin Password (must be strong)" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
$adminPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

# Validate password strength (basic check)
if ($adminPassword.Length -lt 8) {
    Write-Host "`n✗ Password must be at least 8 characters long" -ForegroundColor Red
    exit 1
}

Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "  Configuration Summary" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Subscription ID: $subscriptionId"
Write-Host "Resource Group:  $resourceGroup"
Write-Host "SQL Server:      $serverName"
Write-Host "Database:        MedData"
Write-Host "Location:        $location"
Write-Host "Admin Username:  $adminUsername"
Write-Host ""

$confirm = Read-Host "Proceed with setup? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "Setup cancelled." -ForegroundColor Yellow
    exit 0
}

# Set environment variables
$env:AZURE_SUBSCRIPTION_ID = $subscriptionId
$env:RESOURCE_GROUP = $resourceGroup
$env:SQL_SERVER_NAME = $serverName
$env:AZURE_LOCATION = $location
$env:SQL_ADMIN_USERNAME = $adminUsername
$env:SQL_ADMIN_PASSWORD = $adminPassword

Write-Host "`nStep 1: Installing required Python packages..." -ForegroundColor Cyan
pip install -r scripts/meddata_requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "`nStep 2: Logging in to Azure (if not already authenticated)..." -ForegroundColor Cyan
az account show 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Not logged in. Running 'az login'..." -ForegroundColor Yellow
    az login
}

Write-Host "`nStep 3: Setting Azure subscription..." -ForegroundColor Cyan
az account set --subscription $subscriptionId

Write-Host "`nStep 4: Running database setup script..." -ForegroundColor Cyan
python scripts/setup_meddata_database.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n================================================" -ForegroundColor Green
    Write-Host "  ✓ MedData Database Setup Complete!" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Server:   $serverName.database.windows.net" -ForegroundColor White
    Write-Host "Database: MedData" -ForegroundColor White
    Write-Host "Tables:   MED_SLOTS (13 rows), MED (155 rows)" -ForegroundColor White
    Write-Host ""
    Write-Host "Connection string:" -ForegroundColor Yellow
    Write-Host "Server=$serverName.database.windows.net;Database=MedData;User Id=$adminUsername;Password=***;" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "`n✗ Setup failed. Please check the error messages above." -ForegroundColor Red
    exit 1
}
