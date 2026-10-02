$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $root 'backend'
$frontendDir = Join-Path $root 'frontend'
$venvPython = Join-Path $root '.venv\Scripts\python.exe'

if (-not (Test-Path $venvPython)) {
    Write-Host 'Creating Python virtual environment...'
    py -m venv (Join-Path $root '.venv')
}

# Kill stale port holders before starting the app.
foreach ($port in 5173, 5174, 8000) {
    try {
        $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction Stop
        foreach ($connection in $connections) {
            if ($connection.OwningProcess) {
                Write-Host "Stopping stale process on port $port (PID $($connection.OwningProcess))"
                Stop-Process -Id $connection.OwningProcess -Force -ErrorAction SilentlyContinue
            }
        }
    }
    catch {
        # No active connection on this port.
    }
}

Write-Host 'Installing backend dependencies...'
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $backendDir 'requirements.txt')

Write-Host 'Running Django migrations...'
Push-Location $backendDir
& $venvPython manage.py migrate
Pop-Location

if (-not (Test-Path (Join-Path $frontendDir 'node_modules'))) {
    Write-Host 'Installing frontend dependencies...'
    Push-Location $frontendDir
    npm install
    Pop-Location
}

Write-Host 'Starting backend...'
$backendProcess = Start-Process -FilePath $venvPython -ArgumentList 'manage.py', 'runserver', '0.0.0.0:8000' -WorkingDirectory $backendDir -PassThru -NoNewWindow

Write-Host 'Starting frontend...'
$frontendProcess = Start-Process -FilePath 'npm.cmd' -ArgumentList 'run', 'dev', '--', '--host', '0.0.0.0', '--port', '5173', '--strictPort' -WorkingDirectory $frontendDir -PassThru -NoNewWindow

Write-Host ''
Write-Host 'App is running:'
Write-Host '  Backend:  http://localhost:8000'
Write-Host '  Frontend: http://localhost:5173'
Write-Host '  Admin:    http://localhost:8000/admin/'
Write-Host ''
Write-Host 'Backend PID: ' $backendProcess.Id
Write-Host 'Frontend PID: ' $frontendProcess.Id
