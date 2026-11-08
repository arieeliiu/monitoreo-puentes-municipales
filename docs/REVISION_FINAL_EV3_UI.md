# Revisión final EV3 UI

Rama: `review/ev3-ui`. Correcciones locales preparadas para revisión; push pendiente de aprobación. Sin merge a main ni despliegue.

## Correcciones necesarias

- El API informa `has_more`; cada consulta devuelve como máximo 20 alertas. El cliente continúa los lotes pendientes a intervalos de 1 segundo, con una pausa de 5 segundos después de cada cuatro consultas de la ráfaga. Sin pendientes, ante errores o sin avance del cursor, vuelve a 30 segundos. No hay solicitudes simultáneas; timeout de 8 segundos y pausa en pestaña oculta. No añade tablas, dependencias ni servicios.
- Se mantienen línea base silenciosa al iniciar sesión, cursor por sesión/usuario/etapa, deduplicación y contador de alertas abiertas, independiente de los avisos nuevos.
- Textos futuros: “Consultar proveedor IoT”, “Error al consultar proveedor IoT” y “Actualizar configuración de monitoreo”. La procedencia simulada sigue explícita en los detalles. El resumen de recepción comunica cantidades e incidencias; la identidad y motivo de cada incidencia quedan en auditoría.
- Ninguna descripción histórica se reescribe. La prueba conserva y compara la fila original y confirma su texto literal en Historial de operaciones. Permanecen nombres, fechas, unidades, banderas de simulación y trazabilidad. Las referencias académicas de datos históricos pueden seguir visibles porque forman parte del registro original.
- Revisadas las plantillas y las pantallas Inicio, Mediciones, Alertas, Reglas e Historial. Sin rótulo fijo de demostración ni referencia académica añadida por la interfaz. Se mantienen avisos útiles de disponibilidad, evaluación y origen; no se ocultan problemas de datos. No se modificó el diseño.

## Resultados reales

108 pruebas Python aprobadas, incluidas 12 PostgreSQL; 20 JavaScript aprobadas; 0 fallos, 0 errores y 0 omisiones.

Ejecución: 2026-11-08T16:06:23-03:00 a 2026-11-08T16:15:17-03:00, America/Santiago. La suite completa utiliza SQLite temporal en sus casos locales y exclusivamente el rol/esquema PostgreSQL aislado `puentes_test` en sus casos PostgreSQL. No utiliza credenciales ni datos productivos. El preflight comprobó rol sin superusuario ni bypass RLS, sin acceso al esquema productivo ni a tablas externas de aplicación.

- [Resultado por caso y hashes](evidence/EV3_UI_FINAL_TEST_RESULTS.json).
- [Log completo](evidence/EV3_UI_FINAL_TEST_RUN.log).
- [Verificación del aislamiento, sin credenciales](evidence/EV3_UI_FINAL_PG_PREFLIGHT.json).
- [Chrome: ráfaga y roles](evidence/EV3_UI_FINAL_BROWSER.json): 45 alertas históricas silenciosas, 45 nuevas recuperadas en tres lotes 20/20/5 en 2,37 segundos, sin repetición posterior y sin errores JavaScript. Chrome usa SQLite temporal de laboratorio, separado de las pruebas PostgreSQL.

Los informes y capturas anteriores se conservan como evidencia de aquella ejecución, incluidas sus diez omisiones; este informe documenta la nueva ejecución completa.

## Confirmaciones solicitadas

| Pregunta | Resultado verificado |
|---|---|
| ¿Paginación de 20 sobre PostgreSQL? | Sí: Alertas e Historial 20/20/5, sin duplicados, orden descendente; filtros conservados y límites comprobados. |
| ¿Campana DOM, Inspector y Mantención? | Sí: API autenticada para los tres roles, probado con PostgreSQL y Chrome. |
| ¿Contador abiertas y avisos solo nuevos? | Sí: contador independiente; inicio sin históricos, lotes ascendentes por ID y consulta posterior sin duplicados. |
| ¿Mediciones y Alertas bajo Monitoreo? | Sí: conservan `/measurements`, `/alerts`, enlaces de detalle y permisos; reglas continúan restringidas a DOM. |
| ¿EV3 sin panel avanzado, mantenimiento ni inspecciones programadas? | Sí: se conservan los flags y bloqueos de la etapa `cutoff_2026_11_09`; no se habilitan esos módulos. |
| ¿Respeta RF-2, RF-4, RF-7, HU-02, HU-04, HU-07 y RNF-5? | Sí, dentro del alcance EV3 y con las precisiones siguientes; no equivale a completar módulos futuros ni a aceptación formal municipal. |

## Trazabilidad del alcance

Se contrastaron las fuentes conectadas [Requisitos del sistema](https://docs.google.com/document/d/1AUC_PjiDjPUBGWj9leoANdxqwu_RZh0ntOwNYkh8Vyw/edit) y [HU, casos de uso y criterios](https://docs.google.com/document/d/1ja_t-6dj9pqzESgQG7QOb_pUikvg-5bXB1UMHsMqEyI/edit).

- RF-2 / HU-02: se conserva recepción, validación, almacenamiento, fechas, estados e historial de mediciones y su asociación con alertas. Suite existente sobre PostgreSQL y regresiones de trazabilidad.
- RF-4 / HU-04: evaluación por reglas y condiciones visuales, niveles y vínculos sin modificar umbrales ni convertir avisos en diagnóstico estructural. La validación externa de ingeniería previa a uso real no se declara realizada por esta revisión.
- RF-7 / HU-07: se conserva seguimiento y trazabilidad de alertas e inspecciones; HU-07 está integrada con HU-04/HU-06. El ciclo completo de mantenimiento corresponde a un alcance posterior y sigue deshabilitado en EV3. No se declara RF-7 íntegramente implementado en este corte.
- RNF-5: navegación agrupada, filtros persistentes y textos comprensibles conservan la claridad de operación. Verificación técnica de interfaz y roles; no sustituye una evaluación formal con usuarios municipales.

## Archivos modificados en esta revisión

`app.py`, `static/notifications.js`, `tests/notifications.test.cjs`, `tests/test_cloud.py`, `tests/test_monitoring_ui.py`, `tests/test_final_fixes.py`, `tests/test_iot_update.py`; documentación `README.md`, `docs/ARQUITECTURA.md`, `docs/VERIFICACION.md`, `docs/REVISION_EV3_UI.md`, este informe y los cuatro archivos de evidencia final enlazados arriba.

No se cambió configuración remota, esquema productivo ni datos históricos. Aprobación del usuario requerida antes de push.
