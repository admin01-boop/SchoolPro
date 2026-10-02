#Requires -Version 5.1
# Dumps the PostgreSQL database named by DATABASE_URL in backend/.env to backups/<timestamp>.dump.
# Restore with: pg_restore --clean --if-exists -d <db> backups\<file>.dump
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $root 'backend\.env'
$line = Get-Content $envFile | Where-Object { $_ -match '^\s*DATABASE_URL\s*=\s*postgres' } | Select-Object -First 1
if (-not $line) { throw 'DATABASE_URL in backend/.env is not a postgres:// URL; nothing to back up.' }

$url = [Uri](($line -split '=', 2)[1].Trim())
$user, $password = $url.UserInfo -split ':', 2
$database = $url.AbsolutePath.TrimStart('/')

$backupDir = Join-Path $root 'backups'
New-Item -ItemType Directory -Force $backupDir | Out-Null
$target = Join-Path $backupDir ("{0}_{1}.dump" -f $database, (Get-Date -Format 'yyyyMMdd-HHmmss'))

$env:PGPASSWORD = [Uri]::UnescapeDataString($password)
try {
    pg_dump --format=custom --host $url.Host --port $(if ($url.Port -gt 0) { $url.Port } else { 5432 }) --username $user --file $target $database
    if ($LASTEXITCODE -ne 0) { throw "pg_dump failed with exit code $LASTEXITCODE" }
}
finally {
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
}
Write-Host "Backup written to $target"
