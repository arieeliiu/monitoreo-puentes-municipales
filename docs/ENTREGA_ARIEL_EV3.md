# Entrega técnica individual de Ariel: EV3

Estado: candidato preparado para revisión en feature/ev3-cierre-tecnico, PR #1 en borrador. No implica aprobación formal, integración o publicación.

| Entregable técnico | Archivo / evidencia vigente | Estado |
|---|---|---|
| B-11 / 1.4.4 | [Captura 1.5.2.2](REPORTE_1_5_2_2_CAPTURA_MEDICIONES.md), [Reglas 1.5.2.3](REPORTE_1_5_2_3_REGLAS_ALERTA.md); app.py, provider_client.py y proveedores de referencia. | Contrato de ocho campos sin simulated; reglas, versiones, alertas y seguimiento conservados. |
| D7 y opción A | [Procedimiento](MIGRACION_REFERENCIAS_D7.md); reference_data.py, reference_migration.py, schema_revision.py y herramientas explícitas. | Inventario verificado; retiro de cinco columnas sin marca sustituta, sin migración productiva. |
| B-14 / 1.4.5 | [Panel 1.5.2.4](REPORTE_1_5_2_4_PANEL_MONITOREO.md). | Panel avanzado en corte 28/11; sin programación de inspecciones. |
| B-14 / 1.4.6 | [Mantenimiento 1.5.2.5](REPORTE_1_5_2_5_PLANIFICACION_MANTENIMIENTO.md). | DOM administra; Mantención solo asignadas; Inspector consulta; completar no resuelve alerta. |
| B-01/B-02/B-03 en Drive | [Traspaso exacto](CAMBIOS_PENDIENTES_DRIVE_EV3.md), SQL y [diccionario verificable](evidence/EV3_CHRISTIAN_SCHEMA.json). | Pendientes de aplicar en originales; no se accedió a Drive ni se modificaron esos documentos. |

**147 Python (incluidas 20 PostgreSQL aisladas) y 20 JavaScript aprobadas; cero fallos, errores u omisiones**. Ejecución real: 15/11/2026 15:49:06 a 15/11/2026 16:04:02 (America/Santiago). Código probado: `e71352105fd1f5a3d109f273150c22290b6cea1b`. [JSON por caso](evidence/EV3_CHRISTIAN_TEST_RESULTS.json) y [log](evidence/EV3_CHRISTIAN_TEST_RUN.log).

## Publicación y pendientes

[Plan de publicación](PLAN_PUBLICACION_EV3.md) preparado y no ejecutado: respaldo/restauración, pausa de escritores y captura, D7 sobre esquema anterior, validación PM, retiro de columnas, comprobación de 13/99, activación del código y verificación posterior.

El código de esta revisión no se desplegó. No se modificaron producción, credenciales o recursos externos. Las mediciones provienen del proveedor de referencia; el alcance no incluye sensores físicos (SC-01). Se conservan las limitaciones de HTTPS, credenciales por proveedor y conformidad externa. SC-04 no se declara cerrada automáticamente.

Quedan la actualización de originales Drive y la revisión/aceptación formal del equipo; la revisión de Christian del 15/11 es el origen de estas correcciones, no una aprobación de su implementación posterior. No se atribuyen aprobaciones adicionales a Christian, Alex o la profesora. Migración/publicación requieren autorización y operación coordinada.

Hitos oficiales intactos: recuperación formal B-11 antes del 15/11/2026, término planificado de panel/mantenimiento 24/11/2026, corte 28/11/2026, entrega EV3 30/11/2026. No se acredita su cumplimiento por ejecutar pruebas. Sin hardware, nuevas integraciones, predicción, piloto, marcha blanca, capacitación o UAT.
