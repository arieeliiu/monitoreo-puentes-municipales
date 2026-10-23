# Matriz individual de criterios oficiales y alcance EV2

## Alcance visible del corte 26/10/2026

Esta matriz conserva la evidencia de implementación del modo `full`. La presentación predeterminada corresponde exclusivamente al alcance solicitado para el corte, sin cambiar las fechas ni los porcentajes de la documentación de gestión.

| Área | Corte `cutoff_2026_10_26` | Modo `full` |
|---|---|---|
| HU-01 infraestructura | Disponible con permisos y ubicaciones existentes | Disponible |
| HU-02 mediciones e integración simulada | Manual, API, proveedor, worker, validaciones e historial; evaluación por reglas pendiente | Disponible con evaluación EV2 |
| HU-03 inspecciones y fotos | Disponible; envío de `plan_id` rechazado | Disponible con programación |
| HU-04 reglas y alertas | Rutas bloqueadas; motor omitido; históricos conservados | Implementación conservada y activa |
| Panel completo, mantenimiento y programación | Ocultos y bloqueados en servidor | Implementaciones conservadas |

Evidencia nueva: `tests/test_project_stage.py` comprueba navegación por rol, bloqueo GET/POST sin escrituras, ausencia de consulta de reglas, formularios, fotos, API/worker reales sin alertas, programación manipulada y alternancia sobre datos/fotos poblados. La regresión previa configura `full` explícitamente. Las filas que siguen mantienen su significado como evidencia del modo completo, no como funciones demostradas en el corte.


Fuente literal: [transcripción oficial proporcionada](CRITERIOS_OFICIALES.md), localizada por el usuario en Descargas. Se cotejan implementaciones y pruebas, no solo pantallas. Prevalece EV2 actualizado del 22/10/2026: aceleración vertical pico, cambio respecto de referencia, niveles inclusivos y categorías visuales vigentes. La evidencia es de pruebas automatizadas de servidor y HTTP; no equivale a aceptación municipal.

**EDT 1.4.5 y 1.4.6: término planificado 24/11/2026. Presentación académica: 26/11/2026.**

