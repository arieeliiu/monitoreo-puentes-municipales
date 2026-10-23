$ErrorActionPreference='Stop'
$repo = Split-Path $PSScriptRoot -Parent
. (Join-Path $repo 'demo-procesos.ps1')
foreach ($name in @('publicar-demo.ps1','detener-demo.ps1','demo-procesos.ps1')) {
    $parseErrors=$null; $tokens=$null
    [void][Management.Automation.Language.Parser]::ParseFile((Join-Path $repo $name),[ref]$tokens,[ref]$parseErrors)
    if ($parseErrors.Count) { throw "Sintaxis incorrecta en $name" }
}
Write-Host 'OK: sintaxis de los tres scripts'
$testDirectory=Join-Path $DemoInstance ('prueba-procesos-'+[guid]::NewGuid())
[void][IO.Directory]::CreateDirectory($testDirectory)
$DemoStatePath=Join-Path $testDirectory 'estado.json'
try {
    $identity=Get-DemoIdentity $PID
    if (-not (Test-DemoProcess $identity)) { throw 'No reconoce la identidad actual.' }
    Save-DemoState ([pscustomobject]@{Root=$DemoRoot;Processes=@($identity);Url=$null})
    if (-not (Test-DemoProcess (Read-DemoState).Processes[0])) { throw 'La identidad no sobrevive la serialización JSON.' }
    $falseIdentity=[pscustomobject]@{Id=$PID;Created='otra-fecha';Command=$identity.Command;Role='ajeno'}
    if (Test-DemoProcess $falseIdentity) { throw 'Acepta un PID reutilizado.' }
    Write-Host 'OK: identidad por PID, fecha y comando'
    $state=[pscustomobject]@{Root=$DemoRoot;Processes=@($falseIdentity);Url=$null}
    Save-DemoState $state;Stop-DemoOwned (Read-DemoState)
    if (-not (Get-Process -Id $PID)) { throw 'Detuvo un proceso ajeno.' }
    $empty=[pscustomobject]@{Root=$DemoRoot;Processes=@();Url=$null}
    Save-DemoState $empty;Stop-DemoOwned (Read-DemoState)
    Write-Host 'OK: detención vacía/repetida y PID ajeno intacto'
    try { Stop-DemoOwned ([pscustomobject]@{Root='otra-carpeta';Processes=@()});throw 'Acepta estado de otra carpeta' }
    catch { if ($_.Exception.Message -notlike 'El estado pertenece*') { throw } }
    Write-Host 'OK: rechaza estado de otra carpeta'
} finally {
    # Solo los archivos de prueba nombrados y la carpeta vacía creados arriba.
    Remove-Item -LiteralPath $DemoStatePath -ErrorAction SilentlyContinue
    [IO.Directory]::Delete($testDirectory)
}
