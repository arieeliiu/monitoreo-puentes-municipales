# Reporte 1.5.2.5: Planificación de Mantenimiento

## Resumen

Se probó B-14: módulo 1.4.6. **147 Python (incluidas 20 PostgreSQL aisladas) y 20 JavaScript aprobadas; cero fallos, errores u omisiones**. Ejecución real: 15/11/2026 15:49:06 a 15/11/2026 16:04:02 (America/Santiago). Código probado: `e71352105fd1f5a3d109f273150c22290b6cea1b`. [JSON por caso](evidence/EV3_CHRISTIAN_TEST_RESULTS.json) y [log](evidence/EV3_CHRISTIAN_TEST_RUN.log).

Limitación principal: proveedor de referencia y entornos aislados; no es aceptación municipal ni verificación de un despliegue nuevo.

## Objetivo

Verificar creación, edición, asignación y seguimiento; DOM administra, Mantención actualiza solo asignadas e Inspector consulta. Completar no cierra automáticamente la alerta.

## Fecha y ambiente

Fecha real: **15/11/2026**; intervalo 15/11/2026 15:49:06 a 15/11/2026 16:04:02 (America/Santiago). Windows, Python 3.12.14, SQLite 3.53.1, Node.js con tres suites `node --test`; PostgreSQL remoto con usuario/esquema restringidos `puentes_test`. Fotos y HTTP/worker locales temporales. El runner limpia variables productivas. No se usó la base publicada ni se modificó Vercel/Storage.

## Casos, datos y resultados

| Caso verificable en JSON | Datos utilizados | Resultado esperado | Resultado obtenido | Estado |
|---|---|---|---|---|
| `tests.test_ev3_closure.ClosureStageTests.test_dom_forms_edit_reassignment_and_assigned_worker_followup` | Formularios DOM con puente/componente/alerta/responsable; reasignar a usuario 4; campos protegidos manipulados. | Guardar cambios autorizados, restringir responsable y conservar relaciones. | 302 en creación/edición, responsable anterior 403; nuevo responsable completa y alerta sigue Activa. | Aprobado |
| `tests.test_ev3_closure.ClosureStageTests.test_maintenance_validation_csrf_roles_and_cross_bridge_relations` | Vacíos, puente inexistente, componente/alerta ajenos, responsable Inspector, fecha inválida y CSRF incorrecto. | Rechazar sin escrituras; preservar rol/CSRF y escapar HTML. | Errores de formulario/400/403 y snapshots intactos; texto escapado. | Aprobado |
| `tests.test_ev3_closure.ClosureStageTests.test_maintenance_filters_inspector_readonly_and_alert_stays_open` | Actividades de dos puentes; Inspector consulta; Mantención En ejecución y Completada. | Filtrar correctamente, Inspector sin formularios y alerta independiente. | Actividad Completada con alerta Activa; filtros/estado vacío y permisos comprobados. | Aprobado |
| `tests.test_cloud.PostgresTests.test_postgres_closure_maintenance` | Mismo flujo de creación/edición/asignación en PostgreSQL aislado. | Paridad de permisos y relaciones sin cierre automático. | Caso aprobado en PostgreSQL. | Aprobado |
| `tests.test_christian_review.ChristianTests.test_explicit_reference_load_complete_and_non_destructive` | Base nueva; PM-001/PM-002, cuatro sensores y carga explícita; repetir sobre base ocupada. | Crear datos relacionados y rechazar reemplazo de existentes. | 8 lecturas, 2 inspecciones y 2 actividades; actividad Completada conserva alerta En atención; repetición rechazada. | Aprobado |

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

[Informe anterior íntegro, sin reescribir sus resultados](REPORTE_1_5_2_5_PLANIFICACION_MANTENIMIENTO_HISTORICO_ba0b74e.md). Las capturas de su sección histórica conservan su contexto; no son capturas nuevas del código revisado.