| Criterio | Definición literal | Resultado | Implementación y prueba |
|---|---|---|---|
| CA-01.1 | El sistema permite registrar un puente con la información requerida por el proyecto. | Verificado en piloto académico | app.bridges / bridge; templates/bridges.html y bridge.html; `test_bridge_crud_and_duplicates` |
| CA-01.2 | El sistema valida que los campos obligatorios estén completos. | Verificado en piloto académico | app.bridges / bridge; templates/bridges.html y bridge.html; `test_bridge_crud_and_duplicates` |
| CA-01.3 | El sistema identifica cada puente mediante un identificador único. | Verificado en piloto académico | app.bridges / bridge; templates/bridges.html y bridge.html; `test_bridge_crud_and_duplicates` |
| CA-01.4 | El sistema permite consultar los puentes registrados. | Verificado en piloto académico | app.bridges / bridge; templates/bridges.html y bridge.html; `test_bridge_crud_and_duplicates` |
| CA-01.5 | El sistema permite visualizar la información asociada a un puente seleccionado. | Verificado en piloto académico | app.bridges / bridge; templates/bridges.html y bridge.html; `test_bridge_crud_and_duplicates` |
| CA-01.6 | El sistema permite modificar información de un puente cuando el usuario tiene los permisos correspondientes. | Verificado en piloto académico | app.bridges / bridge; templates/bridges.html y bridge.html; `test_bridge_crud_and_duplicates`; `test_role_permissions` |
| CA-01.7 | El sistema informa cuando se intenta registrar un puente con datos obligatorios incompletos. | Verificado en piloto académico | app.bridges / bridge; templates/bridges.html y bridge.html; `test_bridge_crud_and_duplicates` |
| CA-01.8 | El sistema evita duplicar registros cuando se detecta que el puente ya se encuentra registrado. | Verificado en piloto académico | app.bridges / bridge; templates/bridges.html y bridge.html; `test_bridge_crud_and_duplicates` |
| CA-02.1 | El sistema permite consultar las mediciones asociadas a un puente. | Verificado en piloto académico | app.receive / measurements / measurement; templates/measurements.html; `test_measurement_validation_and_history` |
| CA-02.2 | Cada medición se encuentra asociada al sensor y puente correspondiente. | Verificado en piloto académico | app.receive / measurements / measurement; templates/measurements.html; `test_provider_http_end_to_end_two_bridges_dedup_and_errors` |
| CA-02.3 | El sistema muestra el tipo de medición recibida. | Verificado en piloto académico | app.receive / measurements / measurement; templates/measurements.html; `test_all_pages_render` |
| CA-02.4 | El sistema muestra el valor registrado y su fecha y hora. | Verificado en piloto académico | app.receive / measurements / measurement; templates/measurements.html; `test_measurement_validation_and_history` |
| CA-02.5 | El sistema permite distinguir las mediciones recibidas de aquellas que presentan errores o no están disponibles. | Verificado en piloto académico | app.receive / measurements / measurement; templates/measurements.html; `test_measurement_validation_and_history` |
| CA-02.6 | El sistema informa cuando no existen mediciones disponibles para el puente seleccionado. | Verificado en piloto académico | app.receive / measurements / measurement; templates/measurements.html; `test_dashboard_empty_and_missing_latest` |
| CA-02.7 | El sistema permite consultar mediciones anteriores cuando se encuentran almacenadas. | Verificado en piloto académico | app.receive / measurements / measurement; templates/measurements.html; `test_measurement_validation_and_history` |
| CA-02.8 | El sistema no presenta como válida una medición que no haya superado las validaciones de recepción definidas. | Verificado en piloto académico | app.receive / measurements / measurement; templates/measurements.html; `test_measurement_validation_and_history` |
| CA-03.1 | El sistema permite seleccionar el puente inspeccionado. | Verificado en piloto académico | app.inspections / inspection / photo; templates/inspections.html; `test_schedule_roles_result_and_dashboard` |
| CA-03.2 | El sistema permite registrar la fecha de inspección. | Verificado en piloto académico | app.inspections / inspection / photo; templates/inspections.html; `test_photo_upload_and_authorization` |
| CA-03.3 | El sistema permite ingresar observaciones sobre el estado observado. | Verificado en piloto académico | app.inspections / inspection / photo; templates/inspections.html; `test_csrf_and_xss` |
| CA-03.4 | El sistema valida que la información obligatoria esté completa. | Verificado en piloto académico | app.inspections / inspection / photo; templates/inspections.html; `test_bad_photo_and_cross_bridge_inspection_rollback` |
| CA-03.5 | El sistema asocia la inspección con el puente correspondiente. | Verificado en piloto académico | app.inspections / inspection / photo; templates/inspections.html; `test_bad_photo_and_cross_bridge_inspection_rollback` |
| CA-03.6 | El sistema permite consultar inspecciones previamente registradas. | Verificado en piloto académico | app.inspections / inspection / photo; templates/inspections.html; `test_all_pages_render` |
| CA-03.7 | El sistema identifica la inspección mediante un registro individual. | Verificado en piloto académico | app.inspections / inspection / photo; templates/inspections.html; `test_photo_upload_and_authorization` |
| CA-03.8 | El sistema informa al usuario cuando no se puede guardar una inspección por falta de información obligatoria. | Verificado en piloto académico | app.inspections / inspection / photo; templates/inspections.html; `test_bad_photo_and_cross_bridge_inspection_rollback` |
| CA-04.1 | El sistema permite configurar reglas de alerta para los tipos de medición contemplados. | Verificado en piloto académico | app.rules / evaluate / alerts / alert; templates/rules.html y alert.html; `test_inclination_and_visual_alert` |
| CA-04.2 | Cada regla utiliza umbrales definidos o validados por la contraparte técnica. | Cumple alcance académico: supuestos de contraparte ficticia; sin validación real | app.rules / evaluate / alerts / alert; templates/rules.html y alert.html; `test_academic_rule_without_real_reference` |
| CA-04.3 | El sistema compara las mediciones recibidas con las reglas configuradas. | Verificado en piloto académico | app.rules / evaluate / alerts / alert; templates/rules.html y alert.html; `test_signed_and_absolute_inclination_boundaries` |
| CA-04.4 | Cuando una medición cumple una condición de alerta, el sistema genera el registro correspondiente. | Verificado en piloto académico | app.rules / evaluate / alerts / alert; templates/rules.html y alert.html; `test_alert_threshold_and_simulation` |
| CA-04.5 | La alerta queda asociada al puente y a la medición que la originó. | Verificado en piloto académico | app.rules / evaluate / alerts / alert; templates/rules.html y alert.html; `test_alert_threshold_and_simulation` |
| CA-04.6 | El sistema muestra la fecha y hora de generación de la alerta. | Verificado en piloto académico | app.rules / evaluate / alerts / alert; templates/rules.html y alert.html; `test_all_pages_render` |
| CA-04.7 | El sistema permite consultar las alertas generadas. | Verificado en piloto académico | app.rules / evaluate / alerts / alert; templates/rules.html y alert.html; `test_all_pages_render` |
| CA-04.8 | El sistema informa cuando no existen reglas configuradas para evaluar una medición. | Verificado en piloto académico | app.rules / evaluate / alerts / alert; templates/rules.html y alert.html; `test_no_rule_received_notice` |
| CA-04.9 | El sistema no presenta la alerta como un diagnóstico estructural ni como una decisión automática sobre la seguridad del puente. | Verificado en piloto académico | app.rules / evaluate / alerts / alert; templates/rules.html y alert.html; `test_official_views_and_required_fields` |
| CA-05.1 | El panel permite visualizar los puentes registrados. | Verificado en piloto académico | app.dashboard; templates/dashboard.html; `test_dashboard_empty_and_missing_latest` |
| CA-05.2 | El usuario puede seleccionar un puente para consultar su información. | Verificado en piloto académico | app.dashboard; templates/dashboard.html; `test_all_pages_render` |
| CA-05.3 | El panel muestra las mediciones disponibles asociadas al puente seleccionado. | Verificado en piloto académico | app.dashboard; templates/dashboard.html; `test_official_views_and_required_fields` |
| CA-05.4 | El panel permite identificar las alertas generadas. | Verificado en piloto académico | app.dashboard; templates/dashboard.html; `test_all_pages_render` |
| CA-05.5 | La información mostrada corresponde a los registros disponibles en el sistema. | Verificado en piloto académico | app.dashboard; templates/dashboard.html; `test_dashboard_empty_and_missing_latest` |
| CA-05.6 | El sistema informa cuando no existen mediciones o alertas para mostrar. | Verificado en piloto académico | app.dashboard; templates/dashboard.html; `test_dashboard_empty_and_missing_latest` |
| CA-05.7 | El panel permite distinguir los datos de medición de las observaciones visuales. | Verificado en piloto académico | app.dashboard; templates/dashboard.html; `test_schedule_roles_result_and_dashboard` |
| CA-05.8 | El usuario puede acceder desde el panel a la información relacionada con el puente seleccionado. | Verificado en piloto académico | app.dashboard; templates/dashboard.html; `test_schedule_roles_result_and_dashboard` |
| CA-06.1 | El sistema permite registrar una actividad de mantenimiento asociada a un puente. | Verificado en piloto académico | app.maintenance; templates/maintenance.html; `test_maintenance_assignment_tracking_and_explicit_resolution` |
| CA-06.2 | El sistema permite ingresar la información requerida para identificar la actividad. | Verificado en piloto académico | app.maintenance; templates/maintenance.html; `test_maintenance_assignment_tracking_and_explicit_resolution` |
| CA-06.3 | El sistema permite registrar una fecha planificada. | Verificado en piloto académico | app.maintenance; templates/maintenance.html; `test_maintenance_assignment_tracking_and_explicit_resolution` |
| CA-06.4 | El sistema permite consultar las actividades de mantenimiento registradas. | Verificado en piloto académico | app.maintenance; templates/maintenance.html; `test_maintenance_assignment_tracking_and_explicit_resolution` |
| CA-06.5 | El sistema permite identificar a qué puente corresponde cada actividad. | Verificado en piloto académico | app.maintenance; templates/maintenance.html; `test_maintenance_assignment_tracking_and_explicit_resolution` |
| CA-06.6 | El sistema permite modificar la información de una actividad según los permisos del usuario. | Verificado en piloto académico | app.maintenance; templates/maintenance.html; `test_dom_task_edit_and_inspector_followup` |
| CA-06.7 | El sistema informa cuando faltan datos obligatorios para registrar una actividad. | Verificado en piloto académico | app.maintenance; templates/maintenance.html; `test_official_views_and_required_fields` |
| CA-06.8 | El sistema permite consultar las actividades relacionadas con un puente seleccionado. | Verificado en piloto académico | app.maintenance; templates/maintenance.html; `test_maintenance_filter_and_missing_alert_relations` |
| CA-07.1 | El sistema permite consultar una alerta y la medición que la originó. | Verificado en piloto académico | app.alert / maintenance; templates/alert.html; schema.sql; `test_official_views_and_required_fields` |
| CA-07.2 | El sistema permite identificar el puente asociado a la alerta. | Verificado en piloto académico | app.alert / maintenance; templates/alert.html; schema.sql; `test_alert_threshold_and_simulation` |
| CA-07.3 | El sistema permite relacionar una alerta con una inspección registrada. | Verificado en piloto académico | app.alert / maintenance; templates/alert.html; schema.sql; `test_dom_task_edit_and_inspector_followup` |
| CA-07.4 | El sistema permite relacionar una alerta con una actividad de mantenimiento cuando corresponda. | Verificado en piloto académico | app.alert / maintenance; templates/alert.html; schema.sql; `test_maintenance_assignment_tracking_and_explicit_resolution` |
| CA-07.5 | El sistema permite consultar la información vinculada a una alerta. | Verificado en piloto académico | app.alert / maintenance; templates/alert.html; schema.sql; `test_maintenance_assignment_tracking_and_explicit_resolution` |
| CA-07.6 | El sistema conserva la relación entre alerta, puente y acción asociada. | Verificado en piloto académico | app.alert / maintenance; templates/alert.html; schema.sql; `test_migration_preserves_every_existing_table_row` |
| CA-07.7 | El sistema informa cuando una alerta no tiene una inspección o actividad asociada. | Verificado en piloto académico | app.alert / maintenance; templates/alert.html; schema.sql; `test_maintenance_filter_and_missing_alert_relations` |
| CA-07.8 | El sistema no marca una alerta como resuelta únicamente por haber generado una actividad de mantenimiento. | Verificado en piloto académico | app.alert / maintenance; templates/alert.html; schema.sql; `test_maintenance_assignment_tracking_and_explicit_resolution` |
| CA-08.1 | Se documentan las especificaciones disponibles de los sensores y de la plataforma IoT. | Documentado contrato simulado; especificaciones reales no disponibles | mock_provider.make_server; provider_client.fetch_measurements; app.pull_provider; `Contrato simulado: README.md / mock_provider.demo_records` |
| CA-08.2 | Se verifica la correspondencia entre los sensores y los componentes de la infraestructura. | Verificado exclusivamente en entorno IoT simulado | mock_provider.make_server; provider_client.fetch_measurements; app.pull_provider; `test_sensor_location_and_variable` |
| CA-08.3 | Se configura el acceso a la API del proveedor de acuerdo con las condiciones disponibles. | Verificado exclusivamente en entorno IoT simulado | mock_provider.make_server; provider_client.fetch_measurements; app.pull_provider; `test_provider_http_end_to_end_two_bridges_dedup_and_errors` |
| CA-08.4 | Se ejecutan pruebas de conectividad con la plataforma existente (1.3.5). | Verificado exclusivamente en entorno IoT simulado | mock_provider.make_server; provider_client.fetch_measurements; app.pull_provider; `test_provider_http_end_to_end_two_bridges_dedup_and_errors` |
| CA-08.5 | Se comprueba que los datos recibidos correspondan al formato esperado por el sistema. | Verificado exclusivamente en entorno IoT simulado | mock_provider.make_server; provider_client.fetch_measurements; app.pull_provider; `test_measurement_validation_and_history` |
| CA-08.6 | Se verifica que las mediciones recibidas puedan asociarse al puente y sensor correspondientes. | Verificado exclusivamente en entorno IoT simulado | mock_provider.make_server; provider_client.fetch_measurements; app.pull_provider; `test_provider_http_end_to_end_two_bridges_dedup_and_errors` |
| CA-08.7 | Se registran los resultados de las pruebas de integración. | Verificado exclusivamente en entorno IoT simulado | mock_provider.make_server; provider_client.fetch_measurements; app.pull_provider; `docs/VERIFICACION.md` |
| CA-08.8 | Se documentan los errores o limitaciones detectados durante la validación. | Verificado exclusivamente en entorno IoT simulado | mock_provider.make_server; provider_client.fetch_measurements; app.pull_provider; `test_retry_connection_and_bad_json` |
| CA-09.1 | Se ejecutan pruebas de aceptación para las cinco funcionalidades principales. | Pendiente: aceptación/operación/cierre posterior | No se declara ejecutado; fuera del alcance de estas correcciones. |
| CA-09.2 | Se documentan los resultados de las pruebas realizadas. | Pendiente: aceptación/operación/cierre posterior | No se declara ejecutado; fuera del alcance de estas correcciones. |
| CA-09.3 | Se registran los defectos o ajustes identificados. | Pendiente: aceptación/operación/cierre posterior | No se declara ejecutado; fuera del alcance de estas correcciones. |
| CA-09.4 | Se realizan los ajustes acordados para el piloto. | Pendiente: aceptación/operación/cierre posterior | No se declara ejecutado; fuera del alcance de estas correcciones. |
| CA-09.5 | Se ejecuta el piloto operacional contemplado en el proyecto. | Pendiente: aceptación/operación/cierre posterior | No se declara ejecutado; fuera del alcance de estas correcciones. |
| CA-09.6 | Se realiza la capacitación de los usuarios definidos, incluyendo inspectores, personal de mantención vial y DOM. | Pendiente: aceptación/operación/cierre posterior | No se declara ejecutado; fuera del alcance de estas correcciones. |
| CA-09.7 | Se entrega la documentación operativa acordada. | Pendiente: aceptación/operación/cierre posterior | No se declara ejecutado; fuera del alcance de estas correcciones. |
| CA-09.8 | La aceptación final y la firma corresponden al Patrocinador (Municipalidad), según el procedimiento de cierre establecido en el Acta (EDT 1.6.5). | Pendiente: aceptación/operación/cierre posterior | No se declara ejecutado; fuera del alcance de estas correcciones. |
| CA-09.9 | Se documenta el cierre de las condiciones del proyecto. | Pendiente: aceptación/operación/cierre posterior | No se declara ejecutado; fuera del alcance de estas correcciones. |


