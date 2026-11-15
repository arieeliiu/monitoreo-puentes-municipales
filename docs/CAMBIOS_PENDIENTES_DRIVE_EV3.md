# Traspaso técnico: correcciones pendientes en Drive EV3

## Estado y fuente de verdad

Se implementó en código la opción A solicitada en la revisión de Christian Mesa del **15/11/2026**. Versión técnica candidata: `e713521`, rama `feature/ev3-cierre-tecnico`, PR #1. Este documento prepara cambios de B-01/B-02/B-03; **no se accedió a Google Drive ni se modificaron sus originales o imágenes**. No se atribuyen firmas, aprobaciones o revisiones adicionales al equipo o a la profesora.

Las mediciones provienen del proveedor de referencia; el alcance no incluye sensores físicos (SC-01). Las conexiones físicas, predicción, piloto, marcha blanca, capacitación y UAT están fuera de este trabajo. La corrección técnica no cierra SC-04: falta su registro/formalización correspondiente.

Fuentes: [SQL PostgreSQL definitivo](../sql/postgres.sql), [inventario de 99 columnas y FK](evidence/EV3_CHRISTIAN_SCHEMA.json), [verificación](VERIFICACION.md), [migración D7 y retiro](MIGRACION_REFERENCIAS_D7.md). Los resultados de pruebas se identifican en los cuatro informes, sin presentar ensayos anteriores como nuevos.

## B-01: estándar de interoperabilidad

| Ubicación / tema original | Corrección que debe aplicar el equipo |
|---|---|
| Sección 5.2 | Sustituir `PM-001-VIB-01` por `PM-001-VIBRACION`. |
| Nivel semántico | Sustituir «identidad sensor–componente–puente» por «identidad de sensor, componente y puente». |
| Contrato SMPMRB v1 | Ocho campos: external_id, bridge_code, sensor_code, kind, unit, value, measured_at y status; `simulated` no forma parte del contrato. |
| Identificadores | PM-001, PM-002; PM-001-VIBRACION, PM-001-INCLINACION, PM-002-VIBRACION, PM-002-INCLINACION. |
| Estados y unidades | valido / invalido / no_disponible; vibración m/s² e inclinación °. Mantener el significado y umbrales existentes. |
| Sección 9: «Consulta externa» | Retirar la brecha específica de exigir `simulated`: push y pull ya admiten registros conformes sin esa marca, con validación relacional. No afirmar conexión física. |
| Brechas aún vigentes | Push mantiene un Bearer IOT_API_KEY; pull usa URL y token global opcional. No existe gestión de credenciales independiente por proveedor, el cliente admite HTTP local sin imponer HTTPS, y no se acreditó conformidad/certificación de un tercero ni UAT. Mantener esas limitaciones. |
| Formato | Corregir jerarquía de subsecciones y títulos; usar versión técnica `e713521` como candidata revisable, sin inventar aprobación o firmas. |

## B-02: diagramas de arquitectura

1. Diagrama 01, caja central: **SMPMRB: aplicación municipal**.
2. Diagrama 03, proveedor: **cloud_provider.py (proveedor de referencia) dentro del proceso**. Esta es la variante de nube; el proveedor HTTP local `mock_provider.py` sigue siendo un proceso separado.
3. Diagramas 01 y 02: dejar pendiente la referencia Git de `main` hasta que exista un commit final integrado y se pueda verificar su SHA. `e713521` identifica código candidato de la rama, no una integración ya realizada.
4. Mantener contexto, contenedores y despliegue, distinguiendo local/pruebas y la arquitectura Vercel/Supabase. Las pruebas de esta revisión se hicieron en SQLite temporal y PostgreSQL aislado, no publicando el nuevo código.
5. Distinguir conexiones implementadas (HTTP de referencia, Flask, BD, Storage) de objetivos futuros. No dibujar sensores físicos conectados como implementación existente ni una integración de hardware fuera de SC-01.

Las imágenes originales de Drive no están actualizadas por este PR. No se encontraron fuentes versionadas editables de esos diagramas en la rama; los cambios de sus cajas y referencias deben hacerse en su fuente original.

## B-03: diseño de base de datos

### Modelo definitivo activo

