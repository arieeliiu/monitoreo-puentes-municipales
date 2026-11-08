# Verificación del corte y modo completo

## Resultado de revisión de interfaz EV3

Ejecutado localmente el 08/11/2026: 105 casos Python descubiertos; 95 aprobados, 10 PostgreSQL omitidos por falta de DSN de pruebas aislado, 0 fallos y 0 errores. Las tres suites JavaScript suman 16 aprobadas, 0 fallos. Las suites JS se repitieron después del ajuste de ciclo de vida de navegación; no se cuentan dos veces. [JSON con casos y hashes](evidence/EV3_UI_TEST_RESULTS.json), [TAP final](evidence/EV3_UI_FINAL_JS.tap), [log completo](evidence/EV3_UI_TEST_RUN.log).

Siete regresiones nuevas de servidor y seis de notificaciones cubren 20/20/5 filas, LIMIT/OFFSET real, filtros/fechas persistentes, estados vacíos/límites, roles, sesiones distintas, línea base, lotes de avisos, una sola consulta agregada cuando no hay altas, ID de sesión, rechazo de parámetros, trazabilidad, versiones y conservación de filas. Se actualizaron únicamente las expectativas previas de menú, rótulo de demostración y SVG del icono de campana; el bloqueo del panel avanzado se conserva y comprueba por contenido y consultas.

Chrome verificó DOM/Inspector/Mantención, navegación y paginación, alerta nueva con enlace y contador, ausencia de repetición y viewport de 390 px sin desbordamiento global. [Resultados del navegador](evidence/EV3_UI_BROWSER_RESULTS.json). Bases SQLite temporales; no se probó ni escribió en producción. PostgreSQL real, dispositivos físicos y publicación quedan fuera de esta comprobación. [Reporte completo](REVISION_EV3_UI.md).

## EV3 / B-11 — resultado vigente del 2026-11-08

Suite completa ejecutada de `2026-11-08T12:11:07-03:00` a `2026-11-08T12:18:23-03:00` (America/Santiago): **98 pruebas Python y 10 JavaScript aprobadas; 0 fallos, 0 errores y 0 omisiones**. PostgreSQL de pruebas estuvo habilitado; se ejecutaron diez casos de ese ambiente, sin apuntar al rol/esquema productivo. Se agregaron 12 regresiones EV3 en `tests/test_ev3_stage.py` y una en `tests/test_cloud.py`; el resto conserva pruebas previas de EV2/full.

Runner: `.\.venv\Scripts\python.exe tools/run_ev3_checks.py`. Ejecuta Python y las dos suites JavaScript y genera [resultados por caso, TAP y SHA256](evidence/EV3_B11_TEST_RESULTS.json). La conexión opcional `PUENTES_TEST_DATABASE_URL` debe corresponder exclusivamente al rol restringido de pruebas; el runner elimina las variables productivas de su proceso.

- [Reporte 1.5.2.2 — captura, validación, persistencia, duplicados y errores](REPORTE_1_5_2_2_CAPTURA_MEDICIONES.md).
- [Reporte 1.5.2.3 — reglas, severidades, alertas, permisos y versiones](REPORTE_1_5_2_3_REGLAS_ALERTA.md).

Los tres modos pasan: EV2 mantiene el corte original y evaluación pendiente; EV3 habilita reglas/alertas con inicio básico y bloquea módulos futuros; full conserva panel, mantenimiento y programación. Se verificó también el nuevo corte en navegador local con SQLite temporal. No se realizó despliegue ni prueba de escritura en producción. Los resultados y recuentos de las secciones siguientes son evidencia histórica de entregas anteriores.

## Corrección de alcance al corte 26/10/2026

La etapa predeterminada es `cutoff_2026_10_26`; el modo `full` se conserva explícitamente. La suite previa mantiene sus expectativas completas y configura `full` en las bases y procesos de prueba.

Resultados finales: **66 pruebas aprobadas: 63 Python (189,890 s) y 3 JavaScript; 0 fallos**.

Los 12 casos nuevos de `tests/test_project_stage.py` verifican configuración por defecto/entorno y rechazo de etapa inválida; login/logout de los tres roles; cuatro entradas exactas en menú; inicio sin elementos futuros; GET/POST de rutas futuras con/sin CSRF y ninguna escritura; formularios HTML de puentes y sensores; inspecciones con fotos y categorías EV2; recepción manual/API sin consultas SQL a reglas y con evaluación pendiente; `plan_id` manipulado sin escrituras/fotos; proveedor y worker como procesos reales con intervalo 1 s, desconexión, recuperación, ambos puentes y deduplicación sin alertas; mockups del corte; alternancia de etapas sobre una base poblada y archivos fotográficos inmutables, recuperando evaluación, rutas y programación en `full`.

