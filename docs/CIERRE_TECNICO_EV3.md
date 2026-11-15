# Cierre técnico EV3: revisión Christian Mesa

## Resultado de la implementación

**147 Python (incluidas 20 PostgreSQL aisladas) y 20 JavaScript aprobadas; cero fallos, errores u omisiones**. Ejecución real: 15/11/2026 15:49:06 a 15/11/2026 16:04:02 (America/Santiago). Código probado: `e71352105fd1f5a3d109f273150c22290b6cea1b`. [JSON por caso](evidence/EV3_CHRISTIAN_TEST_RESULTS.json) y [log](evidence/EV3_CHRISTIAN_TEST_RUN.log).

| Corrección solicitada | Implementación y evidencia |
|---|---|
| Contrato SMPMRB v1 | Ocho campos sin simulated; push/pull validados, proveedores actualizados; pruebas Christian y de recepción. |
| Cinco columnas | Retiradas de SQL nuevo; procedimiento explícito schema_revision.py / tools/retire_legacy_columns.py para bases anteriores. 13/99 comprobado en ambos motores. |
| Dependencias | receive/evaluate/API/inspecciones/reglas/alertas y badge sin clasificación; herramientas de inventario sin bridges.simulated; importador rechaza esquemas anteriores. |
| D7 | Firma de puente/sensores/relaciones, sin autorizar por código aislado; funciona antes/después del retiro y rechaza inventario ambiguo. |
| Inicialización | seed-reference-data --confirm-isolated: solo base nueva de pruebas, datos relacionados, rechazo de base ocupada/entorno publicado. Alias demo conservados por compatibilidad. |
| Terminología | Proveedor de referencia en UI, mensajes nuevos y documentación; sin reescribir auditoría anterior. |
| B-11/B-14 | Regresiones completas de captura, reglas/versiones, alertas, panel, mantenimiento, roles, CSRF, fotos y etapas. Completar tarea no resuelve alerta. |
| Informes | Una ejecución principal común; antecedentes resumidos y originales archivados sin reescribir evidencia. |
| Drive | [Traspaso B-01/B-02/B-03](CAMBIOS_PENDIENTES_DRIVE_EV3.md); originales e imágenes inaccesibles no se modificaron. |

## Sustitución de dependencias importantes

| Dependencia anterior | Sustitución actual |
|---|---|
| receive y evaluate | Sin parámetro simulated; INSERT de mediciones/alertas sin la columna; evaluación y severidades originales. |
| POST /api/v1/measurements | Sin validación/argumento de simulación; Bearer, JSON, external_id e identidad relacional conservados. |
| _pull_provider | Sin exigir marca; valida objetos, proveedor configurado e identidad, con savepoints, deduplicación y auditoría. |
| Reglas DOM e inspecciones | INSERT sin clasificación ficticia; versiones, fotos, categorías y permisos conservados. |
| configure_ev2_demo y demo_locations | Inventario de referencia verificado por firma, sensores y relaciones; no consulta bridges.simulated ni sobrescribe ubicaciones manuales. |
| reference_migration y CLI D7 | Verificación del inventario conocido y colisiones; compatibilidad con esquema anterior/nuevo sin leer la columna eliminada. |
| migrate_to_supabase | Fuente y destino deben tener esquema vigente; rechazo explícito del anterior antes de copiar datos. |
| badge y plantillas | Macro de un argumento; llamadas sin simulated y formulario de inspección sin campo oculto. |
| cloud_provider, mock_provider y simulate_iot | Registros con los ocho campos; identificadores PM y contratos de autenticación existentes. |
| schema.sql / postgres.sql y preparaciones EV2 | Instalación sin las cinco columnas; migración destructiva separada, explícita y con respaldo. |

Las menciones restantes de simulated se limitan a detección/retiro del esquema anterior, pruebas negativas/fixtures de compatibilidad y documentos/evidencias históricos. No existe una clasificación sustituta en otra columna.

## Límites, fechas y publicación

Las mediciones provienen del proveedor de referencia; el alcance no incluye sensores físicos (SC-01). No se acredita conexión física, certificación externa, piloto operacional, marcha blanca ni UAT municipal. El token pull es opcional/global y el cliente admite HTTP local; HTTPS obligatorio y credenciales independientes por proveedor siguen pendientes. No se desplegó ni migró producción; SC-04 requiere formalización. PR #1 en borrador, sin fusionar a main. No se cambió producción, credenciales, Cron o Storage. La rama mantiene deshabilitado su despliegue automático. La carpeta B-03 sin seguimiento en la copia original se conserva fuera de este trabajo.

Hitos oficiales: recuperación formal B-11 antes del 15/11/2026; término planificado panel/mantenimiento 24/11/2026; corte 28/11/2026; entrega EV3 30/11/2026. No se declaran cumplidos por ejecutar pruebas. La revisión de Christian del 15/11 es la fuente de requisitos; no se atribuye aprobación de su implementación ni validación posterior de Christian, Alex o la profesora.

Pendientes: actualizar los documentos originales en Drive y sus cinco DER, formalizar SC-04, revisión del equipo y autorización/operación de publicación. [Plan](PLAN_PUBLICACION_EV3.md), [migración](MIGRACION_REFERENCIAS_D7.md), [entrega Ariel](ENTREGA_ARIEL_EV3.md), [verificación y errores reales](VERIFICACION.md).

La limitación de los DER es verificable: no hay fuentes editables de los cinco originales en esta rama; el inventario enlazado permite regenerar 99 columnas/27 FK, pero no se inventó la distribución de columnas en imágenes de Drive no disponibles.

[Resumen anterior íntegro](CIERRE_TECNICO_EV3_HISTORICO_ba0b74e.md).

[Auditoría documental, enlaces, capturas y lista de archivos modificados](evidence/EV3_CHRISTIAN_DOCUMENT_CHECKS.json).
