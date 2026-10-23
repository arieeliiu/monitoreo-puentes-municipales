# Verificación

Suite: `python -m unittest discover -v`. Resultado registrado durante el desarrollo: **18 pruebas aprobadas**. Se ejecuta contra SQLite temporal y cliente HTTP de Flask, incluyendo la recepción API y el contenido HTML de las pantallas. Esto no equivale a integración con dispositivos o aceptación de un especialista.

Ver los nombres y las verificaciones completas en `tests/test_app.py`. La suite verifica controles de permisos de servidor, inyección HTML escapada, CSRF, fotos inválidas sin persistencia, idempotencia de ID externo, asociaciones entre puentes, reglas ficticias, estados no disponibles y cierre explícito de alertas después de completar tareas.

Prueba de aceptación sugerida: seguir el recorrido del README con las tres cuentas. Revisar el panel sin datos antes de las capturas; crear una regla ficticia; capturar un dato que la supere; subir una foto en una inspección; vincular inspección, alerta y actividad; completar con mantención y cerrar como DOM con justificación. Verificar la auditoría. Repetir desde tablet.

Limitaciones pendientes: API/proveedor real, validación estructural de umbrales, contenido oficial detallado de CA, verificación en tablets físicas y despliegue municipal con HTTPS y política de respaldo. La interfaz es adaptable mediante CSS y todas las páginas se renderizan en la suite.

Revisión visual realizada: inicio de sesión DOM y panel con los dos puentes de prueba, aviso sin reglas y estados sin datos. Evidencia: panel-verificado.png. Verificación en navegador local, sin dispositivos físicos.
