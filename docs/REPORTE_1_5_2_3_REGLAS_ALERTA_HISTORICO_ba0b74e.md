# Reporte 1.5.2.3 — Pruebas de reglas de alerta

## Verificación final del PR #1

Alcance: B-11 / reglas y alertas. Configuración y versiones DOM, límites inclusivos, severidad máxima, validaciones, referencia de inclinación, estados/notas y resolución explícita, permisos y CSRF. El corte 09/11 conserva reglas y alertas sin panel avanzado ni mantenimiento. Los IDs de casos de las tablas siguientes también están aprobados en el JSON final; los resultados anteriores conservan sus fechas y contadores históricos.

Ejecución real de `2026-11-14T22:04:07-03:00` a `2026-11-14T22:16:51-03:00`, zona America/Santiago. **135 pruebas Python (incluidas 18 PostgreSQL aisladas) y 20 JavaScript aprobadas; 0 fallos, 0 errores y 0 omisiones**. Entorno: Windows, Python 3.12.14, SQLite 3.53.1, Node.js mediante las tres suites `node --test`; PostgreSQL con rol/esquema aislado `puentes_test`. No se usó producción. [JSON de la ejecución final](evidence/EV3_PR1_FINAL_TEST_RESULTS.json); [log completo](evidence/EV3_PR1_FINAL_TEST_RUN.log).

Versión probada: **`f17bb26a9b911b95c732a1fa1e9038cb7ccdd0d8`**, rama `feature/ev3-cierre-tecnico`, worktree limpio al inicio. Base de comparación: `origin/main` / `e191aed818b8ee94296594f633ed2afe8111ec3d`; la base no es la versión ejecutada. Los 62 archivos del manifiesto corresponden a los blobs Git de HEAD y sus SHA-256 permanecieron iguales hasta finalizar. Durante la ejecución solo se redactó documentación fuera de ese manifiesto; `finished_revision` deja constancia del estado final. Los commits documentales posteriores no se presentan como ejecuciones adicionales.

La evidencia anterior `EV3_CIERRE_TECNICO_TEST_RESULTS.json` se conserva sin cambios como histórica (132 Python + 20 JS). Sus **61/61 SHA-256** coincidieron con el worktree limpio del PR en `229e224` antes de estas correcciones: [cotejo fechado, por archivo](evidence/EV3_PR1_HISTORICAL_SOURCE_AUDIT.json). La ejecución anterior ocurrió sobre cambios locales con HEAD/base `e191aed`; no se atribuye retrospectivamente a `229e224`, creado después. Las capturas y seis comprobaciones de navegador `EV3_CIERRE_BROWSER.json` también son históricas; no se repitieron en esta revisión documental/de trazabilidad.

Etapas vigentes: `cutoff_2026_10_26`: funciones básicas y captura sin evaluación de alertas; `cutoff_2026_11_09`: captura/reglas/alertas con inicio básico y sin mantenimiento; `cutoff_2026_11_28`: añade panel avanzado y mantenimiento, sin programación; `full`: todas las funciones existentes, incluidas inspecciones programadas.

Repetición desde la raíz: `python tools/run_ev3_checks.py --output docs/evidence/EV3_PR1_FINAL_TEST_RESULTS.json`, solo si esa salida no existe. Para otra ejecución usar un nombre nuevo. El runner se niega a sobrescribir evidencia; PostgreSQL requiere `PUENTES_TEST_DATABASE_URL` del rol restringido de pruebas. Sin DSN se registran omisiones, no el resultado completo aquí acreditado.

Estado: preparado técnicamente para revisión; sin aprobación ni entrega formal atribuida al equipo. Publicación y eventual D7 productiva **no ejecutadas**. [Procedimiento operativo](PLAN_PUBLICACION_EV3.md); [índice Ariel](ENTREGA_ARIEL_EV3.md).

### Antecedentes conservados

Las secciones siguientes, incluidas sus tablas y evidencia de navegador, corresponden a ejecuciones anteriores. No se suman a esta ejecución ni se cambian sus fechas.

## Cierre técnico EV3 — revisión del 2026-11-14

Objetivo: recuperar B-11/EDT 1.4.4 con el motor y seguimiento ya implementados. No se reconstruyó el motor. La evidencia histórica siguiente se conserva; esta sección registra únicamente las verificaciones nuevas.

Fecha real de ejecución: **2026-11-14**, America/Santiago; inicio `2026-11-14T21:35:53-03:00`, término `2026-11-14T21:48:52-03:00`. El nombre del corte 28/11/2026 describe alcance, no la fecha de estas pruebas ni un hito declarado cumplido.

