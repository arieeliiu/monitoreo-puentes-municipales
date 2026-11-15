# Reporte 1.5.2.4 — Panel de Monitoreo

## Verificación final del PR #1

Alcance: B-14 / panel. Últimas lecturas de ambos puentes, no disponible/sin lecturas, alertas abiertas, actividades pendientes propias de Mantención, enlaces y permisos de los tres roles. En 28/11 no se consulta ni muestra programación; sus rutas siguen bloqueadas. Paridad SQLite/PostgreSQL comprobada. Los IDs de casos de las tablas siguientes también están aprobados en el JSON final; los resultados anteriores conservan sus fechas y contadores históricos.

Ejecución real de `2026-11-14T22:04:07-03:00` a `2026-11-14T22:16:51-03:00`, zona America/Santiago. **135 pruebas Python (incluidas 18 PostgreSQL aisladas) y 20 JavaScript aprobadas; 0 fallos, 0 errores y 0 omisiones**. Entorno: Windows, Python 3.12.14, SQLite 3.53.1, Node.js mediante las tres suites `node --test`; PostgreSQL con rol/esquema aislado `puentes_test`. No se usó producción. [JSON de la ejecución final](evidence/EV3_PR1_FINAL_TEST_RESULTS.json); [log completo](evidence/EV3_PR1_FINAL_TEST_RUN.log).

Versión probada: **`f17bb26a9b911b95c732a1fa1e9038cb7ccdd0d8`**, rama `feature/ev3-cierre-tecnico`, worktree limpio al inicio. Base de comparación: `origin/main` / `e191aed818b8ee94296594f633ed2afe8111ec3d`; la base no es la versión ejecutada. Los 62 archivos del manifiesto corresponden a los blobs Git de HEAD y sus SHA-256 permanecieron iguales hasta finalizar. Durante la ejecución solo se redactó documentación fuera de ese manifiesto; `finished_revision` deja constancia del estado final. Los commits documentales posteriores no se presentan como ejecuciones adicionales.

La evidencia anterior `EV3_CIERRE_TECNICO_TEST_RESULTS.json` se conserva sin cambios como histórica (132 Python + 20 JS). Sus **61/61 SHA-256** coincidieron con el worktree limpio del PR en `229e224` antes de estas correcciones: [cotejo fechado, por archivo](evidence/EV3_PR1_HISTORICAL_SOURCE_AUDIT.json). La ejecución anterior ocurrió sobre cambios locales con HEAD/base `e191aed`; no se atribuye retrospectivamente a `229e224`, creado después. Las capturas y seis comprobaciones de navegador `EV3_CIERRE_BROWSER.json` también son históricas; no se repitieron en esta revisión documental/de trazabilidad.

Etapas vigentes: `cutoff_2026_10_26`: funciones básicas y captura sin evaluación de alertas; `cutoff_2026_11_09`: captura/reglas/alertas con inicio básico y sin mantenimiento; `cutoff_2026_11_28`: añade panel avanzado y mantenimiento, sin programación; `full`: todas las funciones existentes, incluidas inspecciones programadas.

Repetición desde la raíz: `python tools/run_ev3_checks.py --output docs/evidence/EV3_PR1_FINAL_TEST_RESULTS.json`, solo si esa salida no existe. Para otra ejecución usar un nombre nuevo. El runner se niega a sobrescribir evidencia; PostgreSQL requiere `PUENTES_TEST_DATABASE_URL` del rol restringido de pruebas. Sin DSN se registran omisiones, no el resultado completo aquí acreditado.

Estado: preparado técnicamente para revisión; sin aprobación ni entrega formal atribuida al equipo. Publicación y eventual D7 productiva **no ejecutadas**. [Procedimiento operativo](PLAN_PUBLICACION_EV3.md); [índice Ariel](ENTREGA_ARIEL_EV3.md).

### Antecedentes conservados

Las secciones siguientes, incluidas sus tablas y evidencia de navegador, corresponden a ejecuciones anteriores. No se suman a esta ejecución ni se cambian sus fechas.

## Objetivo B-14 / EDT 1.4.5

Verificar y habilitar la implementación preliminar existente en `cutoff_2026_11_28`, sin rediseño general. Se conservan tarjetas, últimas lecturas, alertas, pendientes, observaciones y enlaces existentes. Se condicionó la consulta y el bloque de programación a su feature flag: no son parte de este corte. Los criterios de visualización se ejercitan mediante puentes y enlaces a consultas filtradas existentes, sin agregar nuevos filtros ni diagnósticos.

Fecha real de ejecución: **2026-11-14**, America/Santiago; inicio `2026-11-14T21:35:53-03:00`, término `2026-11-14T21:48:52-03:00`. El nombre del corte 28/11/2026 describe alcance, no la fecha de estas pruebas ni un hito declarado cumplido.

Ambiente: Windows, Python 3.12.14, SQLite 3.53.1, Node.js y PostgreSQL remoto con usuario y esquema restringidos `puentes_test`. Las fixtures y fotos son temporales. El runner elimina variables productivas y solo admite un DSN de pruebas restringido. No se conectó a datos productivos ni se modificó Vercel, Cron, Storage o credenciales.

