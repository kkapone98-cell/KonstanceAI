Write-Host "Stopping python processes..."
Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Write-Host "Stopped."
