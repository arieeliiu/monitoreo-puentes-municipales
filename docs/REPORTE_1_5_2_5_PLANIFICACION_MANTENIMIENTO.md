# Reporte 1.5.2.5 — Planificación de Mantenimiento

## Objetivo B-14 / EDT 1.4.6

Habilitar y verificar creación, asignación, edición, consulta y seguimiento existentes de `full` en el corte 28/11. No se reconstruyó el módulo ni se ampliaron sus estados/procesos. DOM edita descripción, fecha, responsable y estado; Mantención actualiza estado exclusivamente en actividades asignadas; Inspector consulta. Las relaciones de infraestructura/origen se validan al crear y no se reasocian por campos manipulados al actualizar.

Fecha real de ejecución: **2026-11-14**, America/Santiago; inicio `2026-11-14T21:35:53-03:00`, término `2026-11-14T21:48:52-03:00`. El nombre del corte 28/11/2026 describe alcance, no la fecha de estas pruebas ni un hito declarado cumplido.

Ambiente: Windows, Python 3.12.14, SQLite 3.53.1, Node.js y PostgreSQL remoto con usuario y esquema restringidos `puentes_test`. Las fixtures y fotos son temporales. El runner elimina variables productivas y solo admite un DSN de pruebas restringido. No se conectó a datos productivos ni se modificó Vercel, Cron, Storage o credenciales.

Suite final completa: **132 pruebas Python (incluidas 18 PostgreSQL aisladas) y 20 JavaScript aprobadas; 0 fallos, 0 errores y 0 omisiones**. Son 12 regresiones SQLite nuevas y 3 PostgreSQL nuevas, además de la suite previa; no se suman ensayos ni se duplican pruebas heredadas. [JSON de resultados por caso, fechas, duración, contadores y SHA256](evidence/EV3_CIERRE_TECNICO_TEST_RESULTS.json); [log íntegro](evidence/EV3_CIERRE_TECNICO_TEST_RUN.log).

## Casos, entradas y resultados

| Caso / ID en JSON | Datos utilizados | Resultado esperado | Resultado obtenido | Estado |
|---|---|---|---|---|
| `tests.test_ev3_closure.ClosureStageTests.test_dom_forms_edit_reassignment_and_assigned_worker_followup` | DOM crea con puente/componente/alerta/responsable/fecha; edita y reasigna a usuario 4; Mantención intenta alterar campos protegidos junto al estado. | DOM administra planificación; solo responsable actualiza estado; relaciones conservadas; alerta independiente. | Creación/edición 302; responsable anterior 403; nuevo responsable completa sin alterar descripción, fecha ni relaciones protegidas. Alerta sigue Activa. | Aprobado |
| `tests.test_ev3_closure.ClosureStageTests.test_maintenance_validation_csrf_roles_and_cross_bridge_relations` | Obligatorios vacíos, puente inexistente, componente/alerta de otro puente, responsable no Mantención, fecha inválida, CSRF incorrecto y descripción HTML. | Rechazar sin escrituras; escapar texto y exigir rol/token. | Estados 200 con errores de formulario, 400 CSRF y 403 por rol según caso; snapshots intactos tras rechazos; HTML escapado. | Aprobado |
| `tests.test_ev3_closure.ClosureStageTests.test_maintenance_filters_inspector_readonly_and_alert_stays_open` | Dos actividades en puentes diferentes; Inspector filtra; Mantención pasa por En ejecución y Completada. | Filtros correctos, Inspector solo lectura, cierre de actividad no cierra alerta. | Consultas separadas por puente y vacío para inexistente; no hay formularios de creación/edición para Inspector; actividad Completada y alerta Activa. | Aprobado |
| `tests.test_ev3_closure.ClosureStageTests.test_dashboard_pending_assignments_and_empty_states` | Dos responsables con actividades pendientes. | Pendientes propios en panel de Mantención; no modificar desde Inspector. | Asignación ajena ausente; completada sale del panel de pendientes; POST Inspector 403. | Aprobado |
| `tests.test_cloud.PostgresTests.test_postgres_closure_maintenance` | Creación, edición, reasignación, campos protegidos, cierre y relaciones con PostgreSQL aislado. | Comportamiento equivalente a SQLite. | Caso aprobado: reasignación y cierre de actividad sin cierre de alerta, con permisos preservados. | Aprobado |

## Contadores observados por fixture

| Caso (sufijo) | Mediciones | Inspecciones | Reglas | Alertas | Actividades |
|---|---:|---:|---:|---:|---:|
| `test_dom_forms_edit_reassignment_and_assigned_worker_followup` | 1 | 0 | 1 | 1 | 1 |
| `test_maintenance_validation_csrf_roles_and_cross_bridge_relations` | 1 | 0 | 1 | 1 | 1 |
| `test_maintenance_filters_inspector_readonly_and_alert_stays_open` | 1 | 0 | 1 | 1 | 2 |
| `test_dashboard_pending_assignments_and_empty_states` | 0 | 0 | 0 | 0 | 2 |

## Formulario real → servidor → datos → respuesta

En navegador DOM creó para PM-001/Tablero la actividad ligada a alerta #1, responsable Mantención y día 24/11/2026. Luego editó descripción y estado En ejecución; Mantención completó la actividad desde su formulario limitado al estado. El detalle vinculado mostró alerta Activa y actividad Completada; Inspector consultó sin botones de escritura. [Captura](evidence/EV3_CIERRE_MANTENIMIENTO.png), [observaciones, datos y auditoría persistidos](evidence/EV3_CIERRE_BROWSER.json), [log HTTP 302/200](evidence/EV3_CIERRE_BROWSER_SERVER.log). Los datos pertenecen solo a esa base temporal; no acreditan una actividad operacional ni un hito realizado.

## Limitaciones y pendientes

La verificación es técnica con datos de referencia y proveedores simulados. No acredita hardware, interoperabilidad nueva, diagnóstico estructural, piloto operacional, marcha blanca, capacitación ni UAT municipal. No se publicaron estos cambios. Revisión del equipo, autorización de migración D7/entorno, publicación y prueba posterior quedan pendientes. Las etapas históricas y sus registros se conservan; no hay reevaluación retroactiva.

Reproducción desde la raíz: ejecutar `python tools/run_ev3_checks.py` con el intérprete del entorno y, para PostgreSQL, solo `PUENTES_TEST_DATABASE_URL` del rol restringido. Sin el DSN se registran omisiones y no se puede atribuir el resultado completo de este reporte. El runner ejecuta unittest y las tres suites Node, y guarda un JSON nuevo sin sobrescribir los informes históricos B-11.

Revisión frontend/procesos de Christian y revisión B-14 de Alex pendientes; sin rediseño solicitado ni trabajo atribuido a ellos como realizado. Término planificado 24/11, corte 28/11 y entrega EV3 30/11 se conservan.