Los comandos de la suite son `python -m unittest discover -v` y `node --test tests/frontend.test.cjs`. Los procesos temporales IoT se cierran al terminar. Los mockups se generan con `python tools/build_mockups.py` (corte) y `python tools/build_mockups.py --stage full` (documentación completa separada). No se cambia el diseño general, las especificaciones técnicas, el esquema de datos ni las fechas o porcentajes de gestión.

La instalación local se reinicia en corte sobre su misma base, con copia SQLite privada previa y verificación de que las filas y hashes de fotografías no cambian al iniciar/consultar el modo. Los respaldos y datos quedan excluidos de Git. La evidencia anterior que sigue corresponde a la versión completa conservada. Se verificó en navegador el inicio local con las cuatro opciones y la ficha sin acceso a alertas. Se corrigió el cierre del árbol de procesos temporales en Windows para liberar el log heredado por el intérprete hijo del entorno virtual; la suite final completa no presenta errores de limpieza. La base local conserva 2 puentes, 6 componentes, 4 sensores y 18 reglas; no tenía mediciones, fotos ni alertas. La conservación de esas entidades pobladas y sus archivos se comprueba en las bases temporales de prueba, sin atribuir registros inexistentes a la instalación local.


Fecha: 23/10/2026. Referencia funcional: alcance EV2 actualizado del 22/10/2026, prevalente sobre especificaciones anteriores.

## Suite automatizada

`python -m unittest discover -v`: **51 pruebas Python aprobadas, 0 fallos** en la instalación del escritorio. Se conservan 36 casos de regresión (actualizados solo donde EV2 cambia unidades, comparaciones o interfaz) y se añaden 9 casos EV2 y 6 casos de corrección final. No se cuentan duplicados por herencia.

| Caso EV2 | Resultado verificado |
|---|---|
| test_numeric_levels_positive_negative_and_exact_limits | Ambos sensores, límites exactos e intermedios, comparación >=, signos positivos/negativos, una sola severidad máxima por medición. |
| test_reference_offset_snapshot_missing_and_invalid | Referencia 10°, cambios en ambos sentidos, límites decimales exactos, snapshot inmutable después de cambiar referencia, ausencia explícita sin alertar y rechazo de referencia no finita. |
| test_old_units_are_never_relabelled | Migración desde esquema anterior poblado: mm/s y valor originales conservados, configuración futura del sensor en m/s² con previous_unit, condición Mala sin equivalencia, fotos/alertas/FK preservadas e idempotencia. Nuevas capturas mm/s rechazadas. |
| test_visual_categories_and_configured_alerts | Baja/Media/Alta/Crítica, reglas por coincidencia exacta, niveles generados y rechazo de categorías anteriores en inspecciones nuevas. |
| test_rule_configuration_versions_and_highest_only | Umbrales editables por DOM, versiones conservadas, orden validado y alerta original vinculada a su regla; inspector sin permiso. |
| test_demo_setup_is_idempotent_and_customizable | Tres componentes requeridos por puente, referencias configuradas no sobrescritas, niveles desactivados no reactivados y ningún sensor físico adicional inventado. |
| test_professional_ui_and_severity_styles_all_roles | Cinco módulos y programación accesibles con los tres roles, una indicación discreta por pantalla, ausencia de HU/EDT/fechas/etiquetas repetidas y severidad diferenciada por texto/color. |
| test_ev2_provider_flow_both_bridges | HTTP independiente real y cliente municipal: aceleración 0,5 m/s² en un puente e inclinación con referencia 10° y lectura 9,771° en el otro; alertas Atención/Alerta, snapshot 0,229° y deduplicación. |
| test_fresh_demo_has_three_components_per_bridge | Instalación desde cero, seed-demo funcional, dos puentes con exactamente Tablero/Viga/Estribo, cuatro sensores configurables y referencias simuladas. |

La regresión conserva controles de permisos, CSRF, escape HTML, fotos opcionales/privadas y validación de archivos, persistencia, filtros, mantenimiento y trazabilidad sin cierre automático. También prueba el worker periódico (ciclos con reloj controlado), recuperación de desconexión y reintentos HTTP, singleton, identidad puente/variable, rechazo de registros inconsistentes y errores auditados. Mockups comprobados contra las vistas actuales.

## Corrección final de sensores y verificación IoT

Resultado: **54 pruebas aprobadas** (51 Python + 3 JavaScript), sin fallos. Comandos: `python -m unittest discover -v` y `node --test tests/frontend.test.cjs` (Node.js 18+). Las pruebas usan bases temporales; no incorporan sensores ni mediciones de prueba a la base del usuario.

