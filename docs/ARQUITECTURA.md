# Arquitectura vigente — especificación EV2 y etapas EV3

## Cierre técnico EV3 — revisión del 2026-11-14

`cutoff_2026_11_28` añade únicamente advanced_dashboard y maintenance al corte B-11. El panel consulta/renderiza programaciones solo si inspection_plans está habilitada (full). Se reutilizan consultas, motor, estados y permisos. La habilitación funcional del corte es independiente del retiro de columnas de la revisión de Christian, descrito a continuación. `reference_data.py` comparte códigos neutrales entre seed y proveedores; [migración D7](MIGRACION_REFERENCIAS_D7.md) explícita y separada del arranque. [Informes y límites](CIERRE_TECNICO_EV3.md). Las fechas anteriores del documento son referencias históricas; los hitos vigentes son los del resumen de esta tarea.

La [verificación final del PR #1](CIERRE_TECNICO_EV3.md) diferencia el commit base del código probado mediante blobs Git, hashes SHA-256 y estado del worktree. [Plan operativo de publicación](PLAN_PUBLICACION_EV3.md); sin despliegue ni migración productiva ejecutados.

## Modelo y contrato revisados: 15/11/2026

El contrato v1 contiene ocho campos, sin `simulated`; tampoco existen esas columnas en bridges, measurements, inspections, rules o alerts. Modelo final: 13 tablas, 99 campos, 27 FK, 9 CHECK, 9 UNIQUE, 13 PK; PostgreSQL conserva cinco índices explícitos, 13 tablas con RLS y 13 políticas. No hay un indicador sustituto. [Inventario verificable](evidence/EV3_CHRISTIAN_SCHEMA.json).

`receive` y `evaluate` ya no reciben ni propagan clasificación de simulación. Push y pull conservan validación, Bearer/configuración del proveedor, deduplicación, savepoints y auditoría. Los proveedores emiten PM y los ocho campos oficiales. La carga inicial se identifica mediante firma de infraestructura y sensores/relaciones esperados; códigos por sí solos no autorizan modificaciones.

El código nuevo rechaza esquemas aún provistos de las columnas antiguas. D7 precede al retiro explícito y transaccional de `schema_revision.py`; no hay migración destructiva al arrancar. Se verifican hashes de filas conservadas e índices/restricciones/políticas. [Procedimiento](MIGRACION_REFERENCIAS_D7.md). Las mediciones provienen del proveedor de referencia; el alcance no incluye sensores físicos (SC-01). El token pull es opcional/global y el cliente permite HTTP local: no se afirma autenticación independiente por proveedor, HTTPS obligatorio ni conformidad externa.

## Navegación, paginación y avisos EV3

Se conservan los feature flags y todos los contratos de recepción/evaluación. `/measurements` y `/alerts` siguen siendo vistas separadas. El detalle de medición consulta sus alertas solo si la etapa las habilita. Reglas no cambia su motor: la separación se realiza en Jinja a partir de active y standard.

Alertas e historial ejecutan COUNT más SELECT con LIMIT 20/OFFSET, ordenados por created_at DESC,id DESC; las páginas fuera de rango se ajustan a la última, los parámetros inválidos se rechazan y los filtros se conservan en los enlaces. No hay paginación cosmética en JavaScript.

GET `/api/v1/measurement-series` (refinamiento UI) exige sesión de cualquier rol y no escribe. Parámetros `days` (1, 7 o 30) y opcionales `bridge_id`/`sensor_id`. Devuelve, por sensor, el máximo por intervalo (10 min o 1 h) de lecturas válidas EV2 —en inclinación, del cambio absoluto evaluado—, conteos por estado y, si la etapa habilita alertas, los umbrales vigentes. Agrega en SQL sobre la ventana pedida; los gráficos lo consultan cada 60 s con la pestaña visible.

GET `/api/v1/alert-notifications` exige sesión y rol DOM/Inspector/Mantención. En EV2 se bloquea antes de acceder a BD. Cada consulta obtiene abiertas (Activa/En atención) y último ID con un agregado; solo si hay IDs posteriores hace un segundo SELECT limitado a 20. La primera consulta fija una línea base sin avisos históricos. El cursor se conserva por usuario/etapa/sesión de login en sessionStorage de la pestaña. El identificador de sesión de avisos rota al autenticar y la respuesta se comprueba para impedir consumir una sesión cambiada.

Cliente sin dependencias externas: consulta normal cada 30 s; si `has_more` indica pendientes, continúa cada 1 s con descanso de 5 s tras cuatro lotes (20 por lote); timeout de 8 s, sin solapamiento, pausa de consultas en pestaña oculta, reintento de fallos transitorios y detención ante 401/403 o cambio de sesión. Usa textContent para contenido y enlaces locales por ID. No existe estado de lectura, nueva tabla ni escritura de históricos. Ver [regresiones y límites](REVISION_EV3_UI.md).

## Etapa configurable de presentación

`app.create_app` toma `PROJECT_STAGE` de la configuración explícita o del entorno y valida cuatro valores: `cutoff_2026_10_26` (predeterminado), `cutoff_2026_11_09`, `cutoff_2026_11_28` y `full`. `STAGE_FEATURES` y `feature_enabled()` centralizan las funciones disponibles para rutas, inicio, recepción, inspecciones y contexto Jinja; `cutoff_mode()` conserva su significado original de EV2. No depende del reloj ni de archivos de gestión.

| Etapa | alerts (reglas/evaluación/seguimiento) | advanced_dashboard | maintenance | inspection_plans |
|---|---|---|---|---|
| `cutoff_2026_10_26` | No | No | No | No |
| `cutoff_2026_11_09` | Sí | No | No | No |
| `cutoff_2026_11_28` | Sí | Sí | Sí | No |
| `full` | Sí | Sí | Sí | Sí |

El `before_request stage_access` bloquea por función las rutas futuras antes de sesión/CSRF/base de datos. EV2 conserva recepción sin consulta de reglas ni evaluación. EV3 usa la misma recepción y motor de full, sin duplicar validaciones ni cambiar esquema, reglas o unidades: mediciones válidas evaluables e inspecciones nuevas generan alertas con la versión activa correspondiente. La ausencia de regla/referencia y las lecturas inválidas/no disponibles mantienen sus resultados existentes sin alertas.

En los tres cortes (`cutoff_2026_10_26`, `cutoff_2026_11_09` y `cutoff_2026_11_28`) las inspecciones rechazan `plan_id` antes de escrituras/fotos y omiten la consulta de programaciones. Solo `full` habilita inspecciones programadas.

En `cutoff_2026_11_09`, el detalle de alerta no consulta tareas ni muestra mantenimiento y el inicio usa el resumen básico, sin consultas del panel avanzado. B-11 funciona sin depender de EDT 1.4.5/1.4.6. En `cutoff_2026_11_28`, el inicio sí muestra el panel avanzado, sus últimas mediciones, alertas y actividades pendientes; el detalle de alerta puede consultar y enlazar mantenimiento. DOM administra actividades, Mantención actualiza solo las asignadas e Inspector consulta. Completar una actividad no resuelve la alerta. Las notas y estados de alerta conservan sus permisos en ambos cortes EV3.

Web, CLI y worker comparten `create_app` y deben arrancar con la misma etapa. Cambiar de modo no escribe datos ni reevalúa históricos. No hay migración ni cambio automático de configuración productiva para B-11. Los apartados siguientes describen las capacidades conservadas de full; [reportes B-11](REPORTE_1_5_2_3_REGLAS_ALERTA.md) documentan el alcance intermedio.


En local se mantienen Flask/Jinja, SQLite, archivos fotográficos privados, proveedor HTTP independiente y worker periódico. La publicación usa PostgreSQL y Storage privados en Supabase, Flask en Vercel y Cron remoto; véase [arquitectura de nube](SUPABASE_VERCEL.md). Los cambios se concentran en el modelo de evaluación y presentación.

```mermaid
flowchart LR
    Proveedor[API del proveedor de referencia] --> Cliente[Cliente HTTP con reintentos]
    Cliente --> Recepcion[Identidad, unidad, valor, estado y fecha]
    Recepcion --> Referencia[Lectura y referencia guardadas por medición]
    Referencia --> Variacion[Inclinación: abs lectura menos referencia]
    Variacion --> Niveles[Comparación inclusiva y mayor severidad]
    Recepcion --> Niveles
    Niveles --> BD[(SQLite)]
    Inspector --> Visual[Baja / Media / Alta / Crítica]
    Visual --> Niveles
    BD --> Panel[Panel de monitoreo]
```

`KINDS` identifica unidades canónicas (m/s² para aceleración vertical pico y ° para inclinación). El proveedor entrega lectura bruta; la referencia se obtiene de la base, administrada por DOM, no de un campo no confiable del proveedor. `measurements` guarda referencia y variación de cada lectura EV2. Se resta con Decimal antes de convertir el resultado finito a almacenamiento REAL para conservar límites decimales exactos.

`config/ev2_pilot.json` configura los supuestos iniciales. `configure-ev2-demo` agrega componentes y configuraciones que no existen, sin sensores adicionales ni modificación de referencias definidas. `app.rules` valida finitud, no negatividad y orden de niveles y versiona reglas al guardar. `evaluate` filtra reglas activas EV2, compara >= y selecciona una sola severidad máxima, vinculando alerta/regla/medición. Visuales se comparan por condición exacta y también conservan la regla generadora. Una alerta no es diagnóstico estructural y las tareas no cambian su estado automáticamente.

## Migraciones e históricos

`schema.sql` crea el bootstrap local sin las cinco columnas retiradas; `migrations.py` agrega campos previos y llama a `ev2_migration.py`. EV2 agrega reference_value/previous_unit a sensores, reference_value/variation/specification a mediciones, standard/severity/unit a reglas, standard/severity a alertas y standard a inspecciones.

La ampliación del CHECK de inspecciones utiliza una nueva tabla con columnas originales, copia por nombre de columnas, conserva IDs, sustituye la tabla y comprueba foreign_key_check dentro de una transacción. La desactivación temporal de FK se limita a la migración y se restaura al finalizar. No se eliminan registros ni archivos, ni se cambia el valor/unidad de mediciones anteriores. Su specification queda historica; no se calcula retroactivamente la variación. Las categorías visuales anteriores se conservan sin equivalencia automática. Las reglas históricas no evalúan registros EV2; alertas pasadas conservan relaciones y no reciben una severidad inventada.

El cambio de unidad de configuración de sensores de vibración solo afecta a capturas nuevas; previous_unit conserva la configuración anterior. No es una conversión física. La actualización se aplica con web y worker detenidos y respaldo completo previo.

## Captura y seguridad

Manual y automática comparten validaciones y deduplicación. BEGIN IMMEDIATE serializa la recepción; savepoints evitan filas/alertas parciales por elemento. El worker es un proceso independiente con bloqueo de SO, configuración de intervalo, recuperación tras errores y conexiones cerradas por ciclo. Auditoría registra identidad/motivo de rechazos; fallos que impidan auditar se registran por logging.

Se mantienen autenticación, permisos, CSRF, CSP, carga fotográfica validada, relaciones de programación y mantenimiento y trazabilidad. La UI conserva los registros y trazabilidad interna sin el aviso retirado por D7. Los mockups se construyen desde estas plantillas y datos temporales.

Fechas documentales: 24/11/2026 término de EDT 1.4.5/1.4.6; 26/11/2026 presentación. El alcance cuantitativo EV2 prevalece sobre documentación histórica. No se declara proveedor real, validación externa ni aceptación HU-09.
