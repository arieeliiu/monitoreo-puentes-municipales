# Revisión de interfaz EV3 para Sol

**Revisión final posterior:** 108 pruebas Python aprobadas, incluidas 12 PostgreSQL; 20 JavaScript aprobadas; 0 fallos, 0 errores y 0 omisiones. [Informe y confirmaciones](REVISION_FINAL_EV3_UI.md). Los resultados anteriores se conservan como historial de su ejecución.

## Estado de entrega

Repositorio local: `C:/Users/westl/Desktop/puentes`, remoto identificado `arieeliiu/monitoreo-puentes-municipales`. Rama `review/ev3-ui`, creada desde main en 405d861. Cambios confirmados para revisión en GitHub por autorización posterior del usuario. Rama remota: https://github.com/arieeliiu/monitoreo-puentes-municipales/tree/review/ev3-ui . No se fusiona con main ni se despliega. vercel.json excluye expresamente review/ev3-ui de los despliegues automáticos, conservando la exclusión previa de review/ev3-b11.

## Cambios

- Monitoreo agrupa Mediciones/Alertas mediante navegación común, sin cambiar URLs ni responsabilidades. Detalles mantienen la pestaña activa. EV2 conserva su navegación anterior.
- Alertas y operaciones: COUNT y LIMIT/OFFSET de 20 registros; anterior/siguiente, página actual, vacío y límites. Orden por fecha/ID descendente. Alertas conserva puente, severidad, estado y rango UTC al paginar.
- Campana para los tres roles que ya consultaban alertas. Contador de Activa/En atención, separado del concepto de no leídas. Consulta autenticada periódica, línea base sin avisos históricos, cursor por sesión/usuario/etapa y aviso con acceso al detalle. No agrega servicios ni dependencias a la aplicación.
- Reglas solo DOM: vigentes separadas del historial consultable. No se cambia evaluación, umbral o creación/desactivación de versiones.
- Mediciones enlazan sus alertas; alertas conservan vínculo con medición/inspección y su seguimiento.
- Se retiró el rótulo fijo de demostración y referencias de versión académica en indicadores de presentación. Se conservan datos, nombres ingresados, banderas internas de simulación, auditoría, errores y disponibilidad. No se renombra contenido histórico para esconder palabras como prueba o mock.

## Validación real

95 Python aprobadas y 10 PostgreSQL omitidas (sin DSN aislado); 16 JavaScript aprobadas. Cero fallos/errores. No se atribuyen a esta ejecución las 98 pruebas/10 JS de B-11 ni se suman repeticiones. Resultado por caso, hashes, omisiones y TAP en `evidence/EV3_UI_TEST_RESULTS.json`, `EV3_UI_TEST_RUN.log` y `EV3_UI_FINAL_JS.tap`.

Chrome headless sobre SQLite temporal: login DOM/Inspector/Mantención, contador inicial sin históricos, generación real de nueva alerta mediante recepción manual local, enlace directo, no repetición, permisos y 390 px sin desbordamiento. Capturas y JSON son de laboratorio, no de la publicación. No se ejecutó carga inicial sobre ninguna base existente ni se consultaron credenciales productivas.

| Vista | Evidencia |
|---|---|
| Alertas, filtro conservado y página 2 | [Captura](evidence/EV3_UI_ALERTAS.png) |
| Medición y alerta asociada | [Captura](evidence/EV3_UI_MEDICION.png) |
| Reglas e historial desplegado | [Captura](evidence/EV3_UI_REGLAS.png) |
| Historial de operaciones, página 2 | [Captura](evidence/EV3_UI_HISTORIAL.png) |
| Campana, nueva alerta y abiertas | [Captura](evidence/EV3_UI_CAMPANA.png) |
| Vista móvil | [Captura](evidence/EV3_UI_MOVIL.png) |

## Reproducir

```powershell
.\.venv\Scripts\python.exe tools/run_ev3_checks.py --output docs/evidence/EV3_UI_TEST_RESULTS.json
node --test tests/frontend.test.cjs tests/cloud-uploads.test.cjs tests/notifications.test.cjs
```

Para navegador: ejecutar `tools/preview_monitoring_ui.py` desde este repositorio y después `node tools/capture_monitoring_ui.cjs`; requiere Chrome y Playwright solo para QA. PLAYWRIGHT_MODULE permite indicar la ruta absoluta del paquete de pruebas ya disponible. El servidor escucha únicamente en 127.0.0.1:5290, crea y elimina su SQLite temporal; detenerlo con Ctrl+C al terminar. No usar la herramienta contra producción. No se añadió Playwright a requirements ni a pyproject.

## Alcance y pendientes

En cutoff_2026_11_09 se conserva Inicio básico y las restricciones de mantenimiento/programación/panel avanzado. Compatibilidad EV2/full cubierta por las regresiones existentes. No se cambió PROJECT_STAGE remoto, esquema, base operativa, datos históricos, integración IoT, reglas ni secretos. No se ejecutó Vercel ni comandos Supabase. Se añadió únicamente la exclusión de despliegue automático para esta rama de revisión en vercel.json.

Revisar PostgreSQL con el rol/esquema aislado antes de publicar; los diez casos omitidos se identifican en el JSON. No se declara validación sobre tablet física ni despliegue. Los avisos son de la sesión visible: no son push con la página cerrada, ni estado persistente de lectura; el cursor se aísla por pestaña y login. Un lote muy grande se entrega en grupos de 20 por consulta. El fallo de actualización se comunica conservando el último contador conocido. Las menciones anteriores a EV2 publicada en README pertenecen al historial; no se verificó la etapa remota indicada por el encargo.

## Archivos para revisar

- `README.md`
- `app.py`
- `docs/ARQUITECTURA.md`
- `docs/CUMPLIMIENTO.md`
- `docs/DISENO.md`
- `docs/REVISION_EV3_UI.md`
- `docs/USABILIDAD.md`
- `docs/VERIFICACION.md`
- `static/app.css`
- `static/notifications.js`
- `templates/alerts.html`
- `templates/audit.html`
- `templates/base.html`
- `templates/macros.html`
- `templates/measurement.html`
- `templates/rules.html`
- `tests/notifications.test.cjs`
- `tests/test_corrections.py`
- `tests/test_ev2.py`
- `tests/test_ev3_stage.py`
- `tests/test_monitoring_ui.py`
- `tools/capture_monitoring_ui.cjs`
- `tools/preview_monitoring_ui.py`
- `tools/run_ev3_checks.py`

- `vercel.json`

Las capturas, JSON y logs nuevos se encuentran en `docs/evidence/EV3_UI_*`. Las evidencias B-11 anteriores permanecen intactas.
