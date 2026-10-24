# Correcciones de usabilidad del corte 26/10

## Hallazgos y cambios

1. Sesión/CSRF: se reprodujo un 400 al recibir la cookie de un GET anónimo a `/favicon.ico` después del GET de login, antes de enviar su formulario. `prepare()` inicializaba una sesión para cualquier ruta, incluso 404 y recursos. Ahora únicamente un GET de login o una página autenticada inicia el token; las respuestas anónimas auxiliares no emiten cookies. Login sigue borrando la sesión y rotando el token, logout la elimina. Tokens ausentes, incorrectos o anteriores se rechazan. El error ofrece un enlace GET para volver al formulario; jamás reenvía el POST. Se conserva Secure/SameSite y no se modifica SECRET_KEY ni variables de Vercel. Esta reproducción demuestra una causa posible; no prueba que todos los 400 previamente observados tuvieran ese origen. Los formularios abiertos antes de cambiar de usuario deben volver a cargarse.
2. Sensores: el historial recibe el puente real mediante componentes y reconstruye las opciones del selector al cambiar de puente. No usa prefijos, ni depende de `hidden` en opciones. Conserva selección compatible, reinicia a Todos si corresponde y mantiene las restricciones SQL combinadas. El registro manual es independiente.
3. Filtros: panel nativo details/summary compacto, cerrado sin filtros y abierto con filtros activos. Conserva selecciones y fechas, consulta GET en servidor y enlace para limpiar. El historial mantiene columnas y límite de 500 por consulta.
4. Navegación: el historial enlaza cada detalle; este obtiene bridge_id por sensor/componente y enlaza `/inspections?bridge_id=...`. La ruta existente mantiene el historial vacío o las inspecciones de ese puente y sus detalles/fotos. No se crea relación entre medición e inspección.
5. Fecha/hora: controles date/time obligatorios; `pilot_time.py` interpreta America/Santiago mediante ZoneInfo, comprueba ambos folds y el recorrido de vuelta desde UTC. Rechaza horas inexistentes y ambiguas y fechas futuras o inválidas; almacena UTC. `tzdata` se declara en ambos manifiestos para Windows. Los POST antiguos con ISO zonificado y el contrato API/IoT siguen funcionando. No hay conversiones de históricos ni cambios de esquema. Referencia: https://docs.python.org/3.12/library/zoneinfo.html

## Verificación y límites

Las regresiones de `tests/test_usability.py` cubren la carrera de cookies, login de los tres roles, rotación y rechazo de tokens, primer POST legítimo, filtros persistidos e incompatibles, enlaces, historial vacío, fotografías, permisos y corte. Comprueban enero UTC-03, junio UTC-04 y horas de transición de abril/septiembre de 2026. `tests/frontend.test.cjs` verifica reconstrucción de opciones. Dos escenarios adicionales se ejecutan sobre el esquema restringido `puentes_test` de PostgreSQL; nunca sobre producción.

En navegador local aislado se verificaron login, panel cerrado/apertura/cierre, selección de sensores por puente, registro manual y conversión UTC, detalle e inspección ingresada desde controles nativos. La comprobación de producción debe limitarse a login, consultas y filtros: no crear mediciones/inspecciones de prueba en producción. Los logins generan su auditoría habitual y la captura periódica continúa agregando mediciones; no se modifica esa integración.

Los datos, contraseñas, sensores, unidades, umbrales y secretos existentes se conservan. Continúa `cutoff_2026_10_26` con Inicio, Infraestructura, Mediciones e Inspecciones visuales; las rutas futuras permanecen bloqueadas. No se han modificado documentos académicos.

Resultado: 80 pruebas Python (ocho PostgreSQL aisladas) y ocho JavaScript aprobadas. La carga real de PNG de 5.9 MB con fecha/hora separadas pasó en el bucket privado de pruebas, incluida recodificación, descarga firmada y rechazo de Mantención.


## Componente estructural en Mediciones

El panel de filtros añade `component_id` entre puente y sensor. Todos los componentes proceden de `components`; cada opción conserva su `bridge_id`. Los sensores conservan `component_id` y el puente obtenido por JOIN. JavaScript reconstruye opciones, reinicia selecciones incompatibles y permite consultar toda la infraestructura sin puente. Un componente sin lecturas conserva el estado vacío existente. La consulta SQL combina las restricciones de puente/componente/sensor y el historial muestra el nombre del componente junto al sensor.

El registro manual usa Puente → Componente estructural → Sensor y envía el `sensor_code` original. El servidor verifica la pertenencia de componente al puente y sensor al componente antes de recibir la lectura. Los POST anteriores sin selectores de contexto conservan el contrato de sensor_code; cuando se envía cualquiera de esos selectores ambos son obligatorios y deben coincidir. API y proveedor IoT conservan sus contratos y validaciones. No hay cambios de esquema, datos, sensores, umbrales, unidades ni asociaciones; Inspecciones visuales conserva su selector.

Las regresiones están en `tests/test_measurement_components.py`, `tests/frontend.test.cjs` y un caso PostgreSQL con el rol/esquema aislado existentes en `tests/test_cloud.py`. Cubren componentes de ambos puentes, códigos de sensor ajenos a los prefijos del piloto, selecciones incompatibles, filtros persistidos, consulta sin puente, estados vacíos, registro manual y permisos.

Resultado de esta ampliación: 84 pruebas Python (nueve PostgreSQL aisladas) y diez JavaScript aprobadas. En navegador local se comprobó la cadena DEM-02 → Tablero → inclinación, la unidad automática y el guardado en la base aislada, así como el filtro por componente y el historial vacío.


## Acciones superiores de DOM en Mediciones

Registrar medición manual y Consultar proveedor se muestran inmediatamente bajo el encabezado, antes de filtros e historial. El botón principal abre/cierra el único formulario existente, inicialmente oculto, con aria-expanded y aria-controls. El botón secundario conserva el POST a /provider/pull y CSRF. Inspector y Mantención conservan únicamente filtros, historial y detalles. No cambian recepción, proveedor, periodicidad, permisos, etapa ni datos. En navegador local se verificaron apertura/cierre, lectura válida guardada, vibración negativa rechazada y consulta simulada con cuatro lecturas recibidas.

Verificación de la reorganización: 85 pruebas Python y diez JavaScript aprobadas, incluidas nueve PostgreSQL aisladas y la regresión de orden/visibilidad/CSRF/permisos existentes.
