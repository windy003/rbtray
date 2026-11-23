$ErrorActionPreference = 'Stop'

$procs = Get-WmiObject Win32_Process | Where-Object {$_.CommandLine -like "*rbtray*"} |   Select-Object  ParentProcessId ,ProcessId, CommandLine

if (-not $procs) {
    Write-Host "No matching process found (jdbendi.com\flask\app.py)." -ForegroundColor Yellow
} else {
    foreach ($p in $procs) {
        Write-Host "Killing PID $($p.ProcessId): $($p.CommandLine)" -ForegroundColor Cyan
        try {
            Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
            Write-Host "  Killed PID $($p.ProcessId)" -ForegroundColor Green
        } catch {
            Write-Host "  Failed to kill PID $($p.ProcessId): $_" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Start-Sleep -Seconds 3
