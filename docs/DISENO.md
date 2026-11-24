# Diseño funcional final

## Refinamiento integral de interfaz (24/11/2026)

Se conserva la identidad (azul estructura `#153848`, azul río `#146e83`, Bahnschrift/Segoe UI) y se formaliza como sistema de diseño en `static/app.css`: variables de color, superficies, radios, sombras y tipografía; componentes compartidos (encabezado de página, paneles, indicadores, insignias, tablas, listas de registros, línea de tiempo, estados vacíos, diálogos) y adaptación a escritorio, tablet (barra lateral de íconos) y móvil (navegación horizontal y tablas como tarjetas). Las insignias distinguen niveles (severidad, condición: fondo de color) de estados (punto de color) y siempre incluyen texto.

- **Sin recursos externos.** La CSP solo admite archivos propios: íconos SVG en `static/icons/` aplicados como máscaras CSS (así el Inicio del corte 26/10 sigue sin `<svg>`), gráficos dibujados en el servidor o por `static/charts.js`.
- **Panel avanzado.** Indicadores de alertas abiertas por severidad, sensores con lectura válida en 24 h, mantenimiento abierto/vencido y inspecciones de 30 días; estado por puente con la última lectura, la alerta que generó y una tendencia de 7 días; alertas por día (30 días) apiladas por severidad. El orden de los paneles prioriza la tarea de cada rol (Mantención: sus actividades). Todo se calcula con registros existentes.
- **Tendencias.** `GET /api/v1/measurement-series` (solo lectura, cualquier rol autenticado) agrega en SQL el máximo por intervalo de lecturas válidas EV2; en inclinación usa el cambio absoluto evaluado. Muestra los umbrales vigentes cuando las alertas están habilitadas y no interpola intervalos sin datos.
- **Mapa de sensores (ficha del puente).** Esquema 2D genérico, no a escala, generado por `bridge_schematic.py` con los datos existentes: cada sensor se ubica en su componente (Tablero, Viga, Estribo, Pila) con el color de su último estado, la última inspección visual se marca por componente y cada marcador enlaza a la tendencia del sensor. Los registros no tienen coordenadas, por lo que no se dibuja un punto medido; el detalle muestra la ubicación descrita por la DOM. Componentes sin zona equivalente se listan aparte. Precisión por zona o un modelo 3D requieren datos nuevos (posición relativa o planos/BIM) y una solicitud de cambio.
- **Interacción.** Confirmación accesible para desactivar reglas, cancelar programaciones y resolver alertas; protección contra envíos duplicados; avisos descartables; `prefers-reduced-motion` respetado. Los permisos siguen controlándose en el servidor.


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
