# Verificación de la versión corregida

Fecha: 23/10/2026. Instalación verificada: carpeta `Desktop/puentes`.

## Resultado automatizado

Comando: `.venv/Scripts/python.exe -m unittest discover -v`

**29 pruebas aprobadas, 0 fallos; ejecución completa: 60,874 segundos.** Se conservan 18 casos de regresión (la prueba de reglas oficiales se adaptó al nuevo requisito académico y la de sensores aporta ubicación obligatoria) y se agregan 11 casos de correcciones. No se cuentan ejecuciones duplicadas por herencia.

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
