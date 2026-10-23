# Diseño funcional y navegación

Usuarios: DOM administra y planifica; Inspector registra hallazgos; Mantención ejecuta tareas asignadas. Todas las rutas requieren autenticación salvo acceso y recepción API, que usa clave independiente.

Dirección visual: azul río `#146e83`, azul estructura `#153848`, agua clara `#e9f3f6`, fondo `#f4f7f8`, tinta `#19333e`, ámbar de atención `#956417`. Bahnschrift para títulos, Segoe UI para controles y Consolas para identificadores/datos. El dibujo de tablero y arcos remite a la infraestructura monitoreada; no representa la geometría real de los puentes. Navegación lateral en computador y horizontal en tablet estrecha. Etiquetas y foco visibles, sin dependencia de animaciones.

Abrir `mockups.html` para cinco bocetos navegables. Los bocetos usan los mismos nombres de campos y acciones que las pantallas implementadas; son documentación estática, sin persistencia. La aplicación ejecutable constituye el prototipo funcional final.

| Funcionalidad | Flujo y rutas | Validaciones / salida |
|---|---|---|
| Infraestructura | Panel → Infraestructura `/bridges` → Registrar puente → Ficha `/bridges/<id>` → componentes → sensores → editar | Identificador único, campos completos, sensor del componente; errores visibles, permanencia de datos |
| Captura | Mediciones `/measurements` → abrir entorno local → sensor/valor/unidad/fecha/estado → guardar → historial; Inspector → Inspecciones `/inspections` → puente/componente/condición/hallazgo/fotos → ficha `/inspections/<id>` | Unidades y fecha válidas, no disponibles diferenciados, imágenes verificadas, componente del mismo puente |
| Alertas | DOM → Reglas `/rules` → crear regla → nueva recepción/inspección dispara evaluación → Alertas `/alerts` → ficha `/alerts/<id>` | Identificación de pruebas, umbral finito, condición visual exacta, referencia de especialista si oficial, registro de origen |
| Panel | Inicio `/` → tarjetas por puente → ficha / historial de sensores / historial visual → fotos; lista de alertas → detalle | Sin datos explícito, última medición por fecha, alertas activas/en atención; no presenta ausencia como normal |
| Mantenimiento | DOM → Mantenimiento `/maintenance` → puente/componente/alerta/responsable/fecha/descripción → crear; Mantención → actividades asignadas → cambiar ejecución; DOM → alerta → nota/inspección → cierre explícito | Personal de mantención, relaciones del mismo puente, fecha válida, permisos y auditoría; tarea no cierra alerta |

Estados: tarea `Pendiente → En ejecución → Completada`; se permite corrección de estado por quien tiene permisos y queda auditoría. Alerta `Activa / En atención / Resuelta`, seleccionada explícitamente por DOM con nota. Inspector puede agregar notas y asociar inspecciones, sin cambiar estado.

Datos de demostración inicial: dos puentes ficticios y sensores sin mediciones; el panel comienza con ausencia de datos. No se simulan inspecciones, umbrales ni alertas sin una acción explícita de prueba.
