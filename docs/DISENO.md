# Diseño funcional final

## Actualización de interfaz EV3 para revisión

La identidad existente se conserva: azul estructura `#153848`, azul río `#146e83`, fondo `#f4f7f8`, línea `#cddde2`, texto `#19333e`, tipografía Bahnschrift para títulos y Segoe UI para controles. La franja de Monitoreo diferencia el contexto de navegación de los colores de severidad.

EV3/full muestra un solo enlace lateral Monitoreo y dos enlaces internos con apariencia de pestañas: Mediciones y Alertas. Se usa navegación de documentos con aria-current, no tabs ARIA de contenido dinámico. EV2 conserva Mediciones y las cuatro opciones anteriores. Detalles heredan el estado activo. Reglas y operaciones permanecen separados y solo DOM los ve. Los botones de paginación indican límites y el estado vacío; las fechas de filtro se etiquetan UTC.

La campana visible en los roles autorizados distingue abiertas de no leídas y presenta avisos discretos con enlace. Se conserva el foco visible, texto junto al color, controles nativos y adaptación móvil. Se retiró el rótulo fijo de demostración y las menciones EV2 de los indicadores históricos de presentación; no se alteró el contenido de registros ni el estado de conectividad. [Capturas y límites de revisión](REVISION_EV3_UI.md).

## Pantallas de presentación del corte 26/10/2026

La interfaz predeterminada conserva los estilos existentes y ofrece Inicio (resumen de infraestructura), Infraestructura (fichas y formularios), Mediciones (historial/recepción) e Inspecciones visuales (hallazgos/fotos). Los tres roles ven esas cuatro opciones; las acciones respetan sus permisos. No hay indicadores de alertas, tareas o programación en Inicio ni accesos a esas funciones en fichas. El Inspector registra inspecciones sin selector de programación.

`docs/mockups.html` refleja esas cuatro opciones y los flujos disponibles. `docs/mockups-full.html` conserva los cinco módulos del modo `full`, descritos en los apartados siguientes. Ambos se generan desde plantillas reales con datos temporales; no cambian la base del usuario.


Interfaz municipal: navegación lateral, azul río/estructura, tipografía clara, formularios con validación, sin rótulos fijos de demostración. Sin HU/EDT ni fechas académicas en pantallas. Los datos y supuestos se explican en README, no mediante etiquetas repetidas por registro.

1. Infraestructura → ficha → Tablero/Viga/Estribo → sensores. DOM configura ubicación, variable y referencia de inclinación; códigos únicos y relaciones validadas.
2. Lecturas → consulta automática o manual → historial/detalle. Aceleración vertical pico m/s²; inclinación muestra lectura, referencia y cambio absoluto. Históricos incompatibles y referencias ausentes se informan. Inspecciones visuales → Baja/Media/Alta/Crítica + hallazgo y fotos opcionales → ficha.
3. Reglas → seleccionar puente/variable/nivel/límite inclusivo → guardar versión → nueva lectura genera una única alerta de mayor severidad. Ficha conserva origen, inspecciones, tareas y notas. Cierre explícito DOM.
4. Panel → tarjetas de puentes y lecturas → niveles de alertas, tareas pendientes, próximas inspecciones y últimos hallazgos visuales → detalles/fotos.
5. Mantenimiento → filtro por puente → DOM planifica/asigna → personal asignado actualiza ejecución. Programación de inspecciones → DOM programa → inspector asignado selecciona programación y registra resultado → Realizada y enlace. Crear/completar una tarea nunca cierra una alerta.

Colores de severidad: Atención ámbar, Alerta naranja, Crítico rojo, siempre acompañados por texto. Datos históricos conservan su escala explícita. Las reglas antiguas no se presentan como vigentes para nuevas lecturas.

`tools/build_mockups.py` genera docs/mockups.html desde plantillas reales y SQLite temporal, con inspector para el formulario de resultado. Los botones están desactivados para no escribir desde los bocetos. La UI sigue adaptándose a computadores y tablets; no se declara prueba en hardware físico.

Fechas solo documentales: 24/11/2026 término de EDT 1.4.5/1.4.6 y 26/11/2026 presentación académica.
