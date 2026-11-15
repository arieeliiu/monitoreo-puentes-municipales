# Índice de entrega técnica individual de Ariel — EV3

Estado: **preparado para revisión**, PR #1 en borrador, rama `feature/ev3-cierre-tecnico`. No equivale a entrega formal, aprobación del equipo/profesora ni publicación. No se atribuyen revisiones a Christian o Alex como realizadas.

| Trabajo técnico preparado | Código / documentación | Estado |
|---|---|---|
| B-11 / 1.4.4: reglas DOM configurables, versiones, generación y seguimiento/cierre de alertas; captura existente | `app.py`, `templates/rules.html`, `templates/alerts.html`, `templates/alert.html`; informes [1.5.2.2 Captura](REPORTE_1_5_2_2_CAPTURA_MEDICIONES.md) y [1.5.2.3 Reglas](REPORTE_1_5_2_3_REGLAS_ALERTA.md) | Recuperación técnica preparada; revisión y entrega formal pendientes. Corte 09/11 sin panel avanzado/mantenimiento. |
| D7: identificadores PM coherentes y procedencia técnica conservada | `reference_data.py`, `cloud_provider.py`, `mock_provider.py`, `demo_locations.py`, seed de `app.py`, mockups; `reference_migration.py` y `tools/rename_reference_identifiers.py`; [plan D7](MIGRACION_REFERENCIAS_D7.md) | Código y pruebas preparados; no se alteraron datos productivos ni identificadores históricos automáticamente. |
| B-14 / 1.4.5: panel existente, últimas lecturas, estados, alertas y pendientes por rol | `app.py`, `templates/dashboard.html`; [informe 1.5.2.4](REPORTE_1_5_2_4_PANEL_MONITOREO.md) | Preparado en `cutoff_2026_11_28`; revisión compartida pendiente. |
| B-14 / 1.4.6: creación, edición, asignación y seguimiento de actividades existentes | `app.py`, `templates/maintenance.html`; [informe 1.5.2.5](REPORTE_1_5_2_5_PLANIFICACION_MANTENIMIENTO.md) | Verificado sin reconstrucción; completar no resuelve la alerta. Revisión compartida pendiente. |

## Evidencias y reproducción

Los cuatro informes identifican la ejecución vigente, sus fechas reales y el código probado. [Resumen y trazabilidad](CIERRE_TECNICO_EV3.md), [verificación](VERIFICACION.md), [auditoría de 61 hashes de la ejecución histórica](evidence/EV3_PR1_HISTORICAL_SOURCE_AUDIT.json). Los JSON/logs anteriores y las capturas de navegador en `docs/evidence/EV3_CIERRE*` se conservan como históricos; no son ejecuciones nuevas.

Runner: `python tools/run_ev3_checks.py --output docs/evidence/EV3_PR1_FINAL_TEST_RESULTS.json`. Requiere que el archivo de salida no exista; para repetir usar otro nombre. PostgreSQL únicamente con `PUENTES_TEST_DATABASE_URL` del rol/esquema restringido `puentes_test`; sin DSN quedan casos omitidos y no se puede atribuir el resultado completo. Ejecuta unittest y las tres suites JavaScript. Las regresiones funcionales están en `tests/test_ev3_stage.py`, `tests/test_ev3_closure.py`, `tests/test_cloud.py` y suites previas; `tests/test_evidence_provenance.py` comprueba atribución de la evidencia.

Resultado vigente: **135 pruebas Python (incluidas 18 PostgreSQL aisladas) y 20 JavaScript aprobadas; 0 fallos, 0 errores y 0 omisiones**, ejecución real 2026-11-14T22:04:07-03:00 a 2026-11-14T22:16:51-03:00. Código probado `f17bb26a9b911b95c732a1fa1e9038cb7ccdd0d8`, base de comparación `e191aed818b8ee94296594f633ed2afe8111ec3d`. [JSON final](evidence/EV3_PR1_FINAL_TEST_RESULTS.json), [log](evidence/EV3_PR1_FINAL_TEST_RUN.log). Las tres regresiones nuevas de esta revisión son de trazabilidad; no agregan funcionalidad del sistema.

## Publicación, límites y acciones pendientes

Publicación **no ejecutada**. El [procedimiento de publicación EV3](PLAN_PUBLICACION_EV3.md) cubre inventario de solo lectura, detección D7, respaldo PostgreSQL y objetos Storage, pausa de escritores/captura, planificación y aplicación autorizada, etapa 28/11, despliegue coordinado, verificación y recuperación. No se integró a main ni se modificaron producción, credenciales, Cron o Storage en este cierre. La rama mantiene deshabilitado su despliegue automático.

Pendientes manuales: revisión técnica del PR por ChatGPT/equipo; revisión B-11 de Christian; parte frontend/procesos y entrega compartida B-14 Ariel/Christian, revisión Alex; autorización operativa, inventario/respaldo restaurable y publicación con pruebas posteriores reales. Son responsabilidades por realizar, no aprobaciones supuestas. Si el inventario no es canónico, faltan respaldos o no se pueden detener escritores, la operación debe detenerse para resolverlo.

Hitos conservados: recuperación técnica B-11 para entrega formal antes del **15/11/2026**, término planificado de 1.4.5/1.4.6 el **24/11**, corte de estado **28/11**, entrega EV3 **30/11**. Las fechas originales de la EDT y B-01/B-02/B-03 permanecen intactas. No se declara hito ni aceptación formal a partir de pruebas. Hardware real, nuevas integraciones, predicción, piloto operacional, marcha blanca y UAT están fuera de este trabajo.
