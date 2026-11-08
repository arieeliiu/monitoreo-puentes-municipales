# README y presentación de fechas de Chile

Rama `fix/readme-fechas-chile`, creada desde `origin/main` en `8af14f9`. El usuario autorizó posteriormente commit, integración y despliegue al terminar la validación. Este informe documenta las pruebas anteriores a la publicación; su resultado operativo se informa por separado. No se usaron credenciales ni datos productivos en las pruebas ni se cambió configuración remota.

## Cambios

README reorganizado por estado actual, funcionalidades, etapas, permisos, fechas, instalación, operación, arquitectura, variables, seguridad, pruebas y alcance pendiente. Reconoce que EV3 está integrada en main. Las ejecuciones históricas conservan sus resultados originales y enlaces, sin sumarse a la ejecución nueva.

Un filtro Jinja común convierte los instantes a America/Santiago usando zoneinfo y tzdata ya instalados. Formato DD/MM/AAAA HH:MM:SS con el desfase vigente UTC-03:00/UTC-04:00. Se aplica a Mediciones y recepción, Alertas y notas, Reglas y versiones, Inspecciones, Historial y fechas visibles de los módulos conservados del modo full. No convierte datos al guardarlos ni solicita permisos nuevos. Las fechas calendario planificadas conservan el día; los valores ISO de campos HTML date no se reemplazan por texto formateado.

Los filtros de Mediciones y Alertas ahora representan días locales de Chile. Se calcula antes de consultar el comienzo inclusivo del primer día y el inicio exclusivo del día siguiente al último en UTC. Incluye transiciones de 23/25 horas y el primer instante válido cuando la medianoche no existe. La consulta usa expresiones SQL compatibles con SQLite/PostgreSQL sobre timestamps UTC del contrato persistido. Mantiene filtros, orden y LIMIT 20/OFFSET; no carga ni pagina listas completas en Python.

Los timestamps sin zona se muestran literalmente con “zona horaria no registrada”; los no interpretables conservan su texto y aviso. No se presume su zona ni se incluyen como instantes conocidos en los filtros de días chilenos. Quedan consultables sin filtros de fecha. Los datos persistidos UTC admitidos en esos filtros usan +00:00 o Z (con T o espacio entre fecha y hora). No se migra ni reinterpreta una fecha histórica ambigua.

Notas, descripciones y detalles de auditoría son texto libre histórico y permanecen literales, aunque incluyan fechas. Las fechas estructuradas del evento sí se presentan en Chile.

## Pruebas reales

Ejecución final: **117 Python aprobadas, incluidas 15 PostgreSQL aisladas; 20 JavaScript aprobadas; cero fallos, errores y omisiones.** Del 2026-11-08T18:24:04-03:00 al 2026-11-08T18:35:04-03:00, America/Santiago.

- [Resultado por caso y hashes de fuente](evidence/EV3_CHILE_TIME_TEST_RESULTS.json).
- [Log completo final](evidence/EV3_CHILE_TIME_TEST_RUN.log).
- [Preflight del rol PostgreSQL aislado](evidence/EV3_CHILE_TIME_PG_PREFLIGHT.json): usuario puentes_test, sin superusuario ni bypass RLS, sin acceso al esquema productivo ni a tablas externas de aplicación.
- [Tres casos PostgreSQL focalizados aprobados tras el ajuste](evidence/EV3_CHILE_TIME_PG_TARGETED.log). No se suman a la suite completa.
- [Chrome, SQLite temporal](evidence/EV3_CHILE_TIME_BROWSER.json): fechas locales visibles en seis vistas, filtros y paginación conservados; cero errores JavaScript. No representa una prueba autenticada de producción.

Las regresiones nuevas comprueban verano/invierno, instantes antes/después de medianoche, fechas de cambio de año, los dos instantes distintos de la hora repetida de otoño, salto de primavera, límites UTC de días de 23/25 horas, rangos abiertos/cerrados, fechas inválidas, paginación con filtros y conservación literal de las tablas consultadas. Las vistas de detalle, notas, reglas, inspecciones y auditoría usan fixtures con cambio de día UTC/Chile. Las pruebas existentes conservan comprobaciones de roles, etapas, generación y deduplicación de alertas.

La primera ejecución completa detectó 3 fallos y 2 errores en las consultas PostgreSQL por el uso de índices negativos de substr, cuyo significado difiere de SQLite. Se corrigió usando length/índices positivos. Se separaron también dos fixtures nuevas para que cada caso PostgreSQL empiece con sus propios datos. La primera corrida no se declara aprobada: [JSON inicial](evidence/EV3_CHILE_TIME_INITIAL_TEST_RESULTS.json), [log inicial](evidence/EV3_CHILE_TIME_INITIAL_TEST_RUN.log). El código final se verificó con una segunda suite completa y sus hashes coinciden con los archivos entregados.

## Archivos modificados

- `README.md`
- `app.py`
- `templates/alert.html`
- `templates/alerts.html`
- `templates/audit.html`
- `templates/dashboard.html`
- `templates/inspection.html`
- `templates/inspection_plans.html`
- `templates/inspections.html`
- `templates/maintenance.html`
- `templates/measurement.html`
- `templates/measurements.html`
- `templates/rules.html`
- `tests/test_cloud.py`
- `tests/test_corrections.py`
- `tools/run_ev3_checks.py`
- `display_time.py`
- `tests/test_chile_time.py`
- `docs/REVISION_FECHAS_CHILE.md`

Evidencia nueva: `docs/evidence/EV3_CHILE_TIME_*` (resultado/log final, resultado/log inicial, preflight, casos PostgreSQL focalizados y navegador). No se sobrescribieron evidencias anteriores de UI, B-11 o paginación.

## Alcance y pendientes

No se cambian motor de alertas, umbrales, permisos, API/IoT, dependencias, esquema ni registros productivos. EV3 conserva bloqueados panel avanzado, mantenimiento y programaciones. Las pruebas PostgreSQL solo reinician sus propias tablas en puentes_test; los casos locales usan SQLite temporal.

La integración y publicación están autorizadas después de esta validación; su comprobación operativa se entrega en el chat. Los históricos sin zona necesitan una procedencia verificable si se pretende ubicarlos en un rango horario; esta revisión no inventa esa información ni los modifica.
