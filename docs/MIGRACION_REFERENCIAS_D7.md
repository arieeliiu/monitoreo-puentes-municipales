# D7: migración de identificadores de referencia

## Alcance vigente

Los códigos nuevos son PM-001/PM-002 y sus cuatro sensores canónicos. Las mediciones provienen del proveedor de referencia; el alcance no incluye sensores físicos (SC-01). El contrato SMPMRB v1 no contiene `simulated`; la opción A de revisión retira sus cinco columnas internas en un paso posterior y separado de D7.

No se ejecutaron estas herramientas en producción. No alteran unidades, umbrales, IDs, relaciones, mediciones/IDs externos, inspecciones, fotos o textos históricos de auditoría. No crean sensores ni sustituyen inventarios personalizados.

## Identificación segura sin indicador de simulación

`reference_data.reference_inventory` contrasta los dos códigos, nombre y ubicación conocidos de cada puente, los dos sensores canónicos por puente con tipo/unidad correctos, su asociación por componente/puente y los componentes Tablero/Viga/Estribo. Se rechazan inventarios incompletos, mixtos, personalizados, colisiones y sensores adicionales o incompatibles. No se autoriza una modificación por un código aislado. Una ubicación manual de sensor se conserva.

`reference_migration.rename_reference_identifiers` acepta esquemas anteriores y nuevos, sin SELECT de `bridges.simulated`. Si no hay códigos retirados, valida el inventario PM cuando existe; un plan vacío sin ese inventario no certifica una instalación lista. Los códigos DEM solo se admiten como origen explícito de migración, fixtures de compatibilidad y evidencia histórica.

## Orden para la base anterior de 13 tablas y 104 columnas

1. Detener escritores/captura, inventariar y comprobar respaldos restaurables de base y fotos.
2. Planificar D7 sobre el esquema anterior; revisar seis cambios de código. Aplicar solo con autorización y respaldo.
3. Validar códigos PM, sensores y relaciones.
4. Planificar el retiro separado de las cinco columnas. Aplicarlo solo con autorización y respaldo posterior a D7.
5. Verificar 13 tablas/99 columnas activas, contenido conservado, restricciones, índices, RLS y fotos.
6. Activar el código actualizado y comprobar captura, alertas, panel y mantenimiento antes de reanudar escritores.

El código nuevo rechaza la conexión de aplicación a un esquema que aún tenga las cinco columnas; no las elimina al arrancar. Las preparaciones aditivas `migrations.py`/`ev2_migration.py` tampoco ejecutan este retiro. Para un esquema anterior a EV2 o personalizado, detenerse y preparar su actualización en una copia; este procedimiento parte de la versión anterior de 104 columnas.

## Comandos propios del repositorio

Planificación por defecto; SQLite abre mode=ro y la transacción se revierte:

```powershell
python tools/rename_reference_identifiers.py --sqlite C:\respaldo\EV3\copia.sqlite
python tools/retire_legacy_columns.py --sqlite C:\respaldo\EV3\copia.sqlite
# PostgreSQL: preparar PUENTES_MIGRATION_DATABASE_URL privadamente; no se usa DATABASE_URL por defecto.
python tools/rename_reference_identifiers.py --postgres --schema puentes
python tools/retire_legacy_columns.py --postgres --schema puentes
```

El segundo plan rechaza códigos DEM pendientes. `--apply --backup <ruta>` es explícito para ambas herramientas. SQLite crea una copia nueva, nunca sobrescribe un backup; PostgreSQL exige un respaldo externo no vacío cuya procedencia/restaurabilidad debe verificar el operador. No confundir esa comprobación de archivo con un ensayo de recuperación.

El retiro es transaccional e idempotente: elimina únicamente bridges.simulated, measurements.simulated, inspections.simulated, rules.simulated y alerts.simulated. Compara hashes/conteos de todas las filas conservadas y firmas de índices/restricciones/políticas, comprueba FK en SQLite y revierte ante conflicto, dependencia o cambio inesperado. No usa CASCADE. Un retiro parcial requiere revisión manual.

## Evidencia y publicación

Los casos de `tests/test_christian_review.py` y los nuevos casos PostgreSQL de `tests/test_cloud.py` ejercitan instalación nueva, D7 anterior al retiro, planificación, aplicación, repetición, rechazo parcial, índice dependiente y preservación de datos. Los resultados reales están en los cuatro informes y [verificación](VERIFICACION.md); las evidencias anteriores no se sobrescriben.

El [procedimiento de publicación](PLAN_PUBLICACION_EV3.md) contiene inventario SQL, pausa del Cron existente, respaldos, configuración de etapa y recuperación coordinada. Si D7 ya se aplicó pero falla el retiro o publicación, mantener congelación: no reactivar un proveedor DEM contra inventario PM ni el código nuevo contra columnas antiguas. No restaurar un dump viejo encima de altas posteriores sin reconciliación y autorización.

Referencias del DDL utilizado: [PostgreSQL ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html) y [SQLite ALTER TABLE](https://www.sqlite.org/lang_altertable.html). La herramienta añade las comprobaciones de conservación e integridad descritas; no desactiva protecciones para forzar el DROP.