## Evidencia EV2 que complementa las filas individuales

| Requisito vigente / criterios relacionados | Evidencia funcional |
|---|---|
| Vibración = aceleración vertical pico en m/s²; CA-02.3, 02.4, 02.8 y HU-08 | `app.receive`, `mock_provider.demo_records`; `test_old_units_are_never_relabelled`, `test_ev2_provider_flow_both_bridges`. Históricos mm/s conservados, identificados y no reinterpretados. |
| Atención/Alerta/Crítico, >= y mayor severidad; CA-04.1–04.7 | JSON configurable + `app.rules`/`evaluate`; `test_numeric_levels_positive_negative_and_exact_limits`, `test_rule_configuration_versions_and_highest_only`. Una alerta por lectura; conserva regla de su versión. |
| Referencia configurable, cambio absoluto y ausencia explícita; CA-02.5, CA-04.3, HU-01 | `sensors.reference_value`, snapshots en measurements; `test_reference_offset_snapshot_missing_and_invalid`. Ambos sentidos y límites exactos con referencias no nulas. |
| Baja/Media/Alta/Crítica nuevas; HU-03 y CA-04.1/04.4 | `app.inspections`/`evaluate`; `test_visual_categories_and_configured_alerts`, `test_old_units_are_never_relabelled`. Sin equivalencia de categorías históricas. Fotos opcionales conservadas. |
| Tres componentes por puente, sensores configurables; RF-1 y HU-01 | `configure-ev2-demo`; `test_demo_setup_is_idempotent_and_customizable`, `test_fresh_demo_has_three_components_per_bridge`. No se inventan sensores físicos adicionales. |
| Interfaz operativa limpia, sin pérdida de datos; HU-05 | `test_professional_ui_and_severity_styles_all_roles`; niveles diferenciados en panel/historial. Ausencias y fallos se conservan. |
| Integración HTTP y worker para ambos puentes; HU-08 | `test_ev2_provider_flow_both_bridges` y suite de captura periódica/identidad. Solo proveedor simulado. |
| Preservación/migración | `ev2_migration.migrate_ev2`; `test_old_units_are_never_relabelled`, `test_migration_preserves_every_existing_table_row`. Fotos, IDs y relaciones preservados. |

