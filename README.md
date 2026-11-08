# Monitoreo de puentes municipales

Aplicación municipal con Flask/Jinja para registrar infraestructura, consultar mediciones, documentar inspecciones visuales y gestionar alertas. Usa SQLite en instalaciones locales o PostgreSQL y Storage privado de Supabase en la instalación Vercel.

EV3 está integrada en `main`. Mediciones incluye paginación de 20 registros: [aplicación](https://monitoreo-puentes-municipales.vercel.app). El proveedor del repositorio es **simulado**; no se declara integración con sensores físicos ni aceptación municipal del piloto.

## Funcionalidades y etapas

- **Infraestructura:** puentes, componentes y sensores, con ubicación y referencia de inclinación.
- **Monitoreo:** Mediciones (`/measurements`) y Alertas (`/alerts`) agrupadas en la navegación, sin cambiar sus rutas ni permisos. Ambas listas y el Historial de operaciones muestran **20 registros por página**. Los filtros se conservan al navegar; no hay carga infinita de filas.
- **Mediciones:** recepción manual por DOM, consulta del proveedor y API autenticada; valores, estado, origen, lectura/referencia/variación, detalle y enlaces a alertas asociadas.
- **Alertas:** filtros por puente, severidad, estado y fechas; origen en medición o inspección, notas de seguimiento y cierre explícito por DOM.
- **Notificaciones web:** campana para DOM, Inspector y Mantención con contador de alertas abiertas. Avisa solo altas posteriores a la línea base de la sesión; no notifica históricos al ingresar ni repite los IDs consumidos en esa pestaña. Consulta normal cada 30 s; lotes de hasta 20 con continuación cada 1 s y descanso de 5 s tras cuatro lotes pendientes. Sin solicitudes simultáneas; timeout de 8 s y pausa con pestaña oculta. No son notificaciones push con el sitio cerrado ni un estado persistente de “leídas”.
- **Reglas:** DOM configura, versiona y desactiva niveles; reglas vigentes e historial se muestran separados. La regla y configuración originales de cada alerta se conservan.
- **Inspecciones visuales:** hallazgos por componente y fotografías privadas opcionales.
- **Historial de operaciones:** consulta reservada a DOM. Se conservan literalmente los detalles históricos; los textos futuros identifican la procedencia simulada cuando corresponde.

`PROJECT_STAGE` controla funciones tanto en la web como en el worker:

| Etapa | Inicio | Reglas, alertas y campana | Mantenimiento e inspecciones programadas |
|---|---|---|---|
| `cutoff_2026_10_26` (predeterminada en código) | Básico | Deshabilitados; recepción con evaluación pendiente | Deshabilitados |
| `cutoff_2026_11_09` (EV3) | Básico | Habilitados con permisos por rol | Deshabilitados |
| `full` | Panel avanzado | Habilitados | Disponibles con sus permisos originales |

EV3 **no habilita panel avanzado, mantenimiento ni inspecciones programadas**. Sus rutas permanecen bloqueadas y las inspecciones rechazan un `plan_id` en estos cortes. Cambiar de etapa no migra ni reevalúa registros. Web y worker deben usar la misma etapa y reiniciarse al alternar.

## Permisos

| Operación en EV3 | DOM | Inspector | Mantención |
|---|---|---|---|
| Consultar infraestructura, mediciones, alertas e inspecciones | Sí | Sí | Sí |
| Consultar campana y contador de abiertas | Sí | Sí | Sí |
| Administrar infraestructura, sensores y referencias | Sí | No | No |
| Registrar medición manual o consultar proveedor desde la web | Sí | No | No |
| Configurar, versionar y desactivar reglas | Sí | No | No |
| Registrar inspección y fotografías | Sí | Sí | No |
| Agregar seguimiento y relacionar inspección con alerta | Sí | Sí | No |
| Cambiar estado/cerrar alerta con nota | Sí | No | No |
| Consultar Historial de operaciones | Sí | No | No |

Solo en `full`, DOM planifica mantenimiento y programaciones; Inspector atiende programaciones que tiene asignadas; Mantención actualiza exclusivamente sus actividades asignadas. Completar una actividad no cierra automáticamente una alerta. Estas capacidades posteriores no están disponibles en EV3.

## Fechas y horas

La interfaz presenta instantes en **`America/Santiago`**, con reglas de verano e invierno de `zoneinfo`/`tzdata`, mediante un único filtro Jinja. Formato: `DD/MM/AAAA HH:MM:SS (UTC-03:00)` o `(UTC-04:00)`, según la fecha. Se aplica a mediciones y recepción, alertas y notas, reglas y versiones, inspecciones, auditoría y fechas visibles del modo completo.

- La base conserva sus valores originales en **UTC**, sin migración ni reescritura. La API y el proveedor conservan su contrato ISO con zona; el ingreso ya normaliza los instantes a UTC. La conversión de presentación no alimenta el almacenamiento.
- Los filtros Desde/Hasta de Mediciones y Alertas representan **días de Chile**. Se convierten antes de consultar a un intervalo UTC: inicio inclusivo del primer día y comienzo exclusivo del día siguiente al último. Esto incluye correctamente medianoches, segundos finales y días de 23/25 horas. Ordenamiento y paginación siguen ejecutándose en SQL sobre los registros originales.
- Un timestamp histórico sin zona no se presume UTC ni chileno: se conserva visible con “zona horaria no registrada”. Las consultas por fechas incluyen los instantes con zona UTC explícita del contrato persistido (`+00:00` o `Z`); los históricos sin zona siguen consultables sin filtro de fechas. No se inventa su ubicación temporal ni se corrigen sus datos.
- Fechas planificadas sin hora son días calendario: se presentan `DD/MM/AAAA` sin desplazamiento. Los campos HTML `date` mantienen `AAAA-MM-DD` y los formularios manuales continúan usando fecha/hora de Chile. Una hora inexistente o ambigua por cambio de horario se rechaza con explicación, como antes.
- Textos libres de notas, descripciones y detalles históricos de auditoría se conservan literalmente, aunque incluyan fechas escritas por su autor.

## Instalación local en Windows

Python 3.12+ y PowerShell. Node.js 18+ se utiliza solo para pruebas JavaScript.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app app init-db
# Solo para una base local nueva y vacía:
.\.venv\Scripts\python.exe -m flask --app app seed-demo
$env:PROJECT_STAGE='cutoff_2026_11_09'
.\start.ps1
```

Abrir http://127.0.0.1:5000. `seed-demo` muestra contraseñas aleatorias para `dom`, `inspector` y `mantencion`; no se ejecuta sobre una base existente. Para una instalación sin datos simulados, omitirlo y crear usuarios con `flask --app app create-user nombre --role DOM` (también admite `Inspector` y `Mantención`). Las cuentas locales existentes no se regeneran; su información privada está en `instance/`, excluido de Git.

### Actualización y conservación de datos

Detener escritores y respaldar conjuntamente SQLite, fotos y clave de sesión en `instance/` antes de una migración local. `flask --app app migrate-db` aplica las migraciones compatibles. `schema.sql` es el bootstrap original: la definición vigente incluye `migrations.py` y `ev2_migration.py`.

Esta revisión de README/fechas **no necesita migración**. No ejecutar `seed-demo`, `configure-ev2-demo`, `configure-demo-locations` ni importadores para actualizar presentación o activar EV3. Esos configuradores son herramientas específicas del piloto; su alcance e idempotencia se describen en [verificación](docs/VERIFICACION.md) y [arquitectura](docs/ARQUITECTURA.md).

Los valores históricos en mm/s siguen siendo velocidad de vibración, incompatibles con aceleración en m/s²; no se convierten ni reclasifican. Condiciones y reglas históricas conservan sus escalas y asociaciones. Las referencias nuevas de inclinación no cambian la referencia/variación guardada en mediciones anteriores.

## Configuración y arquitectura

La aplicación usa Flask/Jinja, sin framework frontend adicional. SQLite/fotos privadas locales y el proveedor/worker son procesos independientes. En Vercel se requiere PostgreSQL y Storage privado de Supabase; no se permite usar almacenamiento local efímero para datos o fotos. [Arquitectura](docs/ARQUITECTURA.md) y [operación de nube](docs/SUPABASE_VERCEL.md) detallan migración, respaldos y Cron. Los apartados históricos de esos documentos describen sus propias ejecuciones, no sustituyen el estado de este README.

| Variable | Uso |
|---|---|
| `PROJECT_STAGE` | Etapa de web y worker; EV3: `cutoff_2026_11_09`. |
| `SECRET_KEY` | Clave estable de sesión obligatoria en nube; local puede conservar `instance/session.key`. |
| `COOKIE_SECURE=1` | Cookie solo HTTPS para uso institucional. |
| `DATABASE_URL`, `DATABASE_SCHEMA` | PostgreSQL y esquema (`puentes` por defecto); sin URL, SQLite local. |
| `PHOTO_STORAGE` | `local` o `supabase`; Vercel requiere `supabase`. |
| `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `SUPABASE_STORAGE_BUCKET` | Acceso servidor a Storage privado; bucket predeterminado `puentes-fotos`. |
| `PROVIDER_URL`, `PROVIDER_TOKEN` | Proveedor HTTP local y token opcional. |
| `IOT_POLL_INTERVAL` | Intervalo de worker; predeterminado 60 s, argumento CLI tiene prioridad. |
| `IOT_API_KEY` | Clave Bearer para POST municipal `/api/v1/measurements`; sin ella la recepción alternativa responde 503. |
| `CLOUD_PROVIDER=1`, `CRON_SECRET` | Proveedor simulado de nube y autorización de `/internal/iot/pull`. |
| `PUENTES_TEST_DATABASE_URL` | **Solo pruebas:** rol/esquema aislado `puentes_test`; nunca una URL productiva. |

No versionar valores privados ni imprimir credenciales en logs. No copiar la base local sobre producción: las dos instalaciones no se sincronizan automáticamente. Un despliegue no respalda PostgreSQL ni los objetos de Storage.

## Operación IoT y reglas

Flujo: sensor/plataforma del proveedor → API del proveedor → cliente municipal. El proveedor incluido es simulado y exige procedencia explícita, identidad y mediciones válidas; se conservan ID externo único, deduplicación y auditoría por elemento.

```powershell
# Terminal del proveedor local
.\.venv\Scripts\python.exe mock_provider.py --port 5100
# Otra terminal, con la misma etapa que la web
$env:PROJECT_STAGE='cutoff_2026_11_09'
$env:PROVIDER_URL='http://127.0.0.1:5100/measurements'
.\start-iot.ps1 -Interval 60
```

Ejecutar un solo worker. Consulta inicial inmediata, intervalo configurable de 1–86400 s, bloqueo por base y recuperación ante fallos. El cliente HTTP tiene timeout de 3 s, hasta 3 intentos y espera exponencial para desconexiones/429/5xx. Consulta manual por DOM o `flask --app app pull-provider`. Cada elemento usa savepoint para que un registro inválido no impida guardar los válidos; se conserva la identidad/motivo de incidencias en auditoría.

La instalación de nube dispone de recepción protegida para Supabase Cron; el procedimiento existente programa el proveedor simulado cada minuto. No se ha modificado ni vuelto a validar el trabajo Cron remoto en esta revisión. La API alternativa mantiene Bearer `IOT_API_KEY`, JSON ISO con zona, respuestas de validación y contrato existentes; véase [contrato y operación](docs/SUPABASE_VERCEL.md).

Los niveles asumidos del piloto están en `config/ev2_pilot.json`; no son un diagnóstico estructural ni umbrales validados externamente. Se compara de forma inclusiva y se genera una alerta del nivel más alto alcanzado. Inclinación usa `abs(lectura − referencia)`, con referencia y variación conservadas por lectura; sin referencia se informa que no es evaluable. Condiciones visuales nuevas usan Baja/Media/Alta/Crítica y reglas configurables, sin equivalencias automáticas con categorías históricas. Esta revisión no cambia generación de alertas, umbrales, integración ni permisos.

## Seguridad y respaldo

Autenticación local con hash de contraseñas, permisos del lado servidor, rotación de sesión al ingresar, CSRF, CSP y auditoría. Fotos privadas JPEG/PNG verificadas y recodificadas: hasta 5 imágenes, 20 megapíxeles por imagen y 20 MB por petición. HTTPS y secretos estables por entorno para uso institucional; en una instalación local de red, Waitress detrás de TLS.

`instance/`, `.env*`, `.vercel/`, bases, fotografías y credenciales se excluyen de Git. Respaldar SQLite/fotos/clave juntos o, en nube, PostgreSQL y Storage según el procedimiento operativo. No desactivar permisos o protecciones para ejecutar pruebas.

## Pruebas y evidencia

```powershell
.\.venv\Scripts\python.exe tools/run_ev3_checks.py --output docs/evidence/EV3_CHILE_TIME_TEST_RESULTS.json
# Por separado:
.\.venv\Scripts\python.exe -m unittest discover -v
node --test tests/frontend.test.cjs tests/cloud-uploads.test.cjs tests/notifications.test.cjs
```

El runner usa SQLite temporal y, únicamente si se proporciona la URL aislada, PostgreSQL `puentes_test`. Sin esa URL registra omisiones explícitas; no deben declararse aprobadas. Las fixtures PostgreSQL reinician **sus tablas de prueba**. Las verificaciones de navegador también usan una base local temporal, nunca registros productivos.

| Ejecución | Resultado real | Evidencia |
|---|---|---|
| Revisión actual de README y fechas Chile | 117 Python aprobadas, incluidas 15 PostgreSQL aisladas; 20 JavaScript aprobadas; cero fallos, errores y omisiones. | [Resultado por caso](docs/evidence/EV3_CHILE_TIME_TEST_RESULTS.json) |
| Corrección posterior de paginación de Mediciones | 18 pruebas afectadas aprobadas, incluida PostgreSQL; no fue una suite completa nueva. Chrome 20/20/5. | [Log](docs/evidence/EV3_MEASUREMENTS_PAGINATION_TESTS.log), [Chrome](docs/evidence/EV3_MEASUREMENTS_PAGINATION_BROWSER.json) |
| Revisión final UI anterior | 108 Python aprobadas, incluidas 12 PostgreSQL; 20 JavaScript; cero omisiones/fallos. | [Resultado](docs/evidence/EV3_UI_FINAL_TEST_RESULTS.json) |
| Primera revisión UI | 95 Python aprobadas, 10 PostgreSQL omitidas; 16 JavaScript. | [Resultado histórico](docs/evidence/EV3_UI_TEST_RESULTS.json) |
| Incremento B-11 | 98 Python y 10 JavaScript aprobadas, con PostgreSQL aislado y sin omisiones. | [Resultado histórico](docs/evidence/EV3_B11_TEST_RESULTS.json) |

La primera corrida de esta revisión detectó una incompatibilidad SQL entre SQLite/PostgreSQL (3 fallos y 2 errores); se corrigió y se repitió la suite completa. [Detalle de esta revisión](docs/REVISION_FECHAS_CHILE.md). No se suman ejecuciones ni se atribuyen resultados viejos a código nuevo. [Verificación detallada](docs/VERIFICACION.md), [revisión UI anterior](docs/REVISION_FINAL_EV3_UI.md), [diseño](docs/DISENO.md), [usabilidad](docs/USABILIDAD.md) y [matriz de requisitos](docs/CUMPLIMIENTO.md).

## Alcance pendiente

El ciclo completo de mantenimiento y programaciones pertenece a etapas posteriores; RF-7/HU-07 conservan en EV3 el seguimiento y la trazabilidad de alertas e inspecciones. HU-09, aceptación municipal, piloto real, capacitación, hardware/proveedor real y validación externa no se declaran completados.

Los [mockups del corte](docs/mockups.html) y [del modo completo](docs/mockups-full.html) son bocetos históricos; no sustituyen las pantallas actuales. El [túnel temporal local](docs/PUBLICACION.md) requiere el computador encendido y es una alternativa distinta de la publicación Vercel.
