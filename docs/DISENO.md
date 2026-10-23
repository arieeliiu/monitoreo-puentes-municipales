# Diseño funcional final

Interfaz municipal: navegación lateral, azul río/estructura, tipografía clara, formularios con validación y una indicación discreta «Entorno de demostración». Sin HU/EDT ni fechas académicas en pantallas. Los datos y supuestos se explican en README, no mediante etiquetas repetidas por registro.

1. Infraestructura → ficha → Tablero/Viga/Estribo → sensores. DOM configura ubicación, variable y referencia de inclinación; códigos únicos y relaciones validadas.
2. Lecturas → consulta automática o manual → historial/detalle. Aceleración vertical pico m/s²; inclinación muestra lectura, referencia y cambio absoluto. Históricos incompatibles y referencias ausentes se informan. Inspecciones visuales → Baja/Media/Alta/Crítica + hallazgo y fotos opcionales → ficha.
3. Reglas → seleccionar puente/variable/nivel/límite inclusivo → guardar versión → nueva lectura genera una única alerta de mayor severidad. Ficha conserva origen, inspecciones, tareas y notas. Cierre explícito DOM.
4. Panel → tarjetas de puentes y lecturas → niveles de alertas, tareas pendientes, próximas inspecciones y últimos hallazgos visuales → detalles/fotos.
5. Mantenimiento → filtro por puente → DOM planifica/asigna → personal asignado actualiza ejecución. Programación de inspecciones → DOM programa → inspector asignado selecciona programación y registra resultado → Realizada y enlace. Crear/completar una tarea nunca cierra una alerta.

Colores de severidad: Atención ámbar, Alerta naranja, Crítico rojo, siempre acompañados por texto. Datos históricos conservan su escala explícita. Las reglas antiguas no se presentan como vigentes para nuevas lecturas.

`tools/build_mockups.py` genera docs/mockups.html desde plantillas reales y SQLite temporal, con inspector para el formulario de resultado. Los botones están desactivados para no escribir desde los bocetos. La UI sigue adaptándose a computadores y tablets; no se declara prueba en hardware físico.

Fechas solo documentales: 24/11/2026 término de EDT 1.4.5/1.4.6 y 26/11/2026 presentación académica.
