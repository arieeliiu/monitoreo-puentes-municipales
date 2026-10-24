# Publicación con Vercel y Supabase

URL estable: https://monitoreo-puentes-municipales.vercel.app

## Componentes y seguridad

- Flask/Jinja se ejecuta en Vercel con Python 3.12. `wsgi.py` expone la aplicación; `pyproject.toml` declara dependencias y copia los recursos a `public/static` durante el build.
- PostgreSQL usa el pooler transaccional de Supabase, usuario limitado `puentes_app`, esquema privado `puentes`, RLS y permisos exclusivos del backend. El navegador no conecta directamente a las tablas. Se conservan sesiones y permisos DOM, Inspector y Mantención de la aplicación; no se reemplaza el login por Supabase Auth.
- TLS verifica el nombre y la cadena con el certificado público oficial de Supabase en `certs/supabase-ca.crt`. `SET LOCAL search_path` se aplica en cada transacción; no hay conexiones ni estados de sesión compartidos entre solicitudes.
- `puentes-fotos` y `puentes-fotos-staging` son buckets privados. DOM/Inspector preparan como máximo cinco fotos y 20 MB totales con CSRF. El navegador sube directamente mediante tokens temporales; el formulario envía solo un manifiesto ligado a la sesión. Flask descarga, valida con Pillow y recodifica a JPEG antes de guardar el registro. Así se evita el límite de 4.5 MB del cuerpo de funciones Vercel.
- La lectura requiere autenticación y un registro fotográfico existente; redirige a una URL firmada de 60 segundos. La clave de servidor permanece en Vercel. Las cargas temporales consumidas se eliminan; Cron limpia las abandonadas de más de cuatro horas por lotes de 100. Un fallo de Storage permite reintentar; los errores manejados de persistencia compensan los objetos finales recién creados.
- Vercel exige PostgreSQL, Storage remoto y una clave de sesión estable: no usa archivos efímeros como almacenamiento permanente. SQLite y fotos locales siguen disponibles fuera de Vercel.

## Variables privadas

Configurar en Production: `DATABASE_URL`, `DATABASE_SCHEMA=puentes`, `SECRET_KEY`, `PHOTO_STORAGE=supabase`, `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `SUPABASE_STORAGE_BUCKET=puentes-fotos`, `PROJECT_STAGE=cutoff_2026_10_26`, `COOKIE_SECURE=1`, `CLOUD_PROVIDER=1` y `CRON_SECRET`.

`tools/configure_vercel.py` envía los valores de `instance/cloud-private.json` por stdin al CLI, sin argumentos con secretos. `instance/`, `.env*` y `.vercel/` están ignorados y excluidos del despliegue. No publicar ese archivo ni la clave de Storage. Crear los buckets privados, el esquema con `sql/postgres.sql` y el usuario limitado mediante una sesión administradora; la aplicación no ejecuta DDL al atender peticiones. Las credenciales del rol se crean fuera del SQL versionado.

## Migración y respaldo

`tools/migrate_to_supabase.py` usa `DATABASE_URL` y la configuración de Storage del entorno. Recibe `--sqlite`, `--photos` y `--report`. Detener primero los escritores del origen y respaldar toda `instance/`. El importador también crea una copia SQLite fechada, comprueba integridad y relaciones, conserva IDs y hashes de contraseñas, verifica cada fila y compara bytes/SHA256 de fotos. Una base destino diferente se rechaza, no se sobrescribe. Requiere temporalmente UPDATE sobre secuencias para `setval`; retirarlo al finalizar, conservando USAGE/SELECT.

La migración real verificada preservó 3 usuarios, 2 puentes, 6 componentes, 4 sensores, 12 mediciones, 18 reglas y 274 eventos de auditoría. El origen no tenía inspecciones ni fotografías. Los casos con fotografías y relaciones pobladas se comprobaron con fixtures separados. El informe privado `instance/MIGRACION_SUPABASE.json` y la copia original quedan en el equipo. Después del cambio, Supabase es la fuente de datos publicada: no volver a importar SQLite sobre registros nuevos. Respaldar periódicamente PostgreSQL y los objetos de Storage por separado; un despliegue de código no es un respaldo de datos.

## Captura periódica

`cloud_provider.py` genera cuatro registros simulados por minuto UTC, uno por tipo y puente DEM-01/DEM-02, con identidad, unidad y fecha/hora. Los IDs externos reproducibles evitan duplicados entre Cron y consulta manual. La recepción conserva validación, auditoría y bloqueo transaccional compartido.

En Vault se guardan `puentes_iot_url` (URL HTTPS seguida de `/internal/iot/pull`) y `puentes_cron_secret` (mismo valor privado que `CRON_SECRET`). `sql/schedule_iot.sql` habilita pg_cron/pg_net y configura `puentes-iot-60s` cada minuto. El endpoint solo acepta POST con Bearer correcto; cada ejecución es independiente y el ciclo siguiente vuelve a intentar después de un fallo. Revisar tanto `cron.job_run_details` como `net._http_response`: una tarea SQL exitosa no prueba por sí sola que HTTP respondió 200.

Para cambiar intervalo, modificar la expresión de `cron.schedule` conservando URL y secreto de Vault; por ejemplo `*/5 * * * *` consulta cada cinco minutos. Para detenerlo, usar `cron.unschedule('puentes-iot-60s')` como administrador. Cambiar etapa requiere actualizar `PROJECT_STAGE` y desplegar; Cron usa esa misma aplicación. En el corte se guarda evaluación pendiente y no se generan alertas. `full` conserva la evaluación EV2 y módulos completos. El proveedor HTTP y worker originales siguen disponibles en modo local.

## Verificación

Se aprobaron 74 pruebas Python (incluidas seis contra PostgreSQL remoto aislado) y siete JavaScript. Las pruebas de PostgreSQL usan `PUENTES_TEST_DATABASE_URL` con el rol `puentes_test` y esquema separado; nunca apuntar esa variable al rol o esquema de producción, porque las fixtures truncan sus propias tablas.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
node --test tests/frontend.test.cjs tests/cloud-uploads.test.cjs
```

Sin `PUENTES_TEST_DATABASE_URL` se omiten las seis pruebas PostgreSQL. La prueba de migración valida filas, hashes, fotografías, secuencias, idempotencia y rechazo de un destino diferente. Las de nube cubren permisos, cargas firmadas, límites, recuperación, deduplicación y corte. Se verificó además una carga real de PNG de 5.9 MB, recodificación, descarga firmada y denegación de acceso público en Storage y base de pruebas; no se agregaron registros ficticios a producción para esa prueba. HTTPS público y las tres cuentas se comprobaron en la aplicación desplegada.

Los planes gratuitos mantienen sus cuotas y condiciones de disponibilidad; no se contrató un plan de pago. La aplicación no necesita procesos locales encendidos.
