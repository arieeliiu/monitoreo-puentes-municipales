# Reporte 1.5.2.3 — Pruebas de reglas de alerta

## Objetivo y alcance B-11 / EDT 1.4.4

Habilitar y comprobar configuración DOM, versionamiento, evaluación automática, trazabilidad, consulta y seguimiento de alertas en el corte `cutoff_2026_11_09`, conservando EV2 y full. El motor, las reglas EV2 y los estados de seguimiento ya existían en full; se agrega una matriz de funciones por etapa y se eliminan las dependencias de presentación/consulta de mantenimiento y programación en el nuevo incremento. No se rediseña el motor ni la base.

Fecha real: **2026-11-08**, zona America/Santiago. Ejecución completa iniciada `2026-11-08T12:11:07-03:00` y finalizada `2026-11-08T12:18:23-03:00`. El 09/11/2026 identifica el alcance del incremento; no se atribuye esa fecha a las pruebas.

Ambiente: Windows, Python 3.12.14, SQLite 3.53.1, Node.js mediante `node --test`; PostgreSQL/Supabase con usuario restringido `puentes_test` y esquema separado del mismo nombre. Las fixtures SQLite, fotografías y procesos HTTP son temporales. Se limpiaron las variables de conexión/configuración productivas del proceso de pruebas. No se ejecutó DDL, truncado ni prueba funcional sobre producción.

Resultado de la suite completa: **98 pruebas Python y 10 JavaScript aprobadas; 0 fallos, 0 errores y 0 omisiones**. Incluye 12 casos nuevos SQLite de EV3 y un caso adicional PostgreSQL; las regresiones anteriores siguen ejecutándose.

Evidencia principal: [resultado generado por el runner](evidence/EV3_B11_TEST_RESULTS.json), con ID de cada prueba, estado, inicio, duración, resultados JavaScript TAP y SHA256 de las fuentes probadas. El campo `base_commit` identifica el punto de partida; las fuentes de B-11 estaban sin commit durante la ejecución y están identificadas por sus hashes. Los contadores por caso son observados al cerrar su fixture, no estimaciones ni datos publicados.

## Casos ejecutados

| Prueba / evidencia en JSON | Datos de entrada | Resultado esperado | Resultado obtenido y comprobado | Estado |
|---|---|---|---|---|
| `tests.test_ev3_stage.Ev3StageTests.test_stage_configuration_navigation_permissions_and_blocked_writes` | Tres roles; etapa explícita/entorno; inicio y rutas; GET/POST futuros con y sin CSRF. | DOM administra reglas; demás roles 403. Todos consultan alertas. Mantenimiento/programación 404 sin escrituras. | Navegación y rutas coinciden con alcance EV3. DOM crea regla; otros roles no. Bloqueos conservan todas las filas del fixture. | Aprobado |
| `tests.test_ev3_stage.Ev3StageTests.test_numeric_boundaries_engine_reused` | Vibración: 0,499; 0,5; 0,999; 1; 2,499; 2,5; 3 m/s². Inclinación: 0,114 y ±0,115/0,229/0,458°, referencia 0. | Comparación inclusiva y una alerta de máxima severidad; simetría de inclinación. | 14 lecturas aceptadas. Umbrales exactos activan Atención, Alerta o Crítico; 12 alertas, ninguna para los dos valores inferiores. | Aprobado |
| `tests.test_ev3_stage.Ev3StageTests.test_reference_snapshot_engine_reused` | Referencia 10°; 10,115; 9,771; 10,458; 9,542; cambiar referencia a 11; después sin referencia; referencia NaN. | Calcular abs(lectura-referencia), preservar snapshot; sin referencia no alertar; NaN rechazado. | 5 mediciones y 4 alertas; snapshot inicial (10,115; 10; 0,115) inmutable. Lectura sin referencia queda no evaluable, sin nueva alerta. | Aprobado |
| `tests.test_ev3_stage.Ev3StageTests.test_visual_engine_reused` | Condición visual Baja, Media, Alta, Crítica; intento Mala histórica. | Coincidencia con reglas configuradas: ninguna/Atención/Alerta/Crítico; rechazar categoría antigua nueva. | 4 inspecciones y 3 alertas vinculadas a su inspección y regla. Mala no crea inspección nueva. | Aprobado |
| `tests.test_ev3_stage.Ev3StageTests.test_configurable_thresholds_versions_disable_and_invalid_rules` | Umbrales personalizados 7/11/19 m/s²; editar Atención a 8; lecturas 7,8,11,19; desactivar Crítico; lectura 30. Intentos -1, NaN, inf, texto y Atención=12. | Usar configuración, versionar, conservar alertas previas, ignorar desactivada, rechazar reglas inválidas. | 6 lecturas, 5 alertas, 4 versiones. Alerta antigua conserva fila y rule_id; regla anterior inactiva sin cambiar su contenido. Tras desactivar Crítico, 30 produce Alerta. Intentos inválidos no agregan reglas. | Aprobado |
| `tests.test_ev3_stage.Ev3StageTests.test_alert_followup_roles_and_csrf` | CSRF incorrecto; nota Inspector; Inspector intenta resolver; Mantención intenta anotar; DOM En atención y Resuelta con justificación. | 400 CSRF; Inspector solo observaciones; Mantención consulta; DOM cambia estado explícitamente. | 400 y 403 según rol; 3 notas autorizadas; estado final Resuelta. Seguimiento no muestra ni requiere mantenimiento. | Aprobado |
| `tests.test_ev3_stage.Ev3StageTests.test_forged_plan_rejected_before_inspection_and_photos` | plan_id manipulado y archivo PNG desde Inspector, con una programación creada solo en fixture full. | Rechazo previo a escrituras/fotos; no completar programación. | Todas las filas y carpeta de fotografías permanecen iguales. | Aprobado |
| `tests.test_ev3_stage.Ev3StageTests.test_switching_three_modes_preserves_rows_and_has_no_future_queries` | Misma base poblada al iniciar sucesivamente EV2, EV3 y full; trazado SELECT de inicio, alerta e inspecciones. | Conservar datos; EV2 bloquea alertas; EV3 no depende de tasks/inspection_plans; full disponible. | Filas idénticas al alternar. Alerta EV2 404 y EV3/full 200. EV3 no realiza SELECT de tareas ni programaciones en esas vistas. | Aprobado |
| `tests.test_cloud.PostgresTests.test_postgres_ev3_cutoff_rules_and_cron` | Mismo Cron EV3 con umbrales 5 y valores 6 en dos puentes sobre PostgreSQL aislado. | Evaluación y deduplicación equivalentes a SQLite. | 2 alertas Atención, una por puente; sin duplicados; reglas/detalle 200; mantenimiento/programación 404. | Aprobado |

