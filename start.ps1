$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path '.venv\Scripts\python.exe')) { throw 'Primero instala el entorno siguiendo README.md.' }
& '.\.venv\Scripts\python.exe' -m flask --app app run --host 127.0.0.1 --port 5000