Los valores son parámetros asumidos académicamente conforme a EV2; no se solicita validación externa para esta evaluación. Las alertas no son diagnósticos. Las definiciones oficiales de HU/CA se conservan en CRITERIOS_OFICIALES.md; sus detalles cuantitativos anteriores deben leerse con las correcciones EV2 de esta tabla. HU-09 sigue pendiente, sin declarar aceptación municipal.

## Evidencia de la corrección final de sensores

| Alcance | Evidencia adicional |
|---|---|
| HU-01: alta/edición de sensores y ubicaciones | `tests/test_final_fixes.py`: formularios HTML reales, opciones internas, selección persistida y permisos de los tres roles. Creación/edición comprobada también en navegador. `tests/frontend.test.cjs`: componentes habilitados en ficha sin selector de puente y filtro conservado en los demás formularios. |
| HU-01: conservación del piloto | `demo_locations.complete_demo_locations`, CLI `configure-demo-locations`: solo códigos originales simulados con ubicación pendiente. Pruebas de idempotencia, ubicación manual conservada, componentes reconocidos, exclusión de registros ajenos y reglas/asociaciones sin cambios. |
| HU-08: automatización y recuperación | `test_real_provider_and_periodic_worker_restart_recovery`: proveedor y worker en procesos separados, intervalo real de 1 s, ambos puentes, deduplicación, desconexión/reinicio, alertas EV2 y consulta manual. |

Resultado conjunto: 51 pruebas Python y 3 JavaScript aprobadas. HU-09 y la integración con hardware real conservan el estado previamente documentado.
