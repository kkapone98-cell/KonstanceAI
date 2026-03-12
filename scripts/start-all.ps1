$ROOT = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $ROOT

$escapedRoot = [Regex]::Escape($ROOT)

# Kill all same-root and cross-root Konstance runtime processes to avoid split-brain and lock contention.
$killTargets = Get-CimInstance Win32_Process | Where-Object {
    (
        ($_.Name -like "python*" -and $_.CommandLine -match "bot\.py|launcher\.py|scripts\\job_worker\.py|scripts\\cloud_relay_probe\.py") -or
        ($_.Name -like "powershell*" -and $_.CommandLine -match "run-forever\.ps1|start-worker\.ps1|start-cloud-monitor\.ps1")
    ) -and $_.CommandLine -match "KonstanceAI"
}

# Also remove module-launched workers that may not contain full root path in commandline.
$moduleWorkers = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -like "python*" -and $_.CommandLine -match "(^| )-m scripts\.job_worker($| )"
}
$killTargets = @($killTargets) + @($moduleWorkers)
foreach ($p in $killTargets) {
    try {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
        Write-Host ("Stopped old Konstance process PID {0}" -f $p.ProcessId)
    } catch {
        Write-Host ("Could not stop PID {0}: {1}" -f $p.ProcessId, $_.Exception.Message)
    }
}

# Ensure Ollama service is up for local model fallback.
$ollamaOk = $false
try {
    $tcp = Test-NetConnection -ComputerName 127.0.0.1 -Port 11434 -WarningAction SilentlyContinue
    $ollamaOk = [bool]$tcp.TcpTestSucceeded
} catch {}
if (-not $ollamaOk) {
    $ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
    if ($ollamaCmd) {
        Start-Process $ollamaCmd.Source -ArgumentList "serve" -WindowStyle Minimized | Out-Null
        Write-Host "Started Ollama local server."
    } else {
        Write-Host "Ollama command not found."
    }
}

# Try OpenClaw bootstrap only if relay is down and CLI exists.
$relayOk = $false
try {
    $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 -Method GET -Uri "http://127.0.0.1:18789/health"
    $relayOk = ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300)
} catch {}
if (-not $relayOk) {
    $openclawCmd = Get-Command openclaw -ErrorAction SilentlyContinue
    if ($openclawCmd) {
        Start-Process $openclawCmd.Source -ArgumentList "start" -WindowStyle Minimized | Out-Null
        Write-Host "Attempted OpenClaw start."
        Start-Sleep -Seconds 2
    } else {
        Write-Host "OpenClaw command not found; relay may remain down."
    }
}

# Start required components once.
Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$ROOT\scripts\run-forever.ps1`"" -WindowStyle Normal | Out-Null
Start-Sleep -Seconds 1
Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$ROOT\scripts\start-worker.ps1`"" -WindowStyle Minimized | Out-Null
Start-Sleep -Seconds 1
Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$ROOT\scripts\start-cloud-monitor.ps1`"" -WindowStyle Minimized | Out-Null

# Write memory bootstrap if absent.
$memoryPath = Join-Path $ROOT "data\memory.json"
if (-not (Test-Path $memoryPath)) {
    '{"conversations":[]}' | Out-File -FilePath $memoryPath -Encoding utf8 -Force
}

Start-Sleep -Seconds 2
$nowLauncher = Get-CimInstance Win32_Process | Where-Object { $_.Name -like "python*" -and $_.CommandLine -match ([Regex]::Escape("$ROOT\launcher.py")) }
$nowBot = Get-CimInstance Win32_Process | Where-Object { $_.Name -like "python*" -and $_.CommandLine -match ([Regex]::Escape("$ROOT\bot.py")) }
$nowWorker = Get-CimInstance Win32_Process | Where-Object { $_.Name -like "python*" -and $_.CommandLine -match "scripts\\job_worker\.py|-m scripts.job_worker" -and $_.CommandLine -match $escapedRoot }
$nowProbe = Get-CimInstance Win32_Process | Where-Object { $_.Name -like "powershell*" -and $_.CommandLine -match "start-cloud-monitor\.ps1" -and $_.CommandLine -match $escapedRoot }

Write-Host "Konstance simple launcher started: launcher + worker + cloud monitor + model services."
