# Verificación final EV2

Fecha: 23/10/2026. Referencia funcional: alcance EV2 actualizado del 22/10/2026, prevalente sobre especificaciones anteriores.

## Suite automatizada

`python -m unittest discover -v`: **45 pruebas aprobadas, 0 fallos** en la instalación del escritorio. Se conservan 36 casos de regresión (actualizados solo donde EV2 cambia unidades, comparaciones o interfaz) y se añaden 9 casos EV2. No se cuentan duplicados por herencia.

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
