# Criterios de aceptación — Sistema de Monitoreo de Puentes Municipales

**Fuente:** Documento del proyecto «Historias de usuario, casos de uso y criterios de aceptación»:
https://docs.google.com/document/d/1ja_t-6dj9pqzESgQG7QOb_pUikvg-5bXB1UMHsMqEyI/edit

**Uso:** Transcripción de los criterios del documento HU/CU para que Codex pueda contrastarlos con el código sin acceder a Google Drive. El alcance de la implementación prevista al 26/11/2026 comprende HU-01 a HU-07 y el entorno simulado de integración HU-08. HU-09 corresponde a pruebas de aceptación y entrega posteriores, y está incluida solo como referencia documental.

> **Nota académica:** Las magnitudes y umbrales de sensores pueden utilizar valores asumidos/simulados para la demostración, identificándolos como tales. Esta transcripción no acredita que exista una contraparte estructural, un proveedor IoT o una conexión real.

## HU-01 — Registrar infraestructura municipal (EDT 1.4.2)

Como DOM, quiero registrar y consultar los puentes municipales, para mantener centralizada la información de la infraestructura que requiere monitoreo.

- **CA-01.1:** El sistema permite registrar un puente con la información requerida por el proyecto.
- **CA-01.2:** El sistema valida que los campos obligatorios estén completos.
- **CA-01.3:** El sistema identifica cada puente mediante un identificador único.
- **CA-01.4:** El sistema permite consultar los puentes registrados.
- **CA-01.5:** El sistema permite visualizar la información asociada a un puente seleccionado.
- **CA-01.6:** El sistema permite modificar información de un puente cuando el usuario tiene los permisos correspondientes.
- **CA-01.7:** El sistema informa cuando se intenta registrar un puente con datos obligatorios incompletos.
- **CA-01.8:** El sistema evita duplicar registros cuando se detecta que el puente ya se encuentra registrado.

## HU-02 — Consultar mediciones de sensores (EDT 1.3 y 1.4.3)

Como inspector municipal, quiero consultar las mediciones de vibración e inclinación recibidas desde los sensores, para conocer las condiciones registradas en los puentes monitoreados.

- **CA-02.1:** El sistema permite consultar las mediciones asociadas a un puente.
- **CA-02.2:** Cada medición se encuentra asociada al sensor y puente correspondiente.
- **CA-02.3:** El sistema muestra el tipo de medición recibida.
- **CA-02.4:** El sistema muestra el valor registrado y su fecha y hora.
- **CA-02.5:** El sistema permite distinguir las mediciones recibidas de aquellas que presentan errores o no están disponibles.
- **CA-02.6:** El sistema informa cuando no existen mediciones disponibles para el puente seleccionado.
- **CA-02.7:** El sistema permite consultar mediciones anteriores cuando se encuentran almacenadas.
- **CA-02.8:** El sistema no presenta como válida una medición que no haya superado las validaciones de recepción definidas.

## HU-03 — Registrar inspecciones visuales (EDT 1.4.3)

Como inspector municipal, quiero registrar observaciones visuales sobre el estado de un puente, para complementar las mediciones de los sensores con información obtenida en terreno.

- **CA-03.1:** El sistema permite seleccionar el puente inspeccionado.
- **CA-03.2:** El sistema permite registrar la fecha de inspección.
- **CA-03.3:** El sistema permite ingresar observaciones sobre el estado observado.
- **CA-03.4:** El sistema valida que la información obligatoria esté completa.
- **CA-03.5:** El sistema asocia la inspección con el puente correspondiente.
- **CA-03.6:** El sistema permite consultar inspecciones previamente registradas.
- **CA-03.7:** El sistema identifica la inspección mediante un registro individual.
- **CA-03.8:** El sistema informa al usuario cuando no se puede guardar una inspección por falta de información obligatoria.

**Aclaración:** Los CA no exigen fotografías obligatorias. El prototipo las admite como evidencia opcional; no reemplazan la descripción de la observación.

