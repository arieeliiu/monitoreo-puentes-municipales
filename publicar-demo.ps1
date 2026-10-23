. (Join-Path $PSScriptRoot 'demo-procesos.ps1')
$demoLock = Enter-DemoLock
$state = $null
try {
    $old = Read-DemoState
    if ($null -ne $old) {
        if ($old.Root -ne $DemoRoot) { throw 'El estado pertenece a otra carpeta. No se iniciaron ni detuvieron procesos.' }
        $active = @($old.Processes | Where-Object { Test-DemoProcess $_ })
        if ($active.Count -eq 4 -and $old.Url) {
            Wait-DemoHttp 'http://127.0.0.1:5000/login' ($old.Processes | Where-Object Role -eq 'demo-web')
            Write-Host "Aplicación ya disponible para compartir: $($old.Url)"
            return
        }
        Stop-DemoOwned $old
    }
    $python = Join-Path $DemoRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $python)) { throw 'Falta Python del proyecto. Instala Python y crea .venv según README.md.' }
    & $python -c 'import flask, waitress, PIL' 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'Faltan dependencias. Ejecuta .\.venv\Scripts\python.exe -m pip install -r requirements.txt' }
    $cloud = Get-Command cloudflared.exe -ErrorAction SilentlyContinue
    $cloudPath = if ($cloud) { $cloud.Source } else { $null }
    if (-not $cloudPath) {
        $npmBinary = Join-Path $env:APPDATA 'npm\node_modules\cloudflared\bin\cloudflared.exe'
        if (Test-Path -LiteralPath $npmBinary) { $cloudPath = $npmBinary }
    }
    if (-not $cloudPath) { throw 'Falta cloudflared. Instala: winget install --id Cloudflare.cloudflared --exact ; abre otra terminal y repite.' }
    & $cloudPath --version
    if ($LASTEXITCODE -ne 0) { throw 'cloudflared no funciona. Reinstálalo desde Cloudflare.' }
    foreach ($port in @(5000,5100)) {
        if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) { throw "El puerto $port está ocupado por otro proceso. Detén ese servidor antes de publicar; no se cerrará automáticamente." }
    }
    $env:COOKIE_SECURE='1'
    $env:PROJECT_STAGE='cutoff_2026_10_26'
    $env:PROVIDER_URL='http://127.0.0.1:5100/measurements'
    $database = Join-Path $DemoInstance 'puentes.sqlite'
    if (-not (Test-Path -LiteralPath $database)) {
        & $python -m flask --app app init-db
        if ($LASTEXITCODE -ne 0) { throw 'Falló la inicialización de la base.' }
        $accounts = & $python -m flask --app app seed-demo
        if ($LASTEXITCODE -ne 0) { throw 'Falló seed-demo; revisa la base antes de reintentar.' }
        [IO.File]::WriteAllLines((Join-Path $DemoInstance 'ACCESO_LOCAL.txt'), [string[]]$accounts, [Text.UTF8Encoding]::new($false))
    }
    & $python -c 'import sqlite3; c=sqlite3.connect("instance/puentes.sqlite"); assert c.execute("PRAGMA integrity_check").fetchone()[0]=="ok"; assert c.execute("SELECT count(*) FROM users").fetchone()[0]>0; c.close()'
    if ($LASTEXITCODE -ne 0) { throw 'La base existente no es válida o no tiene usuarios. No se ejecutó seed-demo sobre ella.' }
    $state = [pscustomobject]@{ Root=$DemoRoot; Processes=@(); Url=$null }
    Save-DemoState $state
    $web = Start-DemoOwned $state 'demo-web' $python @('-m','waitress','--listen=127.0.0.1:5000','--call','app:create_app')
    Wait-DemoHttp 'http://127.0.0.1:5000/login' $web
    $provider = Start-DemoOwned $state 'demo-provider' $python @('mock_provider.py','--port','5100')
    Wait-DemoHttp $env:PROVIDER_URL $provider
    $worker = Start-DemoOwned $state 'demo-worker' $python @('-m','flask','--app','app','poll-provider','--interval','60')
    $quickConfig = Join-Path $DemoInstance 'quick-tunnel.yml'
    [IO.File]::WriteAllText($quickConfig, '{}', [Text.UTF8Encoding]::new($false))
    $tunnel = Start-DemoOwned $state 'demo-tunnel' $cloudPath @('tunnel','--config',$quickConfig,'--no-autoupdate','--loglevel','info','--url','http://127.0.0.1:5000')
    for ($attempt=0; $attempt -lt 120; $attempt++) {
        foreach ($record in $state.Processes) { if (-not (Test-DemoProcess $record)) { throw "Terminó $($record.Role). Revisa su log privado en instance." } }
        $log = (Get-Content -LiteralPath (Join-Path $DemoInstance 'demo-tunnel.err.log') -Raw -ErrorAction SilentlyContinue)
        if ($log -match 'https://[a-z0-9-]+\.trycloudflare\.com') { $state.Url=$Matches[0]; break }
        Start-Sleep -Milliseconds 500
    }
    if (-not $state.Url) { throw 'Cloudflare no proporcionó URL. Revisa instance\demo-tunnel.err.log.' }
    Save-DemoState $state
    Write-Host "Aplicación disponible para compartir: $($state.Url)"
    Write-Host 'Mantén el computador encendido y conectado. Credenciales privadas: instance\ACCESO_LOCAL.txt'
    Write-Host 'Para detener únicamente esta publicación: .\detener-demo.ps1'
} catch {
    if ($state) { Stop-DemoOwned $state }
    throw
} finally { $demoLock.Dispose() }
