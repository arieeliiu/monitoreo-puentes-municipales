# D7 — Plan de migración de identificadores de referencia

Los códigos activos nuevos son PM-001/PM-002 y sus sufijos VIBRACION/INCLINACION. No representan integración física. `simulated` se conserva. Los códigos retirados solo aparecen como origen explícito de migración, fixtures de compatibilidad o evidencia histórica que no se debe reescribir.

`reference_migration.py` y `tools/rename_reference_identifiers.py` están separados del arranque, init-db, migraciones de esquema, seed-demo, web y despliegue. **No se ejecutaron sobre producción.** No hay DDL. El único cambio posible son seis campos code: dos puentes y cuatro sensores canónicos. IDs, relaciones, ubicaciones, mediciones/IDs externos, referencias, umbrales/versiones, inspecciones/fotos y auditoría conservan sus valores.

## Comportamiento seguro

- Predeterminado: plan de solo lectura y rollback; SQLite se abre mode=ro. `--apply` es explícito y requiere `--backup`.
- SQLite exige una base existente. Al aplicar crea una copia con backup de SQLite, sin sobrescribir un archivo existente; luego vuelve a validar y aplica en una transacción.
- PostgreSQL exige `--postgres --schema puentes` (o puentes_test) y la variable privada PUENTES_MIGRATION_DATABASE_URL; no toma DATABASE_URL por defecto. Para aplicar, el respaldo PostgreSQL externo indicado debe existir y no estar vacío. El operador debe verificar que sea recuperable y corresponda al entorno: el archivo por sí solo no prueba esa correspondencia.
- Rechaza destinos ocupados, puentes no marcados como prueba, sensores con tipo/puente incorrecto o inventario canónico parcial/personalizado. No fusiona ni inventa registros. Ante conflicto, nada se aplica. Repetir sobre un inventario ya renombrado devuelve un plan vacío.
- Los textos históricos de auditoría y los ID externos no se sustituyen. La migración no interpreta sus prefijos ni reclasifica lecturas.

El procedimiento operativo completo, con inventario SQL, pausa de Cron, respaldos y orden de publicación, está en [PLAN_PUBLICACION_EV3.md](PLAN_PUBLICACION_EV3.md). Este documento describe las garantías de la herramienta; no acredita ejecución en el entorno publicado.

## Secuencia posterior a revisión y autorización

1. Revisar inventario, DSN/esquema y plan sobre una copia restaurada. Detener web/escritores y captura Cron/worker del entorno autorizado para impedir cambios concurrentes.
2. Obtener y verificar respaldo de base y fotos; PostgreSQL requiere respaldo externo restaurable, no una copia SQLite de otro entorno.
3. Ejecutar solo planificación: `python tools/rename_reference_identifiers.py --sqlite C:\respaldo\puentes.sqlite`, o `python tools/rename_reference_identifiers.py --postgres --schema puentes` con la variable privada preparada por el operador. Revisar los IDs exactos y conflictos.
4. Solo con autorización de aplicación, añadir `--apply --backup` con la ruta apropiada. Comprobar códigos y relaciones; si hay conflicto, detenerse y resolverlo con DOM, sin cambiar códigos manuales de forma automática.
5. Publicar coordinadamente el código de proveedores nuevos y activar la etapa autorizada; restaurar captura y comprobar ambos puentes, deduplicación y alertas. No publicar primero el proveedor nuevo contra un inventario que aún usa los códigos retirados.
6. Si falla, mantener escritores detenidos y revisar recuperación de código/datos en conjunto. No restaurar una copia vieja encima de registros nuevos sin evaluación y aprobación específicas.

Pruebas: los tres casos D7 de tests/test_ev3_closure.py verifican plan sin cambios, conservación de todas las tablas/fotos, aplicación/idempotencia, conflictos y CLI/respaldo. test_postgres_d7_migration_fixture repite plan/aplicación sobre puentes_test. [Resultados reales](evidence/EV3_CIERRE_TECNICO_TEST_RESULTS.json).
