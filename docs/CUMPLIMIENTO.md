# Matriz de cumplimiento

Fecha objetivo inalterada: **26/11/2026**. Los rangos de CA fueron entregados sin el texto individual de cada criterio. Esta tabla acredita los requisitos funcionales explícitos del encargo; el cotejo individual de cada CA queda pendiente de recibir su definición oficial.

| EDT | HU / rango solicitado | Implementación | Evidencia automatizada |
|---|---|---|---|
| 1.4.2 | HU-01 / CA-01.1–01.8 | Alta/edición/fichas de puentes, criticidad, componentes, sensores, unicidad y validación, permisos DOM | `test_bridge_crud_and_duplicates`, `test_components_sensors_validation_and_edits`, `test_role_permissions` |
| 1.4.3 | HU-02 / CA-02.1–02.8 | Recepción local/API, unidad/fecha/estado, asociación al puente por sensor/componente, historial filtrado | `test_measurement_validation_and_history`, `test_iot_auth_idempotency_and_unavailable_configuration` |
| 1.4.3 | HU-03 / CA-03.1–03.8 | Inspección con autor autenticado, condición, fecha y descripción; fotos opcionales; ficha e historial | `test_photo_upload_and_authorization`, `test_bad_photo_and_cross_bridge_inspection_rollback` |
| 1.4.4 | HU-04 / CA-04.1–04.9 | Reglas numéricas/visuales, pruebas identificadas, referencia de validación para reglas oficiales, generación atómica, origen y estado; aviso sin reglas | `test_alert_threshold_and_simulation`, `test_inclination_and_visual_alert`, `test_official_rule_requires_reference` |
| 1.4.5 | HU-05 / CA-05.1–05.8 | Dos puentes demo, últimas mediciones según fecha, sin datos/no disponible, alertas abiertas, enlaces a históricos/fichas/fotos | `test_dashboard_empty_and_missing_latest`, `test_all_pages_render` |
| 1.4.6 | HU-06 / CA-06.1–06.8 | Tareas por puente/componente, responsable, planificación, edición/reasignación DOM, ejecución por asignado | `test_maintenance_assignment_tracking_and_explicit_resolution`, `test_cross_bridge_task_and_bad_assignee`, `test_role_permissions` |
| 1.4.6 | HU-07 / CA-07.1–07.8 | Alerta enlazada al origen, notas con inspección, actividades, autor/fecha, cierre DOM justificado | `test_maintenance_assignment_tracking_and_explicit_resolution` |
| 1.3 | Integración | API receptora configurable y simulador local implementados. Integración real pendiente | Prueba de API local; sin verificación de proveedor |
| 1.2.1 | Diseño funcional | Mockups navegables y flujos de cinco funcionalidades coherentes con las rutas reales | `docs/mockups.html`, render de todas las vistas en pruebas |
| Transversal | Autenticación, persistencia, auditoría | Hash de contraseñas, CSRF, roles, SQLite, fotos privadas, registro de operaciones | `test_csrf_and_xss`, `test_persistence_after_app_recreation`, pruebas de roles y trazabilidad |

No se declaran validados los umbrales, la integración real ni los CA cuyo texto no se proporcionó. La disponibilidad de datos no equivale a un dictamen estructural.
