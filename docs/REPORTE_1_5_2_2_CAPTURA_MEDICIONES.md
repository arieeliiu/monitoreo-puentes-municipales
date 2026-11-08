# Reporte 1.5.2.2 — Pruebas de captura de mediciones

## Objetivo y alcance B-11

Verificar que las entradas manuales, API y proveedor simulado mantengan validación, persistencia, identidad relacional, deduplicación y recuperación de errores al habilitar `cutoff_2026_11_09`. Se reutilizan recepción, proveedor y worker existentes; no se cambia su protocolo ni el esquema.

Fecha real: **2026-11-08**, zona America/Santiago. Ejecución completa iniciada `2026-11-08T12:11:07-03:00` y finalizada `2026-11-08T12:18:23-03:00`. El 09/11/2026 identifica el alcance del incremento; no se atribuye esa fecha a las pruebas.

Ambiente: Windows, Python 3.12.14, SQLite 3.53.1, Node.js mediante `node --test`; PostgreSQL/Supabase con usuario restringido `puentes_test` y esquema separado del mismo nombre. Las fixtures SQLite, fotografías y procesos HTTP son temporales. Se limpiaron las variables de conexión/configuración productivas del proceso de pruebas. No se ejecutó DDL, truncado ni prueba funcional sobre producción.

Resultado de la suite completa: **98 pruebas Python y 10 JavaScript aprobadas; 0 fallos, 0 errores y 0 omisiones**. Incluye 12 casos nuevos SQLite de EV3 y un caso adicional PostgreSQL; las regresiones anteriores siguen ejecutándose.

Evidencia principal: [resultado generado por el runner](evidence/EV3_B11_TEST_RESULTS.json), con ID de cada prueba, estado, inicio, duración, resultados JavaScript TAP y SHA256 de las fuentes probadas. El campo `base_commit` identifica el punto de partida; las fuentes de B-11 estaban sin commit durante la ejecución y están identificadas por sus hashes. Los contadores por caso son observados al cerrar su fixture, no estimaciones ni datos publicados.

## Casos ejecutados

| Prueba / evidencia en JSON | Datos de entrada | Resultado esperado | Resultado obtenido y comprobado | Estado |
|---|---|---|---|---|
| `tests.test_ev3_stage.Ev3StageTests.test_capture_invalid_missing_no_rule_and_api_dedup_traceability` | API: S1, 5 m/s², válido, ID ev3-api; repetición; inválido 500; no disponible sin valor; -1, NaN, mm/s, fecha 2099 y puente incompatible. S2 sin regla. | Persistir solo entradas admitidas; duplicado/error 400; no alertar inválidos, ausentes o sin regla; conservar trazabilidad. | API válida 201; duplicada 400 sin nueva fila. Quedan 4 mediciones y 1 alerta enlazada al puente/sensor/medición/regla. Los cinco datos incorrectos no agregan filas. S2 registra Sin regla aplicable. | Aprobado |
| `tests.test_ev3_stage.Ev3StageTests.test_http_provider_two_bridges_dedup` | HTTP local real: P1/S1, 0,5 m/s²; P2/S3, 9,771°, referencia 10°. Consultar dos veces. | Dos mediciones y dos alertas; cambio 0,229°; segunda consulta sin duplicados. | Persisten 2 lecturas y 2 alertas: P1 Atención, P2 Alerta; referencia 10 y variación 0,229. Segunda consulta no aumenta contadores. | Aprobado |
| `tests.test_ev3_stage.Ev3StageTests.test_provider_inconsistent_records_and_savepoints` | Lote HTTP de 2 registros válidos y 6 inconsistentes: puente/tipo incorrectos, identidad ausente y repetición con tipo incompatible. | Mantener válidos por savepoint y rechazar inconsistentes con evidencia de auditoría, sin contaminar otro puente. | 2 lecturas persistidas tras repetir consulta. Auditoría conserva identificadores y motivo de los rechazos; no hay reglas de este fixture que generen alertas. | Aprobado |
| `tests.test_ev3_stage.Ev3StageTests.test_cron_ev3_evaluates_both_bridges_and_deduplicates` | POST interno sin token y con Bearer de prueba; lote controlado P1/S1 y P2/S3, valor 6 y umbral configurable 5; repetir. | 401 sin token; primer ciclo recibe 2; segundo registra 2 duplicados; alerta por puente. | 401; respuesta inicial received=2, duplicates=0, errors=[]; repetición received=0, duplicates=2, errors=[]; 2 alertas Atención. | Aprobado |
| `tests.test_final_fixes.FinalFixTests.test_real_provider_and_periodic_worker_restart_recovery` y `tests.test_project_stage.ProjectStageTests.test_cutoff_real_provider_worker_retries_deduplicates_without_alerts` | Proveedor y worker como procesos reales; intervalo 1 s; arranque desconectado, conexión, desconexión y reinicio del proveedor. | Auditar fallos, recuperar sin reiniciar worker, deduplicar; full evalúa y EV2 no evalúa. | Ambas pruebas aprobadas: 4 lecturas iniciales y 8 tras reinicio; web responde 200; consulta manual no duplica. Full termina con 8 alertas; EV2 con 0 y evaluación pendiente. | Aprobado |
| `tests.test_cloud.PostgresTests.test_postgres_ev3_cutoff_rules_and_cron` | Cron EV3, token válido/ausente, 2 puentes y repetición sobre PostgreSQL aislado. | Igual recepción y deduplicación que SQLite; reglas y alertas accesibles sin módulos futuros. | 2 mediciones y 2 alertas; repetición sin nuevas filas. Reglas/detalle 200; mantenimiento/programación 404; inicio básico. | Aprobado |

