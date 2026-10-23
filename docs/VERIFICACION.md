# Verificación de la versión corregida

Fecha: 23/10/2026. Instalación verificada: carpeta `Desktop/puentes`.

## Resultado automatizado

Comando: `.venv/Scripts/python.exe -m unittest discover -v`

**36 pruebas aprobadas, 0 fallos; ejecución completa actual: 74,616 segundos.** Se conservan 18 casos de regresión (la prueba de reglas oficiales se adaptó al nuevo requisito académico y la de sensores aporta ubicación obligatoria) y se agregan 11 casos de la corrección anterior y 7 casos de umbrales, captura automática, identidad IoT y mockups. No se cuentan ejecuciones duplicadas por herencia.

- Infraestructura: alta/edición, unicidad, validaciones, ubicación de sensor y variable visible.
- Tres roles: controles de servidor, datos de mantenimiento asignados, programación DOM y resultado solo por inspector asignado.
- Mediciones e inspecciones: historial, valores inválidos/no disponibles, fotos válidas/inválidas, CSRF, escape HTML y persistencia.
- Reglas: numéricas y visuales, inclinaciones positivas/negativas, gt/lt/abs_gt, límites exactos, supuesto académico y aviso individual sin regla.
- Panel: cinco funcionalidades navegables, datos disponibles/ausentes, pendientes, programación y últimos hallazgos con enlaces a fotos.
- Mantenimiento: filtro por puente, responsable, ejecución, relación con alertas y cierre explícito DOM.
- Programación: estado, cancelación, validación de puente/componente, resultado único y rechazo de inspector no asignado.
- IoT: servidor HTTP independiente en puerto efímero, cliente real, lote para ambos puentes, mediciones/alertas persistidas, duplicados y registro inválido aislado. Se prueba desconexión y servidor HTTP 503 que responde correctamente al tercer intento.
- Migración: idempotencia, conservación tabla por tabla y apertura de base con esquema anterior.

## Conservación de la instalación existente

Se creó respaldo SQLite antes de migrar, dentro de `instance/` (excluido de Git). Se compararon los valores de todas las columnas previas y filas de todas las tablas después de migrar: 3 usuarios, 2 puentes, 2 componentes, 4 sensores y 2 operaciones de auditoría conservados. No había mediciones, inspecciones, reglas, alertas ni tareas en esa base al migrar; no se atribuye conservación de datos que no existían. La suite sí prueba la migración con esas entidades pobladas. Se verificó igualdad de archivos fotográficos (0 en esta instalación), `integrity_check=ok` y `foreign_key_check` sin errores. Informe local: `instance/MIGRACION_VERIFICADA.json`.

Servidor corregido iniciado con Waitress; GET `/login` respondió HTTP 200. El cotejo de pantallas y permisos se realiza con el cliente HTTP de Flask; no se afirma una nueva revisión visual en tablets físicas. `panel-verificado.png` corresponde al diseño de la versión inicial, no acredita las correcciones actuales.

## Cobertura oficial y límites

Se cotejó la transcripción `CRITERIOS_OFICIALES.md`: 57 CA de HU-01 a HU-07 con evidencia individual; CA-04.2 dentro del supuesto académico explícito. Los 8 CA de HU-08 se documentan únicamente para el entorno simulado; no hay especificaciones ni conectividad de hardware/proveedor real verificadas. HU-09 permanece pendiente (aceptación municipal, piloto operacional, capacitación y cierre).

Término planificado de EDT 1.4.5 y 1.4.6: **24/11/2026**. Objetivo de presentación académica: **26/11/2026**. No se modifica la línea de base.


## Captura automática, contrato extendido y mockups

- `test_vibration_nonnegative_finite_threshold`: rechazo sin insertar para negativos, no numéricos y no finitos; acepta cero/positivos y conserva inclinación direccional negativa.
- `test_provider_rejects_inconsistent_and_missing_identity_with_evidence`: HTTP independiente con ambos puentes, identidades coherentes/incoherentes, campos ausentes, error persistente accesible en auditoría y duplicados sin nuevas filas.
- `test_optional_api_identity_is_validated_without_breaking_legacy`: API receptora compatible, con validación de identidad cuando se suministra.
- `test_provider_default_json_includes_two_bridges_and_types`: lote generado del proveedor con identificador de ambos puentes, ambas variables y marca de simulación.
- `test_automatic_worker_recovers_and_deduplicates_real_http`: ejecuta el comando CLI con el bucle periódico real y servidor HTTP real; sustituye solo las esperas por un reloj controlado para verificar tres ciclos sin ralentizar la suite. Primer ciclo desconectado, posteriores recuperados, una medición y error auditado; consulta manual conservada y web operativa. El cliente HTTP y sus reintentos se verifican además en la regresión existente.
- `test_worker_interval_environment_lock_and_bad_json`: intervalo inválido, configuración por entorno, singleton liberable y JSON inválido sin reintentos inútiles.
- `test_mockups_cover_current_real_views`: cinco secciones, programación y selección por inspector, pendientes, condiciones visuales, ubicación de sensores y consultas IoT; sin formularios que escriban en la aplicación.

Los mockups se regeneraron desde plantillas reales usando SQLite temporal (`tools/build_mockups.py`). No se realizó una nueva revisión visual en tablet física. El servidor web se reinició con la versión corregida y respondió HTTP 200. El worker de producción local se inicia explícitamente con `start-iot.ps1` o `poll-provider`, independiente de la web; no se declara un servicio permanente instalado. URL e intervalo están documentados en README.

Esta actualización no cambia el esquema ni borra datos. Se creó respaldo local `backup-antes-iot-*.sqlite` excluido de Git. Se compararon todas las filas de la base respaldada con las posteriores a la actualización. Las pruebas usan sus propias bases temporales. Se mantienen los supuestos académicos y las fechas de línea de base.
