# =============================================================================
# Dental AI Voice Agent - Development Startup Script
# =============================================================================
# This script starts:
# 1. FastAPI server (uvicorn)
# 2. ngrok tunnel for Twilio webhooks
# 3. Updates Twilio webhook automatically
# =============================================================================

param(
    [int]$Port = 8000,
    [switch]$SkipTwilioUpdate
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Dental AI Voice Agent"

# Colors
function Write-Header { param($msg) Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "[✓] $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "[i] $msg" -ForegroundColor Yellow }
function Write-Err { param($msg) Write-Host "[✗] $msg" -ForegroundColor Red }

# Load environment
Write-Header "Loading Environment"
$envPath = Join-Path $PSScriptRoot ".env"
if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
    Write-Success "Loaded .env file"
} else {
    Write-Err ".env file not found!"
    exit 1
}

# Check required env vars
$requiredVars = @("DEEPGRAM_API_KEY", "OPENAI_API_KEY", "TWILIO_SID", "TWILIO_TOKEN", "TWILIO_NUMBER")
foreach ($var in $requiredVars) {
    $val = [Environment]::GetEnvironmentVariable($var, "Process")
    if (-not $val -or $val -like "*your-*") {
        Write-Err "Missing or invalid: $var"
        exit 1
    }
}
Write-Success "All required environment variables present"

# Check for existing processes
Write-Header "Checking for Existing Processes"
$existingUvicorn = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" }
if ($existingUvicorn) {
    Write-Info "Stopping existing uvicorn process..."
    $existingUvicorn | Stop-Process -Force
}

$existingNgrok = Get-Process -Name "ngrok" -ErrorAction SilentlyContinue
if ($existingNgrok) {
    Write-Info "Stopping existing ngrok process..."
    $existingNgrok | Stop-Process -Force
}

# Start FastAPI server
Write-Header "Starting FastAPI Server"
$serverJob = Start-Job -ScriptBlock {
    param($workDir, $port)
    Set-Location $workDir
    & python -m uvicorn api_main:app --host 0.0.0.0 --port $port --reload
} -ArgumentList $PSScriptRoot, $Port

Write-Success "FastAPI server starting on port $Port..."
Start-Sleep -Seconds 3

# Check if server is responding
try {
    $response = Invoke-RestMethod -Uri "http://localhost:$Port/" -Method GET -TimeoutSec 5
    Write-Success "Server is up: $($response.message)"
} catch {
    Write-Err "Server failed to start. Check logs."
    Receive-Job $serverJob
    exit 1
}

# Start ngrok tunnel
Write-Header "Starting ngrok Tunnel"

# Kill any existing ngrok first
Get-Process -Name "ngrok" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# Start ngrok in background
$ngrokProcess = Start-Process -FilePath "ngrok" -ArgumentList "http", $Port, "--log=stdout" -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 3

# Get ngrok public URL
try {
    $tunnels = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -TimeoutSec 5
    $publicUrl = $tunnels.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1 -ExpandProperty public_url
    
    if (-not $publicUrl) {
        throw "No HTTPS tunnel found"
    }
    
    Write-Success "ngrok tunnel: $publicUrl"
    
    # Update .env with new URL
    $envContent = Get-Content $envPath -Raw
    if ($envContent -match "API_BASE_URL=.*") {
        $envContent = $envContent -replace "API_BASE_URL=.*", "API_BASE_URL=$publicUrl"
        Set-Content $envPath $envContent -NoNewline
        Write-Success "Updated API_BASE_URL in .env"
    }
    
} catch {
    Write-Err "Failed to get ngrok URL. Is ngrok authenticated?"
    Write-Info "Run: ngrok config add-authtoken YOUR_TOKEN"
    Write-Info "Get token from: https://dashboard.ngrok.com/get-started/your-authtoken"
    exit 1
}

# Update Twilio webhook
if (-not $SkipTwilioUpdate) {
    Write-Header "Updating Twilio Webhook"
    
    $twilioSid = [Environment]::GetEnvironmentVariable("TWILIO_SID", "Process")
    $twilioToken = [Environment]::GetEnvironmentVariable("TWILIO_TOKEN", "Process")
    $twilioNumber = [Environment]::GetEnvironmentVariable("TWILIO_NUMBER", "Process")
    
    $webhookUrl = "$publicUrl/inbound/voice"
    
    # Get phone number SID
    $authPair = "${twilioSid}:${twilioToken}"
    $authBytes = [System.Text.Encoding]::ASCII.GetBytes($authPair)
    $authBase64 = [Convert]::ToBase64String($authBytes)
    $headers = @{
        "Authorization" = "Basic $authBase64"
    }
    
    try {
        # List phone numbers to get the SID
        $numbersUrl = "https://api.twilio.com/2010-04-01/Accounts/$twilioSid/IncomingPhoneNumbers.json?PhoneNumber=$([uri]::EscapeDataString($twilioNumber))"
        $numbers = Invoke-RestMethod -Uri $numbersUrl -Headers $headers -Method GET
        
        if ($numbers.incoming_phone_numbers.Count -eq 0) {
            throw "Phone number not found: $twilioNumber"
        }
        
        $phoneSid = $numbers.incoming_phone_numbers[0].sid
        
        # Update the voice URL
        $updateUrl = "https://api.twilio.com/2010-04-01/Accounts/$twilioSid/IncomingPhoneNumbers/$phoneSid.json"
        $body = @{
            VoiceUrl = $webhookUrl
            VoiceMethod = "POST"
        }
        
        $result = Invoke-RestMethod -Uri $updateUrl -Headers $headers -Method POST -Body $body
        Write-Success "Twilio webhook updated: $webhookUrl"
        
    } catch {
        Write-Err "Failed to update Twilio webhook: $_"
        Write-Info "Please update manually in Twilio Console"
    }
}

# Display summary
Write-Header "Ready!"
Write-Host ""
Write-Host "  Server:    http://localhost:$Port" -ForegroundColor White
Write-Host "  Public:    $publicUrl" -ForegroundColor White
Write-Host "  Docs:      http://localhost:$Port/docs" -ForegroundColor White
Write-Host "  Webhook:   $publicUrl/inbound/voice" -ForegroundColor White
Write-Host "  Phone:     $([Environment]::GetEnvironmentVariable('TWILIO_NUMBER', 'Process'))" -ForegroundColor White
Write-Host ""
Write-Host "  Call your Twilio number to test!" -ForegroundColor Green
Write-Host ""
Write-Host "  Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# Keep script running and show server logs
try {
    while ($true) {
        if ($serverJob.State -eq "Completed" -or $serverJob.State -eq "Failed") {
            Write-Err "Server stopped unexpectedly"
            Receive-Job $serverJob
            break
        }
        
        # Show any new output from server
        Receive-Job $serverJob -Keep | ForEach-Object { Write-Host $_ }
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Header "Shutting Down"
    
    # Stop server
    if ($serverJob) {
        Stop-Job $serverJob -ErrorAction SilentlyContinue
        Remove-Job $serverJob -ErrorAction SilentlyContinue
        Write-Info "Stopped FastAPI server"
    }
    
    # Stop ngrok
    if ($ngrokProcess -and -not $ngrokProcess.HasExited) {
        Stop-Process $ngrokProcess -Force -ErrorAction SilentlyContinue
        Write-Info "Stopped ngrok"
    }
    
    Write-Success "Cleanup complete"
}
