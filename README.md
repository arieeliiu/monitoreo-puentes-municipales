# Monitoreo de puentes municipales

Aplicación Flask + SQLite con cinco módulos y tres roles: DOM, inspector municipal y mantención. Esta versión aplica el **Enunciado del Alcance EV2 actualizado del 22/10/2026**, que prevalece sobre especificaciones anteriores.

## Instalación nueva (PowerShell, Python 3.12+)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app app init-db
.\.venv\Scripts\python.exe -m flask --app app seed-demo
.\start.ps1
```

Abrir http://127.0.0.1:5000. `seed-demo` muestra contraseñas aleatorias para `dom`, `inspector`, `mantencion`; solo se admite en una base vacía. La instalación local existente conserva sus cuentas y claves en `instance/ACCESO_LOCAL.txt`, excluido de Git. Para datos reales, crear usuarios con `flask --app app create-user nombre --role DOM` (también Inspector y Mantención), sin ejecutar seed-demo.

## Actualizar una instalación existente

Detener web, worker IoT y proveedor simulado y respaldar **toda** la carpeta `instance/` (SQLite, fotos y clave de sesión). Después:

```powershell
.\.venv\Scripts\python.exe -m flask --app app migrate-db
.\.venv\Scripts\python.exe -m flask --app app configure-ev2-demo
```

`init-db` y `migrate-db` ejecutan las migraciones compatibles. `schema.sql` es el bootstrap original para permitir probar instalaciones anteriores; la definición vigente es su resultado más `migrations.py` y `ev2_migration.py`. No basta ejecutar solo el SQL base.

- No se borran filas, IDs, cuentas, fotografías ni relaciones. Se amplía el CHECK de inspecciones dentro de una transacción, con comprobación de claves foráneas y rollback ante errores.
- Las mediciones originales permanecen en **mm/s** y con sus valores exactos: son velocidad de vibración histórica, **incompatible con aceleración EV2**. No se convierte ni se cambia su etiqueta. El sensor se configura para **nuevas** capturas en m/s², guardando su unidad de configuración anterior en `previous_unit`.
- Las reglas y alertas anteriores se conservan con escala histórica; no evalúan las nuevas lecturas ni se reclasifican retrospectivamente. Las alertas antiguas muestran «sin clasificación EV2».
- Buena, Regular, Mala y Crítica históricas se conservan literalmente con `standard=historica`. **No existe equivalencia automática** con Baja/Media/Alta/Crítica. Incluso una antigua Crítica sigue identificada como histórica. El servidor solo admite categorías EV2 en inspecciones nuevas.
- `configure-ev2-demo` agrega los componentes faltantes Tablero/Viga/Estribo en puentes marcados como demostración. Normaliza el antiguo nombre «Tablero · prueba» a «Tablero», conservando ID y relaciones; no borra otros componentes. No agrega sensores físicos adicionales: los cuatro existentes siguen configurables.
- En sensores de inclinación de demostración sin referencia se configura el valor simulado del JSON; no sobrescribe referencias ya definidas ni modifica sensores de puentes reales. Agrega únicamente configuraciones EV2 nunca definidas; no reactiva niveles que DOM desactivó ni sobrescribe sus cambios.

## Ubicaciones del piloto y formularios de sensores

DOM crea y edita sensores desde la ficha del puente. Las opciones muestran los nombres EV2 y envían `vibracion` / `inclinacion`; la edición conserva la selección. El selector de componentes de esa ficha queda habilitado sin exigir un segundo selector de puente.

Para completar únicamente ubicaciones pendientes en una instalación existente:

```powershell
.\.venv\Scripts\python.exe -m flask --app app configure-demo-locations
```

La operación es idempotente y solo alcanza los cuatro códigos originales `DEM-01/02-VIBRACION/INCLINACION`, en sus puentes marcados como simulados, cuando la ubicación está vacía o dice «Pendiente de precisar». Usa posiciones específicas según el componente actual Tablero, Viga o Estribo (ver `demo_locations.py`). Conserva ubicaciones manuales, códigos personalizados, componentes desconocidos, asociaciones, referencias, datos históricos y umbrales. No agrega sensores ni los redistribuye: los cuatro sensores originales siguen asociados a sus tableros. Las posiciones son parte de la configuración simulada del piloto. `seed-demo` y `configure-ev2-demo` también completan estas ubicaciones.

## Criterios de medición y niveles EV2

| Nivel | Aceleración vertical pico (m/s²) | Cambio absoluto de inclinación (°) |
|---|---:|---:|
| Atención | 0,5 | 0,115 |
| Alerta | 1,0 | 0,229 |
| Crítico | 2,5 | 0,458 |

Son **parámetros asumidos del piloto académico**. Se cargan desde `config/ev2_pilot.json`, no desde constantes de evaluación. DOM puede configurar o desactivar niveles desde Reglas de alerta; guardar un nivel existente desactiva la versión anterior y crea otra, conservando la regla original de las alertas previas. Se valida que los límites numéricos sean finitos, no negativos y crecientes entre niveles. Las reglas existentes no se reevaluan retroactivamente.

Comparación **inclusiva `>=`**. Se genera una sola alerta por lectura, con el **nivel más alto** alcanzado. Una aceleración de 1,0 m/s² es Alerta; 2,5 es Crítico. La ausencia de regla aplicable se informa por registro.

Inclinación: **variación = abs(lectura − referencia del sensor)**. DOM administra la referencia en la ficha del sensor. Cada medición guarda lectura, referencia utilizada y variación; cambios posteriores no alteran las mediciones anteriores. El cálculo decimal evita perder un límite exacto por restas de coma flotante. Ejemplo con referencia 10°: lectura 9,771° → cambio 0,229° → Alerta. Sin referencia, se guarda la lectura y se informa que no puede evaluarse; no se genera alerta numérica por ella. La referencia inicial de demostración es 0°, configurable y simulada.

Inspecciones nuevas: **Baja, Media, Alta, Crítica**. Las condiciones generan alertas por coincidencia exacta según reglas configuradas por DOM. La configuración inicial asume Media→Atención, Alta→Alerta y Crítica→Crítico; Baja no tiene regla inicial. Este mapeo solo corresponde a categorías EV2 nuevas, es configurable y no se aplica a categorías históricas. Las fotos siguen siendo opcionales.

Una alerta es una situación para revisión, **no un diagnóstico estructural**. No se solicita contratar ni contactar especialistas para esta demostración; la revisión externa es previa a una eventual puesta en marcha real.

## Proveedor IoT y captura periódica

Flujo: Sensor → plataforma del proveedor → API del proveedor → cliente municipal. El proveedor de este repositorio es **simulado**, independiente del proceso web. No se declara integración real con hardware.

```powershell
# Terminal del proveedor
.\.venv\Scripts\python.exe mock_provider.py --port 5100
# Terminal del worker
$env:PROVIDER_URL='http://127.0.0.1:5100/measurements'
.\start-iot.ps1 -Interval 60
# Alternativa: prioridad del argumento sobre IOT_POLL_INTERVAL; predeterminado 60 s
.\.venv\Scripts\python.exe -m flask --app app poll-provider --interval 15
```

Iniciar solo un worker. Primera consulta inmediata y espera configurable entre ciclos (1–86400 s). El worker es independiente de la web, con un bloqueo de SO por base, contexto/conexión por ciclo y recuperación ante errores. `PROVIDER_TOKEN` es opcional para un futuro proveedor. El cliente tiene timeout de 3 segundos, hasta 3 intentos y esperas exponenciales 0,2/0,4 s para desconexiones, 429 y 5xx. No reintenta formatos inválidos/otros 4xx. Un fallo no detiene los ciclos siguientes ni el servidor web. Para servicio permanente, supervisar ambos procesos externamente; no se instala un servicio del sistema.

Consulta manual conservada: DOM → Lecturas → Consultar proveedor; o `flask --app app pull-provider`. Recepción serializada con `BEGIN IMMEDIATE`, ID externo UNIQUE, validación por elemento y rollback con savepoints; registros inválidos no impiden guardar otros válidos.

```json
{"simulated":true,"measurements":[
  {"external_id":"ev2-a","bridge_code":"DEM-01","kind":"vibracion","sensor_code":"DEM-01-VIBRACION","value":1.0,"unit":"m/s²","measured_at":"2026-10-22T10:00:00-03:00","status":"valido","simulated":true},
  {"external_id":"ev2-b","bridge_code":"DEM-02","kind":"inclinacion","sensor_code":"DEM-02-INCLINACION","value":-0.229,"unit":"°","measured_at":"2026-10-22T10:00:00-03:00","status":"valido","simulated":true}
]}
```

El lote del proveedor permanece estable hasta reiniciarlo; consultar otra vez no inventa datos nuevos ni duplica registros. Incluye ambas variables para ambos puentes. Se valida bridge_code y kind contra la relación sensor/componente/puente, unidad, fecha con zona no futura, valor finito y estado. `invalido`/`no_disponible` se guardan diferenciados y no generan alertas. Nuevas capturas de vibración en mm/s se rechazan. Los errores conservan identidad y motivo en auditoría; si SQLite impide auditar, se notifican en logs del worker.

La API POST municipal alternativa se conserva con clave `IOT_API_KEY`, cabecera `Authorization: Bearer ...`. Si esa variable no está configurada responde 503; clave incorrecta 401; JSON inválido/duplicado 400; válida 201. Campos de identidad opcionales por compatibilidad, pero se validan si se suministran. Su unidad vigente también es m/s². El formulario local conserva registro manual, y `simulate_iot.py` conserva el envío manual a esta API.

## Operación por rol

- DOM administra infraestructura, referencias, reglas, programación y mantenimiento. Cierra alertas explícitamente con nota.
- Inspector consulta registros, documenta inspecciones y fotos y registra el resultado de las programaciones que tiene asignadas. Puede relacionar inspecciones con alertas sin cerrarlas.
- Mantención consulta y actualiza exclusivamente sus actividades asignadas.

El panel distingue sensores y condiciones visuales, muestra lectura/referencia/variación, severidades, datos faltantes, alertas activas, pendientes de mantenimiento, próximas inspecciones y últimas observaciones con acceso a fotos. Las tareas no cierran alertas automáticamente. Los históricos no se presentan como datos EV2 evaluados. El filtro de mantenimiento por puente respeta permisos.

Interfaz: solo una indicación discreta «Entorno de demostración» por pantalla; sin HU/EDT, etiquetas repetidas de prueba ni fechas académicas. La marca de simulación sigue persistida. Los errores, faltas de datos y referencias ausentes se mantienen visibles.

## Pruebas y documentación

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
# Regresión JavaScript: Node.js 18+ (solo para pruebas; no requerido por la aplicación)
node --test tests/frontend.test.cjs
.\.venv\Scripts\python.exe tools/build_mockups.py
```

Los mockups se generan con plantillas reales y base temporal; no escriben en el piloto. Ver [arquitectura](docs/ARQUITECTURA.md), [matriz individual](docs/CUMPLIMIENTO.md), [verificación](docs/VERIFICACION.md) y [diseño](docs/DISENO.md).

SQLite, fotos, credenciales, backups y claves están en `instance/`, excluido de Git. Mantener respaldo conjunto y HTTPS para uso institucional. Hash de contraseñas, roles de servidor, CSRF, CSP, imágenes privadas verificadas/recodificadas y auditoría se conservan. Fotografías JPEG/PNG: hasta 5, 20 megapíxeles y petición máxima 20 MB. Para red institucional usar Waitress detrás de TLS con `COOKIE_SECURE=1` y secretos por entorno.

Línea de base conservada en documentación: término EDT 1.4.5/1.4.6 **24/11/2026**; presentación **26/11/2026**. HU-09 (aceptación municipal, piloto real, capacitación y cierre) sigue pendiente; proveedor real y validación externa no verificados.