Suite final completa: **132 pruebas Python (incluidas 18 PostgreSQL aisladas) y 20 JavaScript aprobadas; 0 fallos, 0 errores y 0 omisiones**. Son 12 regresiones SQLite nuevas y 3 PostgreSQL nuevas, además de la suite previa; no se suman ensayos ni se duplican pruebas heredadas. [JSON de resultados por caso, fechas, duración, contadores y SHA256](evidence/EV3_CIERRE_TECNICO_TEST_RESULTS.json); [log íntegro](evidence/EV3_CIERRE_TECNICO_TEST_RUN.log).

## Casos, entradas y resultados

| Caso / ID en JSON | Datos utilizados | Resultado esperado | Resultado obtenido | Estado |
|---|---|---|---|---|
| `tests.test_ev3_closure.ClosureStageTests.test_cutoff_configuration_roles_and_no_plan_queries` | Nuevo corte, DOM/Inspector/Mantención; lectura de páginas; GET/POST programación y plan_id manipulado. | Panel/mantenimiento accesibles, reglas solo DOM; programación 404 y ninguna consulta de programaciones. | 200 en módulos permitidos, 403 de reglas para otros roles, 404 en programación; sin escrituras y sin SELECT de inspection_plans. | Aprobado |
| `tests.test_ev3_closure.ClosureStageTests.test_dashboard_latest_readings_alert_states_and_visual_separation` | Dos puentes; S1 pasa de 1,25 a 6,25; S2 no disponible; S3 7,5; observación visual y cierre explícito de una alerta. | Mostrar últimas mediciones reales, estados, alertas abiertas y observaciones separadas; enlaces al puente/historial/origen. | Se muestran 6,25 y 7,5, no 1,25; No disponible; observación visual diferenciada; tras cierre, solo la otra alerta permanece en abiertas. Lectura no cambia filas. | Aprobado |
| `tests.test_ev3_closure.ClosureStageTests.test_dashboard_pending_assignments_and_empty_states` | Sin mediciones/reglas/inspecciones; luego dos actividades de distintos responsables; completar la propia. | Estados vacíos explícitos; pendientes de Mantención solo propios; Inspector consulta sin editar. | Sin datos/reglas/alertas/inspecciones y pendientes explícitos; Mantención no ve pendiente ajeno; la completada sale de pendientes; Inspector POST 403. | Aprobado |
| `tests.test_ev3_closure.ClosureStageTests.test_historical_stages_and_four_mode_switch_preserve_rows` | Alternancia de cuatro modos con datos poblados. | No alterar históricos ni adelantar funcionalidades. | Filas idénticas; programación solo en full; panel/mantenimiento solo en 28/11 y full. | Aprobado |
| `tests.test_cloud.PostgresTests.test_postgres_closure_panel` | Mismos datos de última lectura/estado/observación y tres roles sobre PostgreSQL aislado. | Paridad de presentación y relaciones sin programación. | Caso aprobado; panel responde y programación 404; datos relacionados coherentes. | Aprobado |

## Contadores observados por fixture

| Caso (sufijo) | Mediciones | Inspecciones | Reglas | Alertas | Actividades |
|---|---:|---:|---:|---:|---:|
| `test_cutoff_configuration_roles_and_no_plan_queries` | 0 | 0 | 0 | 0 | 0 |
| `test_dashboard_latest_readings_alert_states_and_visual_separation` | 4 | 1 | 2 | 2 | 0 |
| `test_dashboard_pending_assignments_and_empty_states` | 0 | 0 | 0 | 0 | 2 |
| `test_historical_stages_and_four_mode_switch_preserve_rows` | 1 | 1 | 1 | 1 | 1 |

## Evidencia de interfaz y persistencia

Revisión manual real de los tres roles en navegador local, con SQLite temporal. DOM observa PM-001/PM-002, 1,0/2,5 m/s², dos alertas abiertas y sensores sin lecturas; no aparecen programación ni aviso retirado. Se siguió el vínculo entre panel, actividad y alerta. [Captura del panel](evidence/EV3_CIERRE_PANEL.png), [observaciones y filas persistidas](evidence/EV3_CIERRE_BROWSER.json), [HTTP local](evidence/EV3_CIERRE_BROWSER_SERVER.log). Seis comprobaciones manuales aprobadas; no se suman al conteo automatizado. No hubo errores de consola observados.

## Limitaciones y pendientes

La verificación es técnica con datos de referencia y proveedores simulados. No acredita hardware, interoperabilidad nueva, diagnóstico estructural, piloto operacional, marcha blanca, capacitación ni UAT municipal. No se publicaron estos cambios. Revisión del equipo, autorización de migración D7/entorno, publicación y prueba posterior quedan pendientes. Las etapas históricas y sus registros se conservan; no hay reevaluación retroactiva.

Reproducción desde la raíz: ejecutar `python tools/run_ev3_checks.py` con el intérprete del entorno y, para PostgreSQL, solo `PUENTES_TEST_DATABASE_URL` del rol restringido. Sin el DSN se registran omisiones y no se puede atribuir el resultado completo de este reporte. El runner ejecuta unittest y las tres suites Node, y guarda un JSON nuevo sin sobrescribir los informes históricos B-11.

El término planificado 24/11, el corte 28/11 y la entrega 30/11 son hitos acordados, no resultados acreditados por ejecutar estas pruebas antes. B-14 requiere revisión compartida de Ariel/Christian y revisión de Alex; publicación pendiente de autorización.