| Elemento | Conteo / tratamiento |
|---|---|
| Tablas | 13, sin crear ni eliminar entidades. |
| Columnas | 99 activas; anteriormente 104. |
| Columnas retiradas | bridges.simulated, measurements.simulated, inspections.simulated, rules.simulated, alerts.simulated. No hay columna sustituta. |
| FK | 27. |
| CHECK | 9. |
| UNIQUE | 9, independientes de las PK. |
| PK | 13. |
| Índices PostgreSQL | 5 explícitos; 27 en total contando los asociados a PK/UNIQUE. No confundir ambas cifras. |
| RLS / políticas | 13 tablas habilitadas y 13 políticas backend_access en el SQL de instalación; la migración conserva las existentes. |

Los conteos proceden del SQL definitivo y del catálogo de pruebas. No describen una migración ya ejecutada en producción. SQLite mantiene los mismos campos y relaciones; sus índices de PK INTEGER usan rowid y no deben contarse como índices PostgreSQL.

### Diccionario y regeneración de los cinco DER

Eliminar las cinco filas del diccionario y cualquier representación de esas columnas en **cada uno de los cinco DER** donde aparezcan. Conservar entidades, PK, FK, cardinalidades, estados y restricciones restantes; no inventar una nueva relación o marca de origen. La secuencia para bases anteriores es D7 antes del retiro de columnas; no presentar el DROP como actualización automática al arrancar.

| Tabla | Columnas activas | Trazabilidad solicitada |
|---|---:|---|
| users | 4 | Soporte transversal HU-01/HU-03/HU-07; RNF-2 y RNF-4. |
| bridges | 5 | HU-01, CA-01.1 a CA-01.8; RF-1. |
| components | 3 | HU-01; HU-08, CA-08.2/08.6; RF-1. |
| sensors | 8 | Conservar trazabilidad original, cotejando el SQL final. |
| measurements | 13 | Conservar trazabilidad original de captura e interoperabilidad, sin fila simulated. |
| inspections | 8 | HU-03, CA-03.1 a CA-03.8; HU-07; RF-3. |
| photos | 3 | HU-03, evidencia opcional; RF-3. |
| rules | 13 | Conservar trazabilidad original de reglas/versiones, sin fila simulated. |
| alerts | 9 | Conservar trazabilidad original de alertas/seguimiento, sin fila simulated. |
| alert_notes | 6 | Conservar trazabilidad original de seguimiento. |
| tasks | 10 | HU-06, CA-06.1 a CA-06.8; HU-07, CA-07.4/07.8; RF-6 y RF-7 parcial. |
| audit | 7 | RNF-3 y RNF-4. |
| inspection_plans | 10 | Estructura disponible; funcionalidad no comprometida en EV3. |

El inventario JSON enlazado enumera los 99 nombres de columna y las 27 FK por tabla; los tipos/restricciones PostgreSQL se toman de `sql/postgres.sql`. No hay fuentes editables de los cinco DER versionadas en esta rama. Al no disponer de las imágenes originales, no se puede atribuir qué columna aparece en cuál vista: el operador debe retirar las apariciones indicadas en todas las vistas aplicables y regenerarlas desde el SQL. Este límite queda explícito; no se inventan cinco diagramas originales ni se declara que fueron modificados.

### Formato del documento original

- Mantener los títulos originales 4.4, 4.5 y 4.6, sustituyendo su separador por guion simple.
- Sustituir guiones largos de celdas vacías por «No aplica» o por vacío, según el dato.
- Escribir rangos «CA-01.1 a CA-01.8» y «R01 a R27».
- En conclusión, explicar la eliminación de las cinco columnas y la sustitución de sus dependencias por el contrato v1 y validación del inventario. No afirmar que existe otra marca de simulación ni que el cambio acredita dispositivos físicos.
- Referenciar esquema `sql/postgres.sql`, versión candidata `e713521` y 13/99. Actualizar la referencia de integración a main únicamente cuando ese hecho ocurra y se verifique.

## Acciones manuales que siguen pendientes

Aplicar estas correcciones en los originales de Drive, regenerar sus imágenes y someterlos al flujo de revisión del equipo. Mantener hitos oficiales: recuperación formal B-11 antes del 15/11/2026; término planificado de panel/mantenimiento 24/11/2026; corte 28/11/2026; entrega EV3 30/11/2026. No se modifican fechas originales de la EDT ni se declaran cumplidas con el código o las pruebas. Publicación y migración productiva permanecen pendientes de autorización y ejecución coordinada.
