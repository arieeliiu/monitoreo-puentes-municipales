# Procedimiento de publicación EV3 / B-14 y D7

Estado: **publicación y migración preparadas; no ejecutadas**. El 15/11/2026 el usuario autorizó subir los cambios a `main`; esa integración no ejecuta este procedimiento ni autoriza una migración productiva. Ejecutar la publicación solo después de aprobar un SHA concreto y una ventana del entorno. B-11: recuperación técnica para entrega formal antes del 15/11/2026; B-14: término planificado 24/11, corte de estado 28/11, entrega EV3 30/11. Este procedimiento no acredita esos hitos.

## 1. Identificar versión, entorno y responsables

Trabajar desde una copia limpia del SHA revisado; registrar `git rev-parse HEAD`, `git status --short` y la versión/despliegue anterior para recuperación. La integración de `feature/ev3-cierre-tecnico` a `main` fue autorizada por separado. `main` y esta rama tienen el despliegue automático deshabilitado en `vercel.json`: el código nuevo rechaza el esquema anterior y no debe activarse antes de completar la preparación explícita de la base. La integración conserva el despliegue existente; publicación y migración siguen pendientes de autorización y ejecución. Este ajuste de configuración es posterior a la ejecución de 147 pruebas Python y 20 JavaScript del código `e713521`; no modifica ese código funcional ni sus evidencias.

Confirmar el proyecto Vercel y el proyecto Supabase reales en sus paneles; no crear otros recursos. El repositorio documenta esquema `puentes`, buckets privados `puentes-fotos` y `puentes-fotos-staging`, y trabajo Supabase Cron `puentes-iot-60s`; cotejarlos, no asumir que siguen iguales. No confundirlos con `puentes_test`, reservado a pruebas destructivas de fixtures.

Herramientas: Python/dependencias de `requirements.txt`, `psql`, `pg_dump` y `pg_restore` compatibles con el servidor, y Vercel CLI fijado por el repositorio: `npx.cmd --yes vercel@65.2.0`. Se consultó únicamente `--help` de deploy/env update/promote; los binarios PostgreSQL no estaban instalados en este equipo de revisión. Su disponibilidad y restauración real quedan como precondición del operador.

Variables privadas existentes a conservar: `DATABASE_URL`, `DATABASE_SCHEMA`, `SECRET_KEY`, `PHOTO_STORAGE`, `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `SUPABASE_STORAGE_BUCKET`, `COOKIE_SECURE`, `CLOUD_PROVIDER` y `CRON_SECRET`. Solo se prevé cambiar `PROJECT_STAGE` al corte autorizado. La CLI D7 **no usa DATABASE_URL**: requiere `PUENTES_MIGRATION_DATABASE_URL` y `--schema` explícitos. El DSN debe tener permisos de SELECT/UPDATE sobre los códigos del inventario objetivo. Prepararlo fuera de Git sin imprimirlo; no rotar ni crear credenciales en esta tarea.

Los ejemplos `service=puentes_ev3` suponen que el operador ha definido ese alias local en su archivo privado de servicios libpq, con host/puerto/base/usuario reales, TLS `verify-full` y certificado correcto (`certs/supabase-ca.crt`). No es un recurso existente ni una credencial nueva. Password en archivo privado de contraseñas; no escribirla en argumentos, chat o logs. Las rutas `C:\respaldo\EV3\...` son ejemplos: usar una carpeta privada existente fuera del repo y sin sobrescribir respaldos anteriores.

## 2. Inventario de solo lectura y decisión D7

Ejecutar con `psql "service=puentes_ev3" -X -v ON_ERROR_STOP=1` o SQL Editor en el entorno confirmado. **Solo consultas**:

```sql
BEGIN READ ONLY;
SELECT current_database(), current_user;
SELECT b.id,b.code,b.name,c.id AS component_id,c.name AS component,
       s.id AS sensor_id,s.code AS sensor_code,s.kind,s.unit