## HU-04 — Generar alertas por umbrales (EDT 1.4.4; 1.3.2)

Como DOM, configurando reglas con valores ya definidos por la contraparte técnica, quiero que el sistema identifique mediciones que superen los umbrales configurados, para detectar situaciones que requieren revisión o seguimiento.

- **CA-04.1:** El sistema permite configurar reglas de alerta para los tipos de medición contemplados.
- **CA-04.2:** Cada regla utiliza umbrales definidos o validados por la contraparte técnica.
- **CA-04.3:** El sistema compara las mediciones recibidas con las reglas configuradas.
- **CA-04.4:** Cuando una medición cumple una condición de alerta, el sistema genera el registro correspondiente.
- **CA-04.5:** La alerta queda asociada al puente y a la medición que la originó.
- **CA-04.6:** El sistema muestra la fecha y hora de generación de la alerta.
- **CA-04.7:** El sistema permite consultar las alertas generadas.
- **CA-04.8:** El sistema informa cuando no existen reglas configuradas para evaluar una medición.
- **CA-04.9:** El sistema no presenta la alerta como un diagnóstico estructural ni como una decisión automática sobre la seguridad del puente.

**Aclaración académica:** Para la demostración, documentar explícitamente que los valores de umbral son **supuestos de la contraparte dentro de un escenario simulado**. No afirmar que fueron validados realmente ni convertirlos en recomendaciones técnicas de seguridad.

## HU-05 — Visualizar el panel de monitoreo (EDT 1.4.5)

Como usuario del sistema (DOM, inspector municipal o personal de mantención vial), quiero visualizar un panel con información de los puentes, mediciones y alertas, para revisar de manera centralizada el estado de monitoreo de la infraestructura.

- **CA-05.1:** El panel permite visualizar los puentes registrados.
- **CA-05.2:** El usuario puede seleccionar un puente para consultar su información.
- **CA-05.3:** El panel muestra las mediciones disponibles asociadas al puente seleccionado.
- **CA-05.4:** El panel permite identificar las alertas generadas.
- **CA-05.5:** La información mostrada corresponde a los registros disponibles en el sistema.
- **CA-05.6:** El sistema informa cuando no existen mediciones o alertas para mostrar.
- **CA-05.7:** El panel permite distinguir los datos de medición de las observaciones visuales.
- **CA-05.8:** El usuario puede acceder desde el panel a la información relacionada con el puente seleccionado.

**Requisito adicional del caso original:** El panel muestra estado de los puentes, alertas activas y tareas pendientes.

## HU-06 — Planificar actividades de mantenimiento (EDT 1.4.6)

Como DOM (planifica y asigna), quiero registrar y consultar actividades de mantenimiento asociadas a los puentes, para organizar las acciones que deben realizarse y mantener su seguimiento.

- **CA-06.1:** El sistema permite registrar una actividad de mantenimiento asociada a un puente.
- **CA-06.2:** El sistema permite ingresar la información requerida para identificar la actividad.
- **CA-06.3:** El sistema permite registrar una fecha planificada.
- **CA-06.4:** El sistema permite consultar las actividades de mantenimiento registradas.
- **CA-06.5:** El sistema permite identificar a qué puente corresponde cada actividad.
- **CA-06.6:** El sistema permite modificar la información de una actividad según los permisos del usuario.
- **CA-06.7:** El sistema informa cuando faltan datos obligatorios para registrar una actividad.
- **CA-06.8:** El sistema permite consultar las actividades relacionadas con un puente seleccionado.

## HU-07 — Realizar seguimiento de alertas y acciones (EDT 1.4.4, 1.4.5, 1.4.6)

Como DOM, quiero consultar las alertas y relacionarlas con inspecciones o actividades de mantenimiento, para mantener la trazabilidad desde la detección de una situación hasta su revisión o atención.