## Contadores reales de los fixtures EV3

| Caso EV3 (sufijo) | Mediciones | Inspecciones | Versiones de regla | Alertas | Notas |
|---|---:|---:|---:|---:|---:|
| `test_stage_configuration_navigation_permissions_and_blocked_writes` | 1 | 0 | 19 | 1 | 0 |
| `test_numeric_boundaries_engine_reused` | 14 | 0 | 18 | 12 | 0 |
| `test_reference_snapshot_engine_reused` | 5 | 0 | 18 | 4 | 0 |
| `test_visual_engine_reused` | 0 | 4 | 18 | 3 | 0 |
| `test_configurable_thresholds_versions_disable_and_invalid_rules` | 6 | 0 | 4 | 5 | 0 |
| `test_alert_followup_roles_and_csrf` | 1 | 0 | 1 | 1 | 3 |
| `test_forged_plan_rejected_before_inspection_and_photos` | 0 | 0 | 0 | 0 | 0 |
| `test_switching_three_modes_preserves_rows_and_has_no_future_queries` | 1 | 0 | 18 | 1 | 0 |

Los conteos corresponden a fixtures independientes. El cambio de una regla conserva su versión original y el vínculo de las alertas previas; solo cambia a inactiva para impedir su uso futuro. No hay reevaluación masiva de históricos.

## Verificación adicional de interfaz

Revisión manual real de DOM en `http://127.0.0.1:5012`, SQLite temporal separada de la suite: inicio básico, menú EV3, formulario de reglas y configuraciones vigentes/históricas, alertas de origen numérico y visual, detalle con fuente, notas y estados. Se observó ausencia de mantenimiento y programación. Esta revisión no cuenta como otro test automatizado ni prueba un cambio en Vercel.

- [Reglas en navegador local](evidence/EV3_B11_REGLAS.png).
- [Alerta y seguimiento sin mantenimiento](evidence/EV3_B11_ALERTA.png).
- [Observación del navegador y fecha UTC real](evidence/EV3_B11_NAVEGADOR.txt).

## Compatibilidad y seguridad

| Modo | Inicio | Reglas/evaluación/alertas | Mantenimiento y programación |
|---|---|---|---|
| `cutoff_2026_10_26` (predeterminado) | Básico original | Rutas 404; evaluación pendiente, históricos conservados | Ocultos y bloqueados |
| `cutoff_2026_11_09` | Básico | Habilitados con permisos/versionamiento existentes | Ocultos, bloqueados y sin dependencia de consulta en vistas verificadas |
| `full` | Panel completo original | Habilitados como antes | Conservados |

Permisos existentes: DOM crea/versiona/desactiva reglas y decide el estado; Inspector añade notas e inspecciones; Mantención consulta alertas sin modificar su seguimiento. La suite conserva autenticación, CSRF y protección de fotografías. Ninguna alerta constituye un diagnóstico automático de seguridad estructural; los parámetros y unidades siguen siendo los asumidos y configurables de EV2.

## Reproducción y evidencia

Ejecutar `.\.venv\Scripts\python.exe tools/run_ev3_checks.py` desde la raíz; configurar únicamente el DSN restringido `PUENTES_TEST_DATABASE_URL` para reproducir PostgreSQL. El JSON enlazado permite buscar el ID exacto de cada caso, su estado y sus fuentes/contadores. La suite mantiene regresiones de full y EV2 sin contarlas por duplicado mediante herencia.

## Limitaciones y cierre

- Resultado técnico de B-11 satisfactorio en entornos de prueba. No equivale a aceptación municipal, validación de ingeniería ni prueba de hardware.
- No se hizo push, despliegue, migración productiva ni cambio de variables de Vercel. No se alteraron fotografías/históricos productivos ni B-01/B-02/B-03.
- Para publicar falta aprobación explícita del usuario, enviar el commit y activar `PROJECT_STAGE=cutoff_2026_11_09` en el entorno autorizado, desplegar y verificar allí los roles y la siguiente captura Cron. Esa activación no debe reevaluar automáticamente las lecturas históricas pendientes.