FROM puentes.bridges b
LEFT JOIN puentes.components c ON c.bridge_id=b.id
LEFT JOIN puentes.sensors s ON s.component_id=c.id
ORDER BY b.id,c.id,s.id;
SELECT 'bridges' AS entity,count(*) FROM puentes.bridges
UNION ALL SELECT 'components',count(*) FROM puentes.components
UNION ALL SELECT 'sensors',count(*) FROM puentes.sensors
UNION ALL SELECT 'measurements',count(*) FROM puentes.measurements
UNION ALL SELECT 'rules',count(*) FROM puentes.rules
UNION ALL SELECT 'alerts',count(*) FROM puentes.alerts
UNION ALL SELECT 'tasks',count(*) FROM puentes.tasks
UNION ALL SELECT 'inspections',count(*) FROM puentes.inspections
UNION ALL SELECT 'photos',count(*) FROM puentes.photos;
SELECT jobid,jobname,schedule,active FROM cron.job
WHERE jobname='puentes-iot-60s';
COMMIT;
```

Conservar inventario y contadores privadamente. No listar secretos descifrados de Vault ni passwords de usuarios. Guardar también valores/configuración anteriores de etapa, proveedor, intervalo, job y despliegue en un registro de operación protegido.

- Si existen `DEM-01`/`DEM-02` y sus cuatro sensores canónicos, con nombres/ubicaciones y relaciones esperados, sin códigos PM de destino ocupados: **puede requerir D7**, sujeto al plan y respaldo.
- Si existen `PM-001`/`PM-002` y sus sensores correctos y el plan está vacío: **no aplicar una migración vacía**. Verificar también relaciones/tipos/unidades; un plan vacío por sí solo no certifica que el inventario esperado exista.
- Inventario mixto, parcial, códigos personalizados, firmas de inventario incompatibles, destinos ocupados o asociaciones inesperadas: detener y revisar. La herramienta rechaza colisiones/casos canónicos incompletos, no decide cambios manuales ni fusiona puentes. No ejecutar seed, configuradores o importadores para "arreglarlo".

## 3. Congelar escritores y captura antes del respaldo definitivo

El plan puede obtenerse antes de la ventana; inventario, respaldo y plan definitivos se repiten con escritores detenidos. La aplicación no ofrece un flag de solo lectura. El operador debe bloquear temporalmente tráfico de escritura de usuarios y API, incluidos POST manuales DOM, inspecciones/fotos y `/api/v1/measurements`, mediante los controles existentes del entorno; contemplar URL estable y URLs directas de despliegues. Cerrar una pestaña o esconder botones no bloquea escrituras. Registrar cómo se verifica el bloqueo. Si no puede garantizarlo, **no aplicar D7 ni publicar contra ese inventario**.

La captura alojada está en **Supabase pg_cron**, no en un Cron declarado en `vercel.json`. Guardar `active`/schedule previos. Con administrador, durante la ventana autorizada:

```sql
-- Pausa el trabajo existente; conserva nombre, comando e intervalo.
SELECT cron.alter_job(job_id:=jobid,active:=false)
FROM cron.job WHERE jobname='puentes-iot-60s' AND active;
SELECT jobid,jobname,schedule,active FROM cron.job
WHERE jobname='puentes-iot-60s';
SELECT jobid,runid,status,start_time,end_time
FROM cron.job_run_details
WHERE jobid IN (SELECT jobid FROM cron.job WHERE jobname='puentes-iot-60s')
ORDER BY start_time DESC LIMIT 10;
```

Pausar el job no cancela HTTP ya enviado. Esperar la finalización de solicitudes/ciclos en curso y comprobar logs y contadores estables, incluidos `net._http_response` y Vercel. No registrar cabeceras Bearer. Si hay workers locales, detener sus terminales `flask --app app poll-provider` con Ctrl+C y confirmar que terminaron; no arrancar un worker paralelo sobre la base publicada. Mantener proveedor HTTP detenido mientras dure el cambio si lo usa ese entorno. No cambiar el intervalo, Vault ni CRON_SECRET.

No ejecutar `sql/schedule_iot.sql` como pausa: recrea el job con un intervalo fijo de un minuto. No usar `cron.unschedule` si solo se necesita suspender y conservar el trabajo.

## 4. Respaldo recuperable de PostgreSQL y Storage

Con escritores detenidos, exportar el esquema de aplicación, datos, secuencias, propietarios y ACL; guardar roles/permisos y configuración de Cron/Vault mediante el procedimiento administrativo existente, sin publicar secretos. Un respaldo de plataforma verificado puede complementar la copia lógica. No asumir que el plan gratuito dispone de backups automáticos recuperables.

```powershell
pg_dump --dbname="service=puentes_ev3" --format=custom --schema=puentes --file="C:\respaldo\EV3\puentes-pre-d7.dump"
if ($LASTEXITCODE -ne 0) { throw 'Fallo de respaldo; detener publicación' }
pg_restore --list "C:\respaldo\EV3\puentes-pre-d7.dump"
if ($LASTEXITCODE -ne 0) { throw 'Respaldo ilegible; detener publicación' }
Get-FileHash -Algorithm SHA256 -LiteralPath 'C:\respaldo\EV3\puentes-pre-d7.dump'
```

`pg_restore --list` solo valida lectura del archivo. **Antes de aplicar, restaurarlo en una base/esquema aislado y comprobar relaciones, secuencias, filas y acceso con los roles previstos.** No restaurar en producción para probarlo. El dump de `puentes` no incluye roles globales, Vault ni contenido binario de Storage; conservar esos elementos mediante respaldo administrativo protegido por separado. La herramienta D7 solo comprueba que el archivo de backup indicado exista y no esté vacío: no certifica su procedencia/restaurabilidad.

Exportar los bytes de ambos buckets privados con la herramienta de descarga autorizada del operador. Para inventariar los objetos sin modificar Storage, ejecutar como administrador y conservar el resultado privadamente:

```sql
BEGIN READ ONLY;
SELECT bucket_id,id,name,metadata,created_at,updated_at
FROM storage.objects
WHERE bucket_id IN ('puentes-fotos','puentes-fotos-staging')
ORDER BY bucket_id,name;
SELECT id,public FROM storage.buckets
WHERE id IN ('puentes-fotos','puentes-fotos-staging');
COMMIT;
```

El cliente existente `photo_storage.PhotoStorage.request` permite descargar cada clave inventariada mediante `GET object/<bucket>/<clave>` con las variables privadas ya indicadas; `PhotoStorage.get(filename)` cubre las fotos finales planas y `PhotoStorage.staged(filename)` los temporales. No usar `tools/migrate_to_supabase.py` como exportador: escribe en el destino. Si se usa un cliente S3 existente, su configuración y acceso deben estar previamente autorizados; no crear claves nuevas para este cierre.

Conservar claves/rutas, tamaño, SHA-256 y metadatos relevantes de **cada objeto inventariado**, incluidas subcarpetas si existen; cotejar especialmente `puentes.photos.filename`. Descargar una URL firmada no convierte el token en respaldo permanente. Verificar copia/restauración en un bucket aislado privado; no cambiar permisos públicos ni borrar objetos. El respaldo PostgreSQL guarda metadatos de Storage, **no sus objetos**. Si no existe exportación recuperable y completa, la publicación queda detenida; este PR no incorpora una nueva integración de backup ni acredita que ya se hizo esa exportación.

## 5. Planificar sin modificar datos

Desde el SHA aprobado, con la variable privada de migración preparada:

```powershell
python tools/rename_reference_identifiers.py --help
python tools/rename_reference_identifiers.py --postgres --schema puentes
if ($LASTEXITCODE -ne 0) { throw 'Plan D7 rechazado; no continuar' }
```

La ausencia de `--apply` devuelve JSON `applied: false` y revierte su transacción. Revisar IDs exactos: normalmente dos campos code de puentes y cuatro de sensores; no hay DDL, nuevos sensores ni cambios de relaciones/mediciones/IDs externos/umbrales/inspecciones/fotos. Conservar el JSON privado. Ensayar primero el plan y aplicación sobre una copia restaurada aislada; no usar la suite `puentes_test` sobre producción. SQLite local tiene una opción diferente: `python tools/rename_reference_identifiers.py --sqlite C:\respaldo\EV3\copia.sqlite`, solo si ese es realmente el origen autorizado; no sustituye el procedimiento PostgreSQL publicado.

## 6. Orden de migración y publicación autorizada

La versión revisada retira cinco columnas. El orden obligatorio sobre el esquema anterior es **inventario → respaldo → D7 → validar PM → retirar columnas → verificar integridad → activar código**. Una instalación nueva ya usa el esquema de 99 columnas. El código actualizado no elimina columnas al iniciar y rechaza esquemas anteriores hasta completar el procedimiento explícito. No basta con cambiar PROJECT_STAGE.

El DSN administrativo de la migración necesita además permisos ALTER sobre las cinco tablas. No ampliar permisos de `puentes_app` para conseguirlo: usar la sesión administrativa autorizada existente. El plan y aplicación se ensayan primero sobre una copia restaurada aislada.


1. Mantener bloqueo de escritores y Cron detenido. Repetir plan contra el inventario definitivo y confirmar respaldo restaurable. Aprobar los seis cambios exactos o confirmar que no hacen falta.
2. **Solo si hace falta D7 y está autorizado**, aplicar y repetir el plan (debe quedar vacío):

```powershell
python tools/rename_reference_identifiers.py --postgres --schema puentes --apply --backup 'C:\respaldo\EV3\puentes-pre-d7.dump'
if ($LASTEXITCODE -ne 0) { throw 'Migración fallida; mantener captura y escritores detenidos' }
python tools/rename_reference_identifiers.py --postgres --schema puentes
```

3. Después de D7, guardar un respaldo PostgreSQL adicional (por ejemplo `puentes-pm-antes-retiro.dump`) y comprobar que es restaurable. Planificar el retiro de columnas y revisar que son exactamente cinco:

```powershell
python tools/retire_legacy_columns.py --postgres --schema puentes
# Solo con autorización de aplicación y respaldo POSTERIOR a D7:
python tools/retire_legacy_columns.py --postgres --schema puentes --apply --backup 'C:\respaldo\EV3\puentes-pm-antes-retiro.dump'
if ($LASTEXITCODE -ne 0) { throw 'Retiro fallido; no activar código ni captura' }
python tools/retire_legacy_columns.py --postgres --schema puentes
```

Comprobar en information_schema: 13 tablas y 99 columnas activas, ninguna `simulated` en bridges/measurements/inspections/rules/alerts. Confrontar conteos/hashes del informe de retiro, las 27 FK, 9 CHECK, 9 UNIQUE, 13 PK, cinco índices explícitos (27 contando índices de PK/UNIQUE), 13 tablas con RLS y sus políticas. Un índice/constraint/política dependiente provoca rollback y requiere revisión, sin CASCADE. Las cinco columnas retiradas solo se recuperan desde respaldo, no se inventan sus valores al revertir.

Comparar inventario/contadores y relaciones con el respaldo: D7 cambia solo los seis códigos aprobados y el retiro elimina solo las cinco columnas autorizadas, preservando el resto. El proveedor nuevo usa PM, el anterior usa DEM: **no reanudar captura ni habilitar usuarios con versiones e inventario incompatibles**. No ejecutar reemplazos masivos en auditoría ni reescribir IDs externos históricos.
4. Confirmar cuenta/proyecto Vercel desde su vinculación privada existente; si esta copia no está vinculada, hacerlo con el operador eligiendo **el proyecto existente**, sin crear otro. Registrar CLI 65.2.0. Cambiar solo `PROJECT_STAGE` de Production a `cutoff_2026_11_28` en Dashboard. Antes comprobar que la variable tiene alcance Production exclusivo: el CLI advierte que actualizar una entrada compartida afecta todos sus entornos. Para una entrada ya exclusiva, el equivalente verificado por `--help` es:

```powershell
'cutoff_2026_11_28' | npx.cmd --yes vercel@65.2.0 env update PROJECT_STAGE --environment production
```

5. Con autorización explícita de publicación, desplegar el SHA revisado como producción sin asignar todavía el dominio estable:

```powershell
npx.cmd --yes vercel@65.2.0 deploy --prod --skip-domain
```

Registrar URL/ID real devuelto y SHA. `--skip-domain` no aísla la base de datos: usa configuración de producción; mantener la ventana y el bloqueo de versiones anteriores. No usar una Preview con credenciales de producción para ensayar. Las pruebas destructivas se ejecutan solo en entornos aislados.
6. Comprobar carga del despliegue candidato y etapa, usando acceso de operador. Tras verificar lo posible sin escrituras y aprobar el paso, asignar el dominio con `npx.cmd --yes vercel@65.2.0 promote <URL_REAL_DEL_DESPLIEGUE>` (sustituir el marcador; no es una URL existente). Verificar el dominio estable y ejecutar los controles autorizados de la sección siguiente antes de reabrir a todos.

No usar `tools/configure_vercel.py` para cambiar solo etapa: reenvía las doce variables privadas. No ejecutar `init-db`, `seed-demo`, `configure-ev2-demo`, `migrate-db`, `tools/migrate_to_supabase.py` ni `sql/postgres.sql`: este cierre requiere únicamente el retiro explícito descrito, sin reinicializar ni importar datos. No tocar bucket, claves, unidades, reglas o umbrales.

## 7. Verificación posterior y reanudación

Registrar fecha real America/Santiago, SHA/URL, etapa y resultados; no reutilizar los resultados aislados como evidencia de producción. Antes de habilitar escrituras, revisar roles y consultas. Las altas de comprobación requieren autorización expresa: usar un entorno de comprobación aislado para valores inválidos y casos destructivos. En producción privilegiar consultas sobre datos existentes y las próximas capturas previstas; no inventar una inspección/actividad real para marcar un caso aprobado.

| Área | Comprobación y resultado esperado |
|---|---|
| DOM | Acceso a reglas/versiones, captura manual/consulta proveedor, alertas y planificación; CSRF y sesión preservados. |
| Inspector | Consulta de panel/alertas/mantenimiento; sin modificar actividades; inspecciones/fotos existentes accesibles. |
| Mantención | Consulta de panel e historial; modifica estado únicamente de sus actividades; no administra reglas ni recepción. |
| Mediciones | Inventario PM coherente, unidades/referencias sin cambios, ambos puentes, filtros y detalles. Próxima recepción sin errores de identidad. Repetir el mismo lote/minuto no duplica lecturas. |
| B-11 | Capturas nuevas válidas evaluadas con regla activa; rechazo auditado de inconsistencias; versiones y alertas históricas conservadas. No forzar valores productivos para disparar alertas. |
| Panel 28/11 | Última lectura por sensor/puente, sin datos explícitos, alertas abiertas y pendientes según rol, enlaces correctos; sin programación. |
| Mantenimiento | Relación puente/componente/alerta/responsable y seguimiento correctos; completar no resuelve alerta. Si no hay actividad autorizada disponible, registrar caso pendiente y comprobarlo en aislado. |
| Alcance | `/inspection-plans` GET/POST bloqueados (404); no se habilita programación. No alterar etapas históricas para probarlas en producción. |
| Conservación | Mismos IDs, contadores históricos, reglas/umbrales y fotos antes de retomar captura; después distinguir altas autorizadas de pérdida/duplicación. |

Si todo está conforme, reactivar **solo el job que estaba activo** antes de la ventana, conservando schedule/comando:

```sql
-- Sustituir ID_REAL_PREVIAMENTE_ACTIVO por el jobid inventariado; no activar otros.
SELECT cron.alter_job(job_id:=ID_REAL_PREVIAMENTE_ACTIVO,active:=true);
```

Observar al menos dos ciclos completos según el intervalo original: `cron.job_run_details` y respuesta HTTP en `net._http_response` deben concordar; HTTP 200 debe contener recepción sin incidencias inesperadas. Un estado SQL succeeded no acredita captura HTTP. Confirmar web disponible y auditoría sin fallos nuevos. Retirar bloqueo de acceso cuando código, etapa, inventario y captura concuerden. No iniciar además un worker local si ya opera Cron.

## 8. Fallos y recuperación sin perder información

- **Falla el plan o apply:** no continuar a publicación ni activar captura. La transacción D7 revierte ante conflicto/error; confirmar inventario, no asumir el resultado por un timeout. Guardar error y volver a planificar en modo lectura. No reintentar con SQL manual sobre códigos personalizados.
- **D7 aplicada y falla el retiro/build/publicación:** mantener congelación. Resolver el despliegue con el código aprobado o preparar un plan de reversión de esos seis códigos con comprobación de colisiones. No hay comando de reversión automática en este PR. El código anterior DEM es incompatible con inventario PM y el código anterior con columnas eliminadas; revertir solo el alias de Vercel no basta. Se necesita recuperación coordinada de esquema, inventario y versión, con preservación de todas las altas posteriores.
- **Código nuevo activo y falla un control:** cerrar acceso y detener captura, guardar logs/cambios posteriores y evaluar corrección o reversión coordinada de versión/etapa/datos. La variable Vercel modificada no reconfigura despliegues antiguos; registrar y restaurar la configuración futura autorizada, sin cambiar secretos.
- **Restauración:** es el último recurso y requiere autorización específica, respaldo íntegro y reconciliación de filas/fotos nuevas desde el punto de respaldo. No restaurar un dump antiguo encima de registros nuevos ni borrar Storage. Ensayar recuperación en aislado; conservar originales y copias previas. Reabrir solo cuando inventario, versión, etapa y captura sean compatibles.

## Referencias y límites de verificación

Comandos locales contrastados con `app.py`, `reference_migration.py`, `tools/rename_reference_identifiers.py`, `tools/configure_vercel.py`, `sql/schedule_iot.sql` y ayuda Vercel 65.2.0. [D7](MIGRACION_REFERENCIAS_D7.md), [informes/evidencias](CIERRE_TECNICO_EV3.md), [entrega individual](ENTREGA_ARIEL_EV3.md). El inventario, respaldo/restauración, bloqueo operativo y publicación del entorno real **no se ejecutaron**.

Documentación oficial consultada para el procedimiento: [backups Supabase, que excluyen los objetos de Storage](https://supabase.com/docs/guides/platform/backups), [pg_cron y alter_job](https://github.com/citusdata/pg_cron), [servicios de conexión PostgreSQL](https://www.postgresql.org/docs/current/libpq-pgservice.html), [deploy --skip-domain](https://vercel.com/docs/cli/deploy), [promote](https://vercel.com/docs/cli/promote). La CLI Supabase v3 cambió el destino por defecto; este plan usa los comandos propios del repositorio y libpq con destino explícito, sin introducir actualización de CLI ni CI/CD.