- **CA-07.1:** El sistema permite consultar una alerta y la medición que la originó.
- **CA-07.2:** El sistema permite identificar el puente asociado a la alerta.
- **CA-07.3:** El sistema permite relacionar una alerta con una inspección registrada.
- **CA-07.4:** El sistema permite relacionar una alerta con una actividad de mantenimiento cuando corresponda.
- **CA-07.5:** El sistema permite consultar la información vinculada a una alerta.
- **CA-07.6:** El sistema conserva la relación entre alerta, puente y acción asociada.
- **CA-07.7:** El sistema informa cuando una alerta no tiene una inspección o actividad asociada.
- **CA-07.8:** El sistema no marca una alerta como resuelta únicamente por haber generado una actividad de mantenimiento.

## HU-08 — Validar la integración con sensores existentes (EDT 1.3.1–1.3.5 y 1.5.2.6)

Como equipo de desarrollo (Ariel y Christian), quiero verificar que el sistema pueda recibir correctamente los datos desde la plataforma IoT existente, para asegurar que las mediciones se incorporen al sistema de monitoreo de forma consistente.

- **CA-08.1:** Se documentan las especificaciones disponibles de los sensores y de la plataforma IoT.
- **CA-08.2:** Se verifica la correspondencia entre los sensores y los componentes de la infraestructura.
- **CA-08.3:** Se configura el acceso a la API del proveedor de acuerdo con las condiciones disponibles.
- **CA-08.4:** Se ejecutan pruebas de conectividad con la plataforma existente (1.3.5).
- **CA-08.5:** Se comprueba que los datos recibidos correspondan al formato esperado por el sistema.
- **CA-08.6:** Se verifica que las mediciones recibidas puedan asociarse al puente y sensor correspondientes.
- **CA-08.7:** Se registran los resultados de las pruebas de integración.
- **CA-08.8:** Se documentan los errores o limitaciones detectados durante la validación.

**En este ejercicio:** Si se crea una API que simula la del proveedor, dejar claro que la prueba valida el entorno simulado, no un proveedor real.

## HU-09 — Aceptar y entregar el sistema a operaciones (EDT 1.5.3 y 1.6)

Como DOM, quiero participar en las pruebas de aceptación y revisar el sistema junto con la documentación correspondiente, para verificar que los entregables acordados estén disponibles antes del cierre del proyecto.

- **CA-09.1:** Se ejecutan pruebas de aceptación para las cinco funcionalidades principales.
- **CA-09.2:** Se documentan los resultados de las pruebas realizadas.
- **CA-09.3:** Se registran los defectos o ajustes identificados.
- **CA-09.4:** Se realizan los ajustes acordados para el piloto.
- **CA-09.5:** Se ejecuta el piloto operacional contemplado en el proyecto.
- **CA-09.6:** Se realiza la capacitación de los usuarios definidos, incluyendo inspectores, personal de mantención vial y DOM.
- **CA-09.7:** Se entrega la documentación operativa acordada.
- **CA-09.8:** La aceptación final y la firma corresponden al Patrocinador (Municipalidad), según el procedimiento de cierre establecido en el Acta (EDT 1.6.5).
- **CA-09.9:** Se documenta el cierre de las condiciones del proyecto.

**No declarar HU-09 completa ahora:** aceptación formal, piloto real, capacitación y cierre pertenecen a etapas posteriores al desarrollo.

---

## Instrucciones para Codex

1. Usa las definiciones literales anteriores como fuente para la matriz de cumplimiento; no inventes criterios ni reinterpretes sus textos.
2. Compara cada CA de HU-01 a HU-08 contra implementaciones y pruebas concretas del repositorio, citando archivos y funciones.
3. Corrige los faltantes dentro del alcance del desarrollo, sin reescribir la aplicación ni borrar datos.
4. Distingue lo que está probado en el sistema, lo simulado académicamente y lo no verificado.
5. Actualiza `docs/CUMPLIMIENTO.md` con una fila por criterio, resultado y evidencia. No marques como cumplido algo solo porque exista un botón o una vista.
6. Para HU-09, solo identifica como pendientes las actividades de aceptación y cierre posteriores.
