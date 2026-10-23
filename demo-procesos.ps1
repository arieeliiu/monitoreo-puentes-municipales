$ErrorActionPreference = 'Stop'
$DemoRoot = $PSScriptRoot
$DemoInstance = Join-Path $DemoRoot 'instance'
$DemoStatePath = Join-Path $DemoInstance 'publicacion-demo.json'

function Enter-DemoLock {
    if ((Get-Location).Path.TrimEnd('\') -ne $DemoRoot.TrimEnd('\')) {
        throw "Ejecuta el script desde la carpeta del proyecto: $DemoRoot"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $DemoRoot 'app.py'))) { throw 'No se encontró app.py.' }
    [void][IO.Directory]::CreateDirectory($DemoInstance)
    try { return [IO.File]::Open((Join-Path $DemoInstance 'publicacion-demo.lock'), 'OpenOrCreate', 'ReadWrite', 'None') }
    catch { throw 'Ya hay un inicio o una detención en curso. Espera a que termine.' }
}

function Read-DemoState {
    if (Test-Path -LiteralPath $DemoStatePath) { return Get-Content -LiteralPath $DemoStatePath -Raw | ConvertFrom-Json }
    return $null
}

function Save-DemoState($State) {
    [IO.File]::WriteAllText($DemoStatePath, ($State | ConvertTo-Json -Depth 8), [Text.UTF8Encoding]::new($false))
}

function Get-DemoIdentity([int]$ProcessId) {
    $item = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
    if ($null -eq $item) { return $null }
    return [pscustomobject]@{ Id=$ProcessId; Created=$item.CreationDate.ToUniversalTime().Ticks.ToString(); Command=$item.CommandLine }
}

function Test-DemoProcess($Record) {
    $current = Get-DemoIdentity $Record.Id
    return ($null -ne $current -and $current.Created -eq $Record.Created -and $current.Command -eq $Record.Command)
}

function Stop-DemoOwned($State) {
    if ($null -eq $State) { return }
    if ($State.Root -ne $DemoRoot) { throw 'El estado pertenece a otra carpeta; no se detendrá ningún proceso.' }
    $records = @($State.Processes)
    [array]::Reverse($records)
    foreach ($record in $records) {
        if (Test-DemoProcess $record) {
            & taskkill.exe /PID $record.Id /T /F 2>&1 | Out-Null
            if (Test-DemoProcess $record) { throw "No fue posible detener el proceso $($record.Role)." }
        }
    }
    Remove-Item -LiteralPath $DemoStatePath -ErrorAction SilentlyContinue
}

function Start-DemoOwned($State, [string]$Role, [string]$Executable, [string[]]$Arguments) {
    # Start-Process on Windows joins ArgumentList: quote individual arguments.
    $quoted = @($Arguments | ForEach-Object { '"' + $_.Replace('"','\"') + '"' })
    $process = Start-Process -FilePath $Executable -ArgumentList $quoted -WorkingDirectory $DemoRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $DemoInstance "$Role.out.log") -RedirectStandardError (Join-Path $DemoInstance "$Role.err.log")
    $identity = Get-DemoIdentity $process.Id
    if ($null -eq $identity) { throw "No inició $Role. Revisa instance\$Role.err.log." }
    $identity | Add-Member -NotePropertyName Role -NotePropertyValue $Role
    $State.Processes = @($State.Processes) + $identity
    Save-DemoState $State
    return $identity
}

function Wait-DemoHttp([string]$Url, $Record) {
    for ($attempt=0; $attempt -lt 40; $attempt++) {
        if (-not (Test-DemoProcess $Record)) { throw "Terminó $($Record.Role); revisa su log privado en instance." }
        try { if ((Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200) { return } } catch {}
        Start-Sleep -Milliseconds 250
    }
    throw "No respondió $Url."
}