## Contadores reales de los fixtures EV3

| Caso EV3 (sufijo) | Mediciones | Inspecciones | Versiones de regla | Alertas | Notas |
|---|---:|---:|---:|---:|---:|
| `test_capture_invalid_missing_no_rule_and_api_dedup_traceability` | 4 | 0 | 1 | 1 | 0 |
| `test_http_provider_two_bridges_dedup` | 2 | 0 | 18 | 2 | 0 |
| `test_provider_inconsistent_records_and_savepoints` | 2 | 0 | 0 | 0 | 0 |
| `test_cron_ev3_evaluates_both_bridges_and_deduplicates` | 2 | 0 | 2 | 2 | 0 |

El JSON incluye `evaluations` y `alert_sources` con los IDs de puente, fuente y versión de regla de cada alerta. Los sensores adicionales que aparecen en fixtures son datos de prueba aislados; no se agregaron sensores ni se alteraron registros del piloto.

## Regresiones relacionadas

También pasan permisos DOM/Inspector/Mantención, CSRF, formularios reales puente → componente → sensor, filtros combinados y estado vacío, unidades EV2, fecha/hora, fotografías privadas, cargas firmadas y preservación de datos/migraciones en fixtures. Los IDs y resultados de cada caso están en el mismo JSON.

## Reproducción

Desde la raíz, ejecutar `.\.venv\Scripts\python.exe tools/run_ev3_checks.py`. Para incluir PostgreSQL debe existir `PUENTES_TEST_DATABASE_URL` con el rol restringido `puentes_test`; nunca usar la conexión productiva. Sin esa variable el runner registra omisiones PostgreSQL: esa ejecución no equivale al resultado completo de este reporte. El runner ejecuta `unittest discover` y `node --test --test-reporter=tap tests/frontend.test.cjs tests/cloud-uploads.test.cjs` y escribe evidencia fechada.

## Limitaciones y observaciones

- El proveedor es simulado; no se prueba hardware ni conectividad de sensores reales.
- EV3 prueba el endpoint utilizado por Cron con un lote controlado y HTTP del proveedor con servidor local real. El worker como proceso real se ejercita en full y EV2; no se ejecutó el scheduler remoto de producción para esta entrega.
- Se verificó PostgreSQL aislado, no un despliegue nuevo en Vercel. Las pruebas de Storage con dobles de prueba no acreditan una nueva carga real en producción.
- La primera ejecución completa quedó interrumpida antes de producir el archivo de resultados. Se repitió íntegramente en un proceso con registro persistente; este reporte usa solo esa ejecución final. Los ensayos iniciales de las pruebas nuevas corrigieron colisiones entre fixtures y un umbral de prueba fuera de orden, sin modificar el motor por esos fallos.
- No se cambiaron credenciales, datos históricos, umbrales productivos, esquema ni configuración de publicación. B-01, B-02 y B-03 quedan fuera de este trabajo.
