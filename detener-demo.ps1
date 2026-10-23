. (Join-Path $PSScriptRoot 'demo-procesos.ps1')
$demoLock = Enter-DemoLock
try {
    $state = Read-DemoState
    if ($null -eq $state) { Write-Host 'No hay publicación registrada; no se detuvo ningún proceso.'; return }
    Stop-DemoOwned $state
    Write-Host 'Publicación detenida. Base, cuentas, fotografías y registros conservados.'
} finally { $demoLock.Dispose() }