Ambiente: Windows, Python 3.12.14, SQLite 3.53.1, Node.js y PostgreSQL remoto con usuario y esquema restringidos `puentes_test`. Las fixtures y fotos son temporales. El runner elimina variables productivas y solo admite un DSN de pruebas restringido. No se conectó a datos productivos ni se modificó Vercel, Cron, Storage o credenciales.

Suite final completa: **132 pruebas Python (incluidas 18 PostgreSQL aisladas) y 20 JavaScript aprobadas; 0 fallos, 0 errores y 0 omisiones**. Son 12 regresiones SQLite nuevas y 3 PostgreSQL nuevas, además de la suite previa; no se suman ensayos ni se duplican pruebas heredadas. [JSON de resultados por caso, fechas, duración, contadores y SHA256](evidence/EV3_CIERRE_TECNICO_TEST_RESULTS.json); [log íntegro](evidence/EV3_CIERRE_TECNICO_TEST_RUN.log).

| Caso / ID en JSON | Datos utilizados | Resultado esperado | Resultado obtenido | Estado |
|---|---|---|---|---|
| `tests.test_ev3_stage.Ev3StageTests.test_configurable_thresholds_versions_disable_and_invalid_rules` | Umbrales 7/11/19, Atención cambia a 8, desactivar Crítico, valor 30; intentos no finitos/negativos/desordenados. | Usar parámetros, versionar sin alterar alerta previa, ignorar versión inactiva y rechazar inválidos. | Cuatro versiones, seis lecturas y cinco alertas; el 30 termina en Alerta después de desactivar Crítico; histórico vinculado a regla original. | Aprobado |
| `tests.test_ev3_stage.Ev3StageTests.test_numeric_boundaries_engine_reused` | Vibración 0,499/0,5/0,999/1/2,499/2,5/3; inclinación 0,114 y ±0,115/0,229/0,458. | Límites inclusivos y una sola máxima severidad. | 14 lecturas y 12 alertas con Atención, Alerta y Crítico correctos. | Aprobado |
| `tests.test_ev3_stage.Ev3StageTests.test_reference_snapshot_engine_reused` | Referencia 10°; 10,115/9,771/10,458/9,542; cambio de referencia y ausencia de referencia. | Guardar referencia/variación; abs(lectura-referencia); no reevaluar históricos ni alertar sin referencia. | Cinco mediciones y cuatro alertas; snapshot (10,115;10;0,115) conservado y ausencia no evaluable. | Aprobado |
| `tests.test_ev3_stage.Ev3StageTests.test_visual_engine_reused` | Baja/Media/Alta/Crítica y rechazo de Mala como categoría nueva. | Evaluar coincidencia exacta según configuración. | Cuatro inspecciones y tres alertas, vinculadas a inspección y versión de regla. | Aprobado |
| `tests.test_ev3_stage.Ev3StageTests.test_alert_followup_roles_and_csrf` | CSRF incorrecto; notas Inspector; intentos de cierre Inspector y escritura Mantención; DOM cambia estados. | Respetar CSRF/roles y cierre explícito. | 400/403 esperados, tres notas autorizadas y cierre Resuelta solo por DOM. | Aprobado |
| `tests.test_ev3_closure.ClosureStageTests.test_historical_stages_and_four_mode_switch_preserve_rows` | Misma base poblada: EV2, corte 09/11, corte 28/11 y full. | Conservar filas y alcance por etapa. | Corte 09/11 conserva reglas/alertas sin panel avanzado/mantenimiento; 28/11 habilita esos dos módulos sin programación; full y EV2 conservan su alcance. | Aprobado |

El corte `cutoff_2026_11_09` permanece independiente: panel avanzado y mantenimiento no se habilitan en él. Las reglas siguen configurables por DOM, versionadas y trazables. Las alertas requieren revisión y no constituyen un diagnóstico de seguridad estructural.

La verificación es técnica con datos de referencia y proveedores simulados. No acredita hardware, interoperabilidad nueva, diagnóstico estructural, piloto operacional, marcha blanca, capacitación ni UAT municipal. No se publicaron estos cambios. Revisión del equipo, autorización de migración D7/entorno, publicación y prueba posterior quedan pendientes. Las etapas históricas y sus registros se conservan; no hay reevaluación retroactiva.

Reproducción desde la raíz: ejecutar `python tools/run_ev3_checks.py` con el intérprete del entorno y, para PostgreSQL, solo `PUENTES_TEST_DATABASE_URL` del rol restringido. Sin el DSN se registran omisiones y no se puede atribuir el resultado completo de este reporte. El runner ejecuta unittest y las tres suites Node, y guarda un JSON nuevo sin sobrescribir los informes históricos B-11.

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
