# Reporte 1.5.2.3: Reglas de Alerta

## Resumen

Se probó B-11: módulo 1.4.4. **147 Python (incluidas 20 PostgreSQL aisladas) y 20 JavaScript aprobadas; cero fallos, errores u omisiones**. Ejecución real: 15/11/2026 15:49:06 a 15/11/2026 16:04:02 (America/Santiago). Código probado: `e71352105fd1f5a3d109f273150c22290b6cea1b`. [JSON por caso](evidence/EV3_CHRISTIAN_TEST_RESULTS.json) y [log](evidence/EV3_CHRISTIAN_TEST_RUN.log).

Limitación principal: proveedor de referencia y entornos aislados; no es aceptación municipal ni verificación de un despliegue nuevo.

## Objetivo

Verificar reglas configurables/versionadas, evaluación numérica y visual, seguimiento y cierre explícito de alertas sin columnas de simulación; conservar permisos, CSRF y corte 09/11.

## Fecha y ambiente

Fecha real: **15/11/2026**; intervalo 15/11/2026 15:49:06 a 15/11/2026 16:04:02 (America/Santiago). Windows, Python 3.12.14, SQLite 3.53.1, Node.js con tres suites `node --test`; PostgreSQL remoto con usuario/esquema restringidos `puentes_test`. Fotos y HTTP/worker locales temporales. El runner limpia variables productivas. No se usó la base publicada ni se modificó Vercel/Storage.

## Casos, datos y resultados

| Caso verificable en JSON | Datos utilizados | Resultado esperado | Resultado obtenido | Estado |
|---|---|---|---|---|
| `tests.test_ev3_stage.Ev3StageTests.test_configurable_thresholds_versions_disable_and_invalid_rules` | Niveles 7/11/19; cambio Atención a 8; desactivar Crítico; -1/NaN/inf/orden incorrecto. | Versionar, usar regla activa, preservar versiones anteriores y rechazar inválidos. | 4 versiones, 6 lecturas y 5 alertas; tras desactivar Crítico, 30 produce Alerta. | Aprobado |
| `tests.test_ev3_stage.Ev3StageTests.test_numeric_boundaries_engine_reused` | Vibración 0,499 a 3; inclinación ±0,115/0,229/0,458 y valor inferior. | Límites inclusivos, simetría y una sola severidad máxima. | 14 mediciones y 12 alertas, con niveles esperados. | Aprobado |
| `tests.test_ev3_stage.Ev3StageTests.test_visual_engine_reused` | Baja, Media, Alta y Crítica; intento de nueva categoría Mala. | Regla visual exacta, vínculo a inspección y rechazo de categoría histórica nueva. | 4 inspecciones y 3 alertas; Mala rechazada como entrada nueva. | Aprobado |
| `tests.test_ev3_stage.Ev3StageTests.test_alert_followup_roles_and_csrf` | DOM cambia estados; Inspector añade nota e intenta cierre; Mantención intenta escribir; CSRF inválido. | Cierre solo DOM con justificación y permisos/CSRF conservados. | 400/403 esperados; 3 notas autorizadas; DOM deja alerta Resuelta. | Aprobado |
| `tests.test_ev3_closure.ClosureStageTests.test_historical_stages_and_four_mode_switch_preserve_rows` | Misma base poblada al alternar EV2, 09/11, 28/11 y full. | No alterar filas ni habilitar funciones futuras en etapas anteriores. | Filas idénticas; 09/11 sin panel/mantenimiento; programación solo full. | Aprobado |

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

[Informe anterior íntegro, sin reescribir sus resultados](REPORTE_1_5_2_3_REGLAS_ALERTA_HISTORICO_ba0b74e.md). Las capturas de su sección histórica conservan su contexto; no son capturas nuevas del código revisado.
