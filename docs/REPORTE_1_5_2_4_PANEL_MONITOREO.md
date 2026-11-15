# Reporte 1.5.2.4: Panel de Monitoreo

## Resumen

Se probó B-14: módulo 1.4.5. **147 Python (incluidas 20 PostgreSQL aisladas) y 20 JavaScript aprobadas; cero fallos, errores u omisiones**. Ejecución real: 15/11/2026 15:49:06 a 15/11/2026 16:04:02 (America/Santiago). Código probado: `e71352105fd1f5a3d109f273150c22290b6cea1b`. [JSON por caso](evidence/EV3_CHRISTIAN_TEST_RESULTS.json) y [log](evidence/EV3_CHRISTIAN_TEST_RUN.log).

Limitación principal: proveedor de referencia y entornos aislados; no es aceptación municipal ni verificación de un despliegue nuevo.

## Objetivo

Verificar últimas lecturas por puente, estados sin datos, alertas, pendientes, inspecciones visuales y navegación por rol en corte 28/11, sin programación de inspecciones.

## Fecha y ambiente

Fecha real: **15/11/2026**; intervalo 15/11/2026 15:49:06 a 15/11/2026 16:04:02 (America/Santiago). Windows, Python 3.12.14, SQLite 3.53.1, Node.js con tres suites `node --test`; PostgreSQL remoto con usuario/esquema restringidos `puentes_test`. Fotos y HTTP/worker locales temporales. El runner limpia variables productivas. No se usó la base publicada ni se modificó Vercel/Storage.

## Casos, datos y resultados

| Caso verificable en JSON | Datos utilizados | Resultado esperado | Resultado obtenido | Estado |
|---|---|---|---|---|
| `tests.test_ev3_closure.ClosureStageTests.test_dashboard_latest_readings_alert_states_and_visual_separation` | Dos puentes; S1 1,25 luego 6,25; S2 no disponible; S3 7,5; observación visual. | Últimas lecturas, estado explícito y observación separada; enlaces correctos. | Se muestran 6,25 y 7,5, no 1,25; No disponible, alerta/observación y enlaces comprobados. | Aprobado |
| `tests.test_ev3_closure.ClosureStageTests.test_dashboard_pending_assignments_and_empty_states` | Base sin lecturas/inspecciones y dos responsables con pendientes. | Vacíos explícitos; Mantención ve solo pendientes propios y completados salen del panel. | Vacíos y filtros por asignación comprobados; Inspector no modifica. | Aprobado |
| `tests.test_ev3_closure.ClosureStageTests.test_cutoff_configuration_roles_and_no_plan_queries` | DOM/Inspector/Mantención, rutas de módulos y plan_id manipulado. | Funciones permitidas 200, permisos 403 y programación 404 sin SELECT ni escrituras. | 200/403/404 según alcance; ausencia de bloque y consulta de programaciones. | Aprobado |
| `tests.test_cloud.PostgresTests.test_postgres_closure_panel` | Últimas lecturas y estados con PostgreSQL aislado y tres roles. | Paridad del panel sin programación. | Caso aprobado en PostgreSQL; relaciones y permisos conservados. | Aprobado |

## Evidencia y reproducción

La suite completa común a los cuatro informes aprobó **147 Python (incluidas 20 PostgreSQL aisladas) y 20 JavaScript aprobadas; cero fallos, errores u omisiones**. Cada ID de la tabla figura en el JSON principal con estado, fecha y duración; los casos que lo generan también contienen contadores/filas observados en `facts`. El manifiesto SHA-256 y la referencia probada están en ese archivo; los detalles de Git se concentran en [verificación](VERIFICACION.md).

Reproducir desde la raíz: `python tools/run_ev3_checks.py --output docs/evidence/EV3_CHRISTIAN_TEST_RESULTS.json`, solo si esa ruta no existe; para una nueva ejecución elegir otro nombre. PostgreSQL requiere exclusivamente PUENTES_TEST_DATABASE_URL del rol restringido. Sin DSN se registran omisiones y no se puede atribuir el resultado completo. El runner nunca sobrescribe resultados anteriores.

## Alcance y pendientes

Las mediciones provienen del proveedor de referencia; el alcance no incluye sensores físicos (SC-01). No se acredita conexión física, certificación externa, piloto operacional, marcha blanca ni UAT municipal. El token pull es opcional/global y el cliente admite HTTP local; HTTPS obligatorio y credenciales independientes por proveedor siguen pendientes. No se desplegó ni migró producción; SC-04 requiere formalización. Etapas intactas: EV2 básico, 09/11 con reglas/alertas sin panel avanzado/mantenimiento, 28/11 con panel/mantenimiento sin programación, full con funcionalidades completas existentes. Revisión y entrega formal pendientes, sin atribuir aprobaciones posteriores a Christian, Alex o la profesora.

## Antecedentes conservados

| Fecha de ejecución | Versión identificable | Resultado anterior | Evidencia |
|---|---|---|---|
| 08/11/2026 | Fuentes por SHA-256; sin atribuir commit posterior | 98 Python + 10 JavaScript aprobadas | [B-11](evidence/EV3_B11_TEST_RESULTS.json) |
| 14/11/2026, 21:35 | Worktree sobre e191aed; fuentes por SHA-256 | 132 Python + 20 JavaScript aprobadas | [Cierre anterior](evidence/EV3_CIERRE_TECNICO_TEST_RESULTS.json) |
| 14/11/2026, 22:04 | f17bb26 | 135 Python + 20 JavaScript aprobadas | [Revisión anterior](evidence/EV3_PR1_FINAL_TEST_RESULTS.json) |

Estos resultados no se suman a la ejecución principal. Las capturas anteriores conservan su fecha y alcance; no se presentan como nuevas capturas de esta revisión.

[Informe anterior íntegro, sin reescribir sus resultados](REPORTE_1_5_2_4_PANEL_MONITOREO_HISTORICO_ba0b74e.md). Las capturas de su sección histórica conservan su contexto; no son capturas nuevas del código revisado.
