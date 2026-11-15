# Cierre técnico EV3 — D7, B-11 y B-14

## Origen y preservación del trabajo

Se partió de origin/main `e191aed818b8ee94296594f633ed2afe8111ec3d` en un worktree separado, rama feature/ev3-cierre-tecnico. La copia original mantiene la carpeta B-03 sin seguimiento; no se editó, descartó ni incorporó a commits. Antes de recibir la corrección del Plan v3.0 solo se había creado la rama y leído fuentes; git diff estaba vacío y no había commits nuevos. No existía implementación del prompt anterior que revertir.

Se conservaron motor/versiones/seguimiento B-11, panel/mantenimiento preliminares de full, API y proveedores, simulated, permisos, CSRF, fechas chilenas, paginación, fotos y pruebas existentes. El cambio de backend del panel solo evita consultar programaciones cuando la etapa no las habilita. Mantenimiento ya cubría las operaciones requeridas y se verificó sin reconstruirlo.

Una regeneración inicial propia de mockups incorporaba otras diferencias de presentación. Se sustituyó por ediciones acotadas de códigos y aviso, manteniendo la estructura original. Los ensayos nuevos corrigieron cierre de conexiones SQLite y codificación de subprocess en fixtures; el primer intento en sandbox no pudo acceder al temporal/HTTP local. No se modificó el motor por esos resultados. Una ejecución completa quedó interrumpida antes de generar informe; se repitió desde cero. Solo se acredita la ejecución final enlazada.

## Alcance implementado y probado

- D7: PM-001/PM-002 compartidos por carga inicial y ambos proveedores; retirada del aviso en mockups (las interfaces actuales ya lo habían retirado); trazabilidad simulated conservada. Plan opcional D7 separado y no ejecutado en producción.
- B-11: corte 09/11 conservado y verificado; informes 1.5.2.2 y 1.5.2.3 actualizados sin borrar su evidencia anterior.
- B-14: corte explícito cutoff_2026_11_28 permite panel y mantenimiento existentes, sin programación. No hay rediseño ni funciones nuevas ajenas al alcance. Informes 1.5.2.4 y 1.5.2.5 generados.
- EV2 sigue siendo el valor predeterminado en código. Full conserva programación y todos sus módulos anteriores. No hay cambios automáticos por fecha del equipo, migración al iniciar ni reevaluación de históricos.

## Hitos oficiales de esta tarea

| Entregable / hito | Fecha acordada | Tratamiento |
|---|---|---|
| Plan original 1.4.4 | 03/11/2026 | Histórico conservado |
| Plan original 1.5.2.2 | 28/10/2026 | Histórico conservado |
| Plan original 1.5.2.3 | 04/11/2026 | Histórico conservado |
| Recuperación formal B-11 | Antes del 15/11/2026 | Revisión Christian; no se declara entrega formal con estas pruebas |
| Término planificado 1.4.5/1.4.6 | 24/11/2026 | No se modifica ni declara hito cumplido |
| Publicación, pruebas y corte B-14 | Antes del corte 28/11/2026 | Publicación pendiente de autorización |
| Entrega EV3 | 30/11/2026 | Entrega del equipo pendiente |

Las referencias a 26/11 en documentos anteriores son antecedentes, no el hito vigente de esta tarea. No se modificaron entregables B-01/B-02/B-03 para corregir documentación del equipo; su cotejo corresponde a sus responsables. UAT municipal de diciembre queda fuera de EV3.

## Evidencia real

Fecha real de ejecución: **2026-11-14**, America/Santiago; inicio `2026-11-14T21:35:53-03:00`, término `2026-11-14T21:48:52-03:00`. El nombre del corte 28/11/2026 describe alcance, no la fecha de estas pruebas ni un hito declarado cumplido.

Ambiente: Windows, Python 3.12.14, SQLite 3.53.1, Node.js y PostgreSQL remoto con usuario y esquema restringidos `puentes_test`. Las fixtures y fotos son temporales. El runner elimina variables productivas y solo admite un DSN de pruebas restringido. No se conectó a datos productivos ni se modificó Vercel, Cron, Storage o credenciales.

Suite final completa: **132 pruebas Python (incluidas 18 PostgreSQL aisladas) y 20 JavaScript aprobadas; 0 fallos, 0 errores y 0 omisiones**. Son 12 regresiones SQLite nuevas y 3 PostgreSQL nuevas, además de la suite previa; no se suman ensayos ni se duplican pruebas heredadas. [JSON de resultados por caso, fechas, duración, contadores y SHA256](evidence/EV3_CIERRE_TECNICO_TEST_RESULTS.json); [log íntegro](evidence/EV3_CIERRE_TECNICO_TEST_RUN.log).

Seis comprobaciones de navegador local aprobadas, con tres roles, creación/edición DOM, seguimiento Mantención, Inspector solo lectura y alerta Activa después de actividad Completada. Hay observaciones, capturas, log HTTP y consulta de las filas/auditoría persistidas de su SQLite temporal en docs/evidence/EV3_CIERRE_BROWSER.json. No se suman a las pruebas automatizadas.

## Pendientes y responsabilidades

No hay fallo funcional pendiente en los casos ejecutados. B-11 queda técnicamente recuperado para revisión de Christian; B-14 queda preparado técnicamente para revisión compartida Ariel/Christian y revisión Alex. No se atribuye trabajo humano de revisión, aceptación o entrega a esas personas como realizado. Christian debe revisar frontend/procesos/flujos existentes y su parte de la entrega compartida; no se propone un rediseño ni funciones extra.

Faltan autorización de migración/inventario del entorno, publicación coordinada y comprobación posterior de roles/captura, además de la entrega/revisión formal del equipo. La exclusión git.deploymentEnabled=false afecta solo a feature/ev3-cierre-tecnico para impedir despliegues automáticos al hacer el push/PR solicitado; main y sus ajustes permanecen intactos. No se ejecutaron despliegues ni se cambiaron variables productivas, Cron, Storage o credenciales. [Plan D7](MIGRACION_REFERENCIAS_D7.md).

Los cambios se entregan en la rama feature/ev3-cierre-tecnico con PR hacia main sin fusionar. El diff y la evidencia identifican exactamente el código verificado. No se desarrolló integración real, predicción, estándar adicional, piloto operacional, marcha blanca, capacitación ni UAT.
