# Verificación técnica: revisión Christian EV3

**147 Python (incluidas 20 PostgreSQL aisladas) y 20 JavaScript aprobadas; cero fallos, errores u omisiones**. Ejecución real: 15/11/2026 15:49:06 a 15/11/2026 16:04:02 (America/Santiago). Código probado: `e71352105fd1f5a3d109f273150c22290b6cea1b`. [JSON por caso](evidence/EV3_CHRISTIAN_TEST_RESULTS.json) y [log](evidence/EV3_CHRISTIAN_TEST_RUN.log).

## Versión y evidencia

HEAD probado `e71352105fd1f5a3d109f273150c22290b6cea1b`, rama `feature/ev3-cierre-tecnico`, worktree limpio al inicio. Base de comparación `e191aed818b8ee94296594f633ed2afe8111ec3d`; no se confunde con el código ejecutado. Los 73 archivos registrados coinciden con los blobs Git de HEAD y no cambiaron durante la ejecución. Durante la suite solo se redactó documentación fuera del manifiesto. Los commits documentales posteriores no son ejecuciones nuevas.

## Esquema y migraciones comprobados

SQLite y PostgreSQL nuevos: 13 tablas / 99 columnas. Esquema anterior: 104 columnas; D7 antes del retiro, seis códigos cambiados y cinco columnas eliminadas. Las demás filas/IDs/relaciones/fotos/auditoría se conservan. Retiro idempotente, planificación sin cambios y aplicación con respaldo explícito. Se rechazan retiro parcial e inventario incompatible; un índice dependiente revierte toda la operación. PostgreSQL conserva 27 FK, 9 CHECK, 9 UNIQUE, 13 PK, 27 índices (5 explícitos) y 13 políticas RLS. [Inventario y catálogo](evidence/EV3_CHRISTIAN_SCHEMA.json).

Casos: tests.test_christian_review.ChristianTests y test_postgres_fresh_schema_thirteen_tables_ninety_nine_columns / test_postgres_old_d7_then_retire_preserves_data_rls_constraints de tests.test_cloud.PostgresTests. La importación SQLite → PostgreSQL actual se verifica con foto temporal/doble de Storage; una fuente anterior se rechaza explícitamente hasta completar el procedimiento.

## Errores reales encontrados durante preparación

Un ensayo local previo descubrió 145 casos: 124 aprobados, 1 error y 20 PostgreSQL omitidos por no habilitar DSN en ese ensayo; JavaScript no se ejecutó allí. La prueba construía una base antigua con schema.sql actualizado e intentaba insertar seis valores en bridges, ahora de cinco columnas. Se corrigió la fixture usando tests/fixtures/schema_pre_christian.sql; la regresión pertinente se repitió satisfactoriamente antes de la suite completa. No se cambió el motor por ese error. [Log del ensayo previo](evidence/EV3_CHRISTIAN_PREFLIGHT_SQLITE.log). No se presenta ese ensayo como evidencia de versión fijada ni se suma a los resultados finales.

## Alcance funcional

Push/pull de ocho campos sin simulated; validación relacional y unidades; deduplicación; reintentos y errores auditados; reglas/versiones, alertas numéricas/visuales y seguimiento; panel, mantenimiento, roles, CSRF, fotografías y etapas. [Captura](REPORTE_1_5_2_2_CAPTURA_MEDICIONES.md), [reglas](REPORTE_1_5_2_3_REGLAS_ALERTA.md), [panel](REPORTE_1_5_2_4_PANEL_MONITOREO.md), [mantenimiento](REPORTE_1_5_2_5_PLANIFICACION_MANTENIMIENTO.md).

Las mediciones provienen del proveedor de referencia; el alcance no incluye sensores físicos (SC-01). No se acredita conexión física, certificación externa, piloto operacional, marcha blanca ni UAT municipal. El token pull es opcional/global y el cliente admite HTTP local; HTTPS obligatorio y credenciales independientes por proveedor siguen pendientes. No se desplegó ni migró producción; SC-04 requiere formalización.

## Reproducción

`python tools/run_ev3_checks.py --output docs/evidence/EV3_CHRISTIAN_TEST_RESULTS.json`, con salida nueva y PUENTES_TEST_DATABASE_URL aislada. El runner ejecuta unittest y las tres suites JavaScript; no provisiona ni despliega. [Procedimiento de publicación pendiente](PLAN_PUBLICACION_EV3.md). ## Antecedentes conservados

| Fecha de ejecución | Versión identificable | Resultado anterior | Evidencia |
|---|---|---|---|
| 08/11/2026 | Fuentes por SHA-256; sin atribuir commit posterior | 98 Python + 10 JavaScript aprobadas | [B-11](evidence/EV3_B11_TEST_RESULTS.json) |
| 14/11/2026, 21:35 | Worktree sobre e191aed; fuentes por SHA-256 | 132 Python + 20 JavaScript aprobadas | [Cierre anterior](evidence/EV3_CIERRE_TECNICO_TEST_RESULTS.json) |
| 14/11/2026, 22:04 | f17bb26 | 135 Python + 20 JavaScript aprobadas | [Revisión anterior](evidence/EV3_PR1_FINAL_TEST_RESULTS.json) |

Estos resultados no se suman a la ejecución principal. Las capturas anteriores conservan su fecha y alcance; no se presentan como nuevas capturas de esta revisión.

[Verificación anterior íntegra](VERIFICACION_HISTORICO_ba0b74e.md).
