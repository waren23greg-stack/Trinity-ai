.SYNOPSIS
    Nightingale-AI: Restart Print Spooler Service
.DESCRIPTION
    Restarts the Windows Print Spooler service on a remote machine.
    Clears stuck print jobs and resets the spooler to a clean state.
    Returns structured JSON for orchestrator consumption.
.PARAMETER ComputerName
    Target machine (default: localhost)
.PARAMETER ClearQueue
    If $true, deletes all stuck print jobs (default: $false)
.OUTPUTS
    JSON object: { status, action, spooler_state, queue_cleared, error }
#>

param(
    [string]$ComputerName = "localhost",
    [bool]$ClearQueue = $false
)

$ErrorActionPreference = "Stop"
$result = @{
    status = "failure"
    action = "restart_spooler"
    computer = $ComputerName
    spooler_state = "unknown"
    queue_cleared = $false
    error = $null
    duration_seconds = 0
}

$startTime = Get-Date

try {
    # ===== STEP 1: CHECK CURRENT STATE =====
    Write-Host "[Nightingale] Checking spooler state on $ComputerName..."
    $spooler = Get-Service -Name Spooler -ComputerName $ComputerName -ErrorAction Stop
    
    if ($spooler.Status -eq "Running" -and -not $ClearQueue) {
        # Spooler is running. Don't restart unless we need to clear the queue.
        $result.status = "success"
        $result.spooler_state = "running"
        $result.error = $null
        Write-Host "[Nightingale] Spooler already running. No action needed."
        return $result | ConvertTo-Json -Compress
    }

    # ===== STEP 2: STOP SPOOLER =====
    Write-Host "[Nightingale] Stopping spooler..."
    Stop-Service -Name Spooler -ComputerName $ComputerName -Force -ErrorAction Stop
    
    # Wait for service to fully stop (max 10 seconds)
    $timeout = 10
    $elapsed = 0
    while ((Get-Service -Name Spooler -ComputerName $ComputerName).Status -ne "Stopped" -and $elapsed -lt $timeout) {
        Start-Sleep -Seconds 1
        $elapsed++
    }

    # ===== STEP 3: CLEAR PRINT QUEUE (OPTIONAL) =====
    if ($ClearQueue) {
        Write-Host "[Nightingale] Clearing print queue..."
        $spoolPath = "\\$ComputerName\C$\Windows\System32\spool\PRINTERS"
        
        if (Test-Path $spoolPath) {
            Get-ChildItem -Path $spoolPath -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
            $result.queue_cleared = $true
            Write-Host "[Nightingale] Print queue cleared."
        }
    }

    # ===== STEP 4: START SPOOLER =====
    Write-Host "[Nightingale] Starting spooler..."
    Start-Service -Name Spooler -ComputerName $ComputerName -ErrorAction Stop
    
    # Wait for service to be running (max 10 seconds)
    $elapsed = 0
    while ((Get-Service -Name Spooler -ComputerName $ComputerName).Status -ne "Running" -and $elapsed -lt $timeout) {
        Start-Sleep -Seconds 1
        $elapsed++
    }

    # ===== STEP 5: VERIFY =====
    $finalState = (Get-Service -Name Spooler -ComputerName $ComputerName).Status
    
    if ($finalState -eq "Running") {
        $result.status = "success"
        $result.spooler_state = "running"
        Write-Host "[Nightingale] Spooler restarted successfully."
    } else {
        $result.error = "Spooler failed to start. State: $finalState"
        Write-Host "[Nightingale] ERROR: $($result.error)"
    }

} catch {
    $result.status = "failure"
    $result.error = $_.Exception.Message
    Write-Error "[Nightingale] Exception: $($result.error)"
} finally {
    $result.duration_seconds = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 2)
}

# Return structured JSON for orchestrator
return $result | ConvertTo-Json -Compress
