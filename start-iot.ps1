param([ValidateRange(1,86400)][int]$Interval = 60)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path '.venv\Scripts\python.exe')) { throw 'Instala el entorno siguiendo README.md.' }
& '.\.venv\Scripts\python.exe' -m flask --app app poll-provider --interval $Interval
