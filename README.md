# Monitoreo de puentes municipales

Aplicación funcional Flask + SQLite para un piloto de dos puentes de la Región del Biobío. Presentación académica: **26/11/2026**. Término planificado de EDT 1.4.5 y 1.4.6: **24/11/2026**.

## Instalar en Windows

Requiere Python 3.12 o superior y una terminal PowerShell dentro de esta carpeta.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app app init-db
.\.venv\Scripts\python.exe -m flask --app app seed-demo
.\.venv\Scripts\python.exe -m flask --app app run --host 127.0.0.1 --port 5000
```

Abrir http://127.0.0.1:5000. `seed-demo` imprime una contraseña aleatoria para cada usuario: `dom`, `inspector`, `mantencion`. Guardarlas fuera del repositorio. Solo funciona sobre una base vacía. No crea reglas oficiales ni mediciones ficticias sin intervención del usuario.

La instalación local preparada por Codex incluye `.venv` y una base de demostración en `instance/`. Las credenciales locales están en `instance/ACCESO_LOCAL.txt`, excluido de Git. Para iniciarla basta ejecutar `start.ps1` o el último comando anterior.

Para comenzar con información real, usar una base nueva, ejecutar `init-db` y crear usuarios individualmente:

```powershell
.\.venv\Scripts\python.exe -m flask --app app create-user administrador --role DOM
.\.venv\Scripts\python.exe -m flask --app app create-user inspector1 --role Inspector
.\.venv\Scripts\python.exe -m flask --app app create-user tecnico1 --role Mantención
```

Las contraseñas se piden sin eco y requieren 12 caracteres como mínimo. No hay registro público de cuentas.

## Recorrido de demostración

1. DOM: revisar los dos puentes ficticios; editar infraestructura y agregar componentes/sensores.
2. DOM: crear una regla marcada como **ficticia para pruebas**, eligiendo un valor arbitrario solo para demostrar la comparación. No constituye un umbral estructural.
3. DOM: en Mediciones, abrir el entorno local y enviar un valor de prueba superior al umbral, con unidad correspondiente y fecha ISO con zona horaria (por ejemplo `2026-10-22T10:00:00-03:00`). Se guardan medición y alerta en una transacción.
4. Inspector: registrar una inspección del mismo puente, opcionalmente con hasta cinco fotografías JPEG/PNG, y abrir su ficha.
5. DOM: abrir la alerta, relacionar la inspección en una nota y planificar una actividad con esa alerta y personal de mantención.
6. Mantención: consultar la actividad asignada y actualizar a En ejecución / Completada.
7. DOM: revisar el seguimiento y resolver explícitamente la alerta con una justificación. Crear o completar tareas no resuelve alertas.

## Roles

| Operación | DOM | Inspector | Mantención |
|---|---|---|---|
| Consultar infraestructura, mediciones, inspecciones, fotos y alertas | Sí | Sí | Sí |
| Registrar/editar puentes, componentes y sensores | Sí | No | No |
| Registrar mediciones locales ficticias / configurar reglas | Sí | No | No |
| Registrar inspecciones y fotos / notas de alerta | Sí | Sí | No |
| Cambiar estado de alerta / planificar y reasignar mantenimiento | Sí | No | No |
| Consultar mantenimiento | Todo | Todo | Solo asignado |
| Actualizar ejecución de actividad | Todas | No | Solo asignada |
| Consultar auditoría | Sí | No | No |

## Integración IoT y simulador

Arquitectura principal: Sensor → plataforma IoT del proveedor → API del proveedor → cliente municipal (consulta manual o CLI). Existe un proveedor ficticio independiente y un cliente pull implementados; **no hay proveedor ni conexión real verificada**. El proveedor futuro deberá exponer su API y acordar la adaptación al contrato descrito; la API receptora se conserva como alternativa. El sistema no instala sensores ni predice fallas.

```powershell
$env:IOT_API_KEY = 'reemplazar-por-un-secreto-largo-y-aleatorio'
.\.venv\Scripts\python.exe -m flask --app app run
# En otra terminal, configurar la misma variable:
.\.venv\Scripts\python.exe simulate_iot.py --sensor DEM-01-VIBRACION --value 7 --unit mm/s
```

El número del ejemplo es exclusivamente ficticio. El simulador marca siempre `simulated: true`. Sin API key el receptor devuelve 503; clave incorrecta: 401; contenido inválido o ID repetido: 400; recepción válida: 201.

`POST /api/v1/measurements`, cabecera `Authorization: Bearer <IOT_API_KEY>`:

```json
{"external_id":"proveedor-uuid-unico","sensor_code":"DEM-01-VIBRACION","value":7,"unit":"mm/s","measured_at":"2026-10-22T10:00:00-03:00","status":"valido","simulated":true}
```

Unidades canónicas: vibración `mm/s`, inclinación `°`. No se convierten unidades silenciosamente. `status`: `valido`, `invalido`, `no_disponible`; los dos últimos no generan alertas, pueden guardar valor nulo. Payload malformado se rechaza. Un sensor válido con vibración negativa se rechaza; inclinación admite valores con signo. Umbral numérico configurable: `valor > umbral`, `valor < umbral` o `abs(valor) > umbral` (las dos últimas para inclinación); visual: coincidencia exacta con la condición seleccionada. Reglas nuevas no reevalúan registros históricos. Desactivar una regla conserva las alertas existentes. Toda alerta hereda marca de prueba si la regla o el registro es ficticio.

## Datos, seguridad y operación

- SQLite y fotografías se guardan en `instance/`. Reiniciar no borra registros. `init-db` es idempotente. Hacer respaldo conjunto de la base y las fotos con la aplicación detenida.
- Las fechas se normalizan a UTC; los formularios requieren zona horaria y rechazan fechas futuras. Se muestran fecha/hora de la última recepción y estados faltantes explícitos; no existe diagnóstico automático de seguridad estructural ni SLA de frescura acordado.
- Contraseñas con hash scrypt de Werkzeug, control de rol en servidor, CSRF, consultas parametrizadas, CSP y acceso autenticado a fotos. Las imágenes se verifican y recodifican a JPEG; no se conserva EXIF. Máximo 5 fotos, 20 megapíxeles por foto y 20 MB por petición.
- Cambiar tipo o componente de un sensor con mediciones se bloquea para preservar la trazabilidad. Cambios relevantes se registran con autor y fecha en auditoría.
- Historial de mediciones: máximo 500 resultados por consulta; filtrar fechas y sensor. Auditoría: últimas 500 operaciones en pantalla; la base conserva todas.
- Para red institucional, usar HTTPS y servidor WSGI: `waitress-serve --listen=127.0.0.1:5000 --call app:create_app`, detrás de proxy TLS. Configurar `COOKIE_SECURE=1`, `SECRET_KEY` e `IOT_API_KEY` mediante el entorno. El servidor Flask de `start.ps1` se destina a demostración local.
- Fuera del alcance simulado: nombres y ubicaciones reales, aceptación formal municipal, umbrales para uso real, proveedor IoT real y credenciales, política de frescura/retención/respaldo y aceptación municipal. No se solicitan informes, firmas ni contactos reales para las reglas académicas.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

La suite usa bases temporales, sin modificar los datos del piloto. Cubre infraestructura, permisos, fotos, mediciones, alertas numéricas/visuales, API, panel, trazabilidad, mantenimiento, persistencia, CSRF y escape HTML. Ver [cumplimiento](docs/CUMPLIMIENTO.md), [flujos y mockups](docs/DISENO.md), [arquitectura](docs/ARQUITECTURA.md) y [verificación](docs/VERIFICACION.md).

## Repositorio

Nombre solicitado: `monitoreo-puentes-municipales`, visibilidad pública. Publicar únicamente código y documentación. `.venv/`, `instance/`, fotos, credenciales y claves están excluidos de Git. Con GitHub CLI autenticado:

```powershell
gh repo create monitoreo-puentes-municipales --public --source . --remote origin --push
```


## Correcciones del piloto académico

Fechas de línea de base: **término planificado de EDT 1.4.5 y 1.4.6: 24/11/2026**. **Presentación académica: 26/11/2026**. Son hitos diferentes.

### Actualizar sin perder datos

Detener el servidor y respaldar `instance/puentes.sqlite` y `instance/photos/`. Luego:

```powershell
.\.venv\Scripts\python.exe -m flask --app app migrate-db
```

La migración es aditiva e idempotente: conserva IDs, usuarios, hashes, mediciones, reglas, inspecciones, fotos, tareas y auditoría. Agrega `sensors.location`, `rules.comparison`, `measurements.evaluation` e `inspection_plans`. Sensores históricos muestran «Pendiente de precisar» hasta editar su ubicación; no se inventan posiciones. La variable medida sigue identificada por `kind` (Vibración/Inclinación) y su unidad. Reglas históricas mantienen comparación `gt`. Registros antiguos indican que su evaluación no fue registrada históricamente.

### Proveedor IoT ficticio independiente y cliente municipal

En una terminal ejecutar:

```powershell
.\.venv\Scripts\python.exe mock_provider.py --port 5100
```

En otra, iniciar la aplicación. DOM → Mediciones → **Consultar proveedor simulado**, o ejecutar:

```powershell
$env:PROVIDER_URL='http://127.0.0.1:5100/measurements'
.\.venv\Scripts\python.exe -m flask --app app pull-provider
```

La obtención es manual, sin scheduler automático. Puede ejecutarse el comando desde un programador externo si se necesita periodicidad. `PROVIDER_TOKEN` es opcional para un futuro proveedor. La respuesta es `{"simulated":true,"measurements":[...]}` con los registros del contrato descrito arriba. El proveedor ficticio entrega cuatro mediciones (dos variables por cada puente DEM-01 y DEM-02), valores arbitrarios **7 mm/s y −3°**, no referencias seguras. El lote mantiene IDs durante su ejecución; consultar de nuevo cuenta duplicados sin volver a insertarlos. Reiniciar proveedor crea otro lote. Timeout 3 segundos por intento, máximo 3 intentos con espera exponencial 0,2 / 0,4 segundos ante desconexiones, HTTP 429 y 5xx. Otros 4xx o JSON inválido se informan sin reintento. Cada registro inválido se informa y no impide guardar otros válidos. Cada recepción válida comparte la lógica de validación, evaluación y auditoría; siempre se conserva `simulated=true`. La API receptora anterior se mantiene por compatibilidad, pero ya no representa el flujo principal del piloto.

### Reglas e inclinaciones negativas

Para el piloto ficticio elegir **Magnitud absoluta > umbral**, con un umbral académico no negativo elegido por DOM (por ejemplo **2° exclusivamente para demostración**): +3° y −3° alertan; +2° y −2° no alertan. También se admiten reglas direccionales `gt` y `lt` (por ejemplo, valor < −2°). Vibración conserva `gt`; condición visual conserva coincidencia exacta. Las reglas del formulario son supuestos de una contraparte ficticia y no requieren validación real. La ausencia de regla aplicable queda visible por medición y en la respuesta API, incluso cuando existen reglas de otra variable o puente.

### Inspecciones preventivas y panel

DOM → Inspecciones programadas: puente, componente, inspector, fecha y descripción. Estados Programada, Cancelada, Realizada. DOM puede cancelar mientras esté programada. El inspector asignado selecciona la programación al registrar una inspección del mismo puente y componente; se vincula el resultado y sus fotos opcionales y se cambia a Realizada en la misma transacción. No se permite reutilizar la programación ni registrar su resultado como otro inspector o DOM. Se mantienen inspecciones no programadas.

El panel separa sensores de condiciones visuales y muestra actividades no completadas (solo asignadas para Mantención), próximas inspecciones programadas, última inspección visual de cada puente y enlaces a fotografías/observaciones. Mantenimiento permite filtro por puente conservando la restricción del personal asignado. La ficha de alerta informa por separado falta de inspección vinculada (origen visual o nota con inspección) y falta de tarea relacionada. Tener inspecciones en el mismo puente no las vincula implícitamente. Las tareas nunca cierran la alerta automáticamente.