- `templates/bridge.html`: los valores de ambos selectores pasan de etiquetas visibles a identificadores internos. Pruebas de creación y edición extraen los controles, opciones seleccionadas y CSRF de formularios renderizados, los envían y comprueban persistencia y respuesta. Incluyen ambos tipos y cambio de tipo sin mediciones.
- `static/app.js`: la revisión en navegador detectó que `[data-bridge]` también coincidía con un `<option>` de componente. En la ficha, esto deshabilitaba todos los componentes e impedía crear sensores. Ahora solo se usa `select[data-bridge]`. Las tres pruebas JavaScript ejecutan el script real con controles DOM simulados: ficha sin selector de puente, filtros con selector y actualización de unidades EV2.
- Permisos: DOM crea/edita; Inspector y Mantención ven la ficha sin formularios y sus envíos de alta/edición reciben 403. La regresión existente comprueba los cinco módulos, programación y permisos particulares de cada rol.
- Ubicaciones: `configure-demo-locations` completa solo los cuatro códigos originales simulados con ubicación pendiente/vacía y componente reconocido. Se comprueban Tablero/Viga/Estribo, conservación de una ubicación manual, IDs/asociaciones/referencias/reglas, repetición sin cambios y exclusión de sensores ajenos al piloto/componentes desconocidos.
- IoT con procesos reales: inicia el worker de intervalo 1 s sin proveedor, comprueba error auditado, inicia `mock_provider.py`, recibe cuatro registros de ambos puentes y cuatro alertas Alerta según EV2. Consultas periódicas repetidas mantienen cuatro registros/alertas. Detiene y reinicia el proveedor, verifica web disponible y worker vivo, y recibe el nuevo lote hasta ocho registros/alertas. La consulta manual posterior tampoco duplica. No se simulan el reloj ni las respuestas HTTP en este caso. Los límites Atención/Alerta/Crítico y la severidad máxima siguen cubiertos por los casos EV2.
- Interfaz real: en navegador y base aislada, DOM creó UI-VIBRACION en Viga y UI-INCLINACION en Estribo, editó sus ubicaciones y la referencia a 11,25°, guardó y vio los datos actualizados. Ambos formularios de edición conservaron su tipo seleccionado. Esos sensores de verificación no pertenecen a la instalación del usuario.
- Mockups: se regenera únicamente el documento existente desde las plantillas, reflejando valores de opciones corregidos y ubicaciones iniciales específicas; no se agregan pantallas ni se rediseñan los cinco módulos.

La configuración local de ubicaciones se aplica con respaldo SQLite privado y comparación de todos los registros: solo cambian ubicaciones pendientes elegibles y se añade la auditoría correspondiente. No modifica umbrales ni asociaciones. Proveedor y worker utilizados para verificar se detienen al terminar; su arranque operativo continúa documentado en README.

## Defectos corregidos durante la verificación

- Se añadió una lectura de inclinación con referencia/variación a los mockups para representar el flujo completo.
- Se cerró explícitamente la conexión SQLite de la prueba de instalación nueva, para que Windows libere el archivo temporal.
- No quedan fallos conocidos en la suite final.

## Migración de la instalación existente

Web detenida antes del respaldo y migración; no había worker activo. Respaldo e informe privados en `instance/backup-antes-EV2-*.sqlite` y `instance/EV2_MIGRACION_VERIFICADA.json`, excluidos de Git. Comparación por ID de todas las columnas anteriores: cuentas, puentes, sensores, mediciones, inspecciones, fotografías, reglas, alertas, notas, tareas, auditoría y programación conservados. Excepciones documentadas: unidad de configuración futura de sensores y normalización del nombre del componente demo, conservando ID y relaciones. Las mediciones no cambian de unidad ni valor.

En la base local había 3 cuentas, 2 puentes, 2 componentes, 4 sensores y 2 operaciones de auditoría; no había mediciones/inspecciones/fotos/alertas. Por tanto, la preservación de esas entidades pobladas se prueba con bases temporales en la suite, no se atribuye a registros locales inexistentes. Se comprobaron hashes de los archivos disponibles, integrity_check=ok y foreign_key_check sin errores. Tras actualizar: Tablero/Viga/Estribo por puente, sensores existentes, referencias de demostración y reglas EV2 iniciales. Repetir la configuración no duplica infraestructura ni reglas.

Servidor EV2 reiniciado con Waitress y GET /login respondió HTTP 200. Los mockups se generan desde las plantillas reales con datos temporales; no se afirma prueba de tablet física ni nueva captura de pantalla. La imagen panel-verificado.png es de una versión anterior y no acredita los cambios EV2.

## Alcance y pendientes

Requisitos EV2 de unidades, niveles, referencia, condiciones visuales, infraestructura demo, limpieza de interfaz, migración, documentación y pruebas corregidos. Matriz individual HU-01 a HU-08 conservada y complementada con la evidencia EV2. HU-08 se verifica solo con proveedor simulado, no con hardware/proveedor real. No se declara diagnóstico estructural ni validación externa. HU-09 (aceptación municipal, capacitación, piloto operacional y cierre) permanece pendiente y fuera de estas correcciones.

Término EDT 1.4.5/1.4.6: **24/11/2026**. Presentación académica: **26/11/2026**. Fechas conservadas solo en documentación, no en las pantallas operativas.
