# Monitoreo de puentes municipales

Aplicación funcional Flask + SQLite para un piloto de dos puentes de la Región del Biobío. Fecha objetivo de la línea de base: **26 de noviembre de 2026**.

## Instalar en Windows

Requiere Python 3.12 o superior y una terminal PowerShell dentro de esta carpeta.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app app init-db
.\.venv\Scripts\python.exe -m flask --app app seed-demo
.\.venv\Scripts\python.exe -m flask --app app run --host 127.0.0.1 --port 5000
```

Abrir http://127.0.0.1:5000. `seed-demo` imprime una contraseña aleatoria para cada usuario: `dom`, `inspector`, `mantencion`. Guardarlas fuera del repositorio. Solo funciona sobre una base vacía. No crea reglas oficiales ni mediciones ficticias sin intervención del usuario.

La instalación local preparada por Codex incluye `.venv` y una base de demostración en `instance/`. Las credenciales locales están en `instance/ACCESO_LOCAL.txt`, excluido de Git. Para iniciarla basta ejecutar `start.ps1` o el último comando anterior.

Para comenzar con información real, usar una base nueva, ejecutar `init-db` y crear usuarios individualmente:

```powershell
.\.venv\Scripts\python.exe -m flask --app app create-user administrador --role DOM
.\.venv\Scripts\python.exe -m flask --app app create-user inspector1 --role Inspector
.\.venv\Scripts\python.exe -m flask --app app create-user tecnico1 --role Mantención
```

Las contraseñas se piden sin eco y requieren 12 caracteres como mínimo. No hay registro público de cuentas.

## Recorrido de demostración

1. DOM: revisar los dos puentes ficticios; editar infraestructura y agregar componentes/sensores.
2. DOM: crear una regla marcada como **ficticia para pruebas**, eligiendo un valor arbitrario solo para demostrar la comparación. No constituye un umbral estructural.
3. DOM: en Mediciones, abrir el entorno local y enviar un valor de prueba superior al umbral, con unidad correspondiente y fecha ISO con zona horaria (por ejemplo `2026-10-22T10:00:00-03:00`). Se guardan medición y alerta en una transacción.
4. Inspector: registrar una inspección del mismo puente, opcionalmente con hasta cinco fotografías JPEG/PNG, y abrir su ficha.
5. DOM: abrir la alerta, relacionar la inspección en una nota y planificar una actividad con esa alerta y personal de mantención.
6. Mantención: consultar la actividad asignada y actualizar a En ejecución / Completada.
7. DOM: revisar el seguimiento y resolver explícitamente la alerta con una justificación. Crear o completar tareas no resuelve alertas.

## Roles

| Operación | DOM | Inspector | Mantención |
|---|---|---|---|
| Consultar infraestructura, mediciones, inspecciones, fotos y alertas | Sí | Sí | Sí |
| Registrar/editar puentes, componentes y sensores | Sí | No | No |
| Registrar mediciones locales ficticias / configurar reglas | Sí | No | No |
| Registrar inspecciones y fotos / notas de alerta | Sí | Sí | No |
| Cambiar estado de alerta / planificar y reasignar mantenimiento | Sí | No | No |
| Consultar mantenimiento | Todo | Todo | Solo asignado |
| Actualizar ejecución de actividad | Todas | No | Solo asignada |
| Consultar auditoría | Sí | No | No |

## Integración IoT y simulador

Arquitectura: Sensor → plataforma IoT externa → POST API municipal. El adaptador receptor está implementado; **no hay proveedor ni conexión real verificada**. El proveedor futuro debe enviar JSON al contrato siguiente. El sistema no instala sensores ni predice fallas.

```powershell
$env:IOT_API_KEY = 'reemplazar-por-un-secreto-largo-y-aleatorio'
.\.venv\Scripts\python.exe -m flask --app app run
# En otra terminal, configurar la misma variable:
.\.venv\Scripts\python.exe simulate_iot.py --sensor DEM-01-VIBRACION --value 7 --unit mm/s
```

El número del ejemplo es exclusivamente ficticio. El simulador marca siempre `simulated: true`. Sin API key el receptor devuelve 503; clave incorrecta: 401; contenido inválido o ID repetido: 400; recepción válida: 201.

`POST /api/v1/measurements`, cabecera `Authorization: Bearer <IOT_API_KEY>`:

```json
{"external_id":"proveedor-uuid-unico","sensor_code":"DEM-01-VIBRACION","value":7,"unit":"mm/s","measured_at":"2026-10-22T10:00:00-03:00","status":"valido","simulated":true}
```

Unidades canónicas: vibración `mm/s`, inclinación `°`. No se convierten unidades silenciosamente. `status`: `valido`, `invalido`, `no_disponible`; los dos últimos no generan alertas, pueden guardar valor nulo. Payload malformado se rechaza. Un sensor válido con vibración negativa se rechaza; inclinación admite valores con signo. Umbral numérico: comparación estricta `valor > umbral`; visual: coincidencia exacta con la condición seleccionada. Reglas nuevas no reevalúan registros históricos. Desactivar una regla conserva las alertas existentes. Toda alerta hereda marca de prueba si la regla o el registro es ficticio.

## Datos, seguridad y operación

- SQLite y fotografías se guardan en `instance/`. Reiniciar no borra registros. `init-db` es idempotente. Hacer respaldo conjunto de la base y las fotos con la aplicación detenida.
- Las fechas se normalizan a UTC; los formularios requieren zona horaria y rechazan fechas futuras. Se muestran fecha/hora de la última recepción y estados faltantes explícitos; no existe diagnóstico automático de seguridad estructural ni SLA de frescura acordado.
- Contraseñas con hash scrypt de Werkzeug, control de rol en servidor, CSRF, consultas parametrizadas, CSP y acceso autenticado a fotos. Las imágenes se verifican y recodifican a JPEG; no se conserva EXIF. Máximo 5 fotos, 20 megapíxeles por foto y 20 MB por petición.
- Cambiar tipo o componente de un sensor con mediciones se bloquea para preservar la trazabilidad. Cambios relevantes se registran con autor y fecha en auditoría.
- Historial de mediciones: máximo 500 resultados por consulta; filtrar fechas y sensor. Auditoría: últimas 500 operaciones en pantalla; la base conserva todas.
- Para red institucional, usar HTTPS y servidor WSGI: `waitress-serve --listen=127.0.0.1:5000 --call app:create_app`, detrás de proxy TLS. Configurar `COOKIE_SECURE=1`, `SECRET_KEY` e `IOT_API_KEY` mediante el entorno. El servidor Flask de `start.ps1` se destina a demostración local.
- Pendiente de terceros: nombres y ubicaciones reales, criterios CA textuales oficiales, umbrales validados, proveedor IoT y credenciales, política de frescura/retención/respaldo y aceptación municipal. La referencia de validación de reglas es declarada por DOM, no certificada por el sistema.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

La suite usa bases temporales, sin modificar los datos del piloto. Cubre infraestructura, permisos, fotos, mediciones, alertas numéricas/visuales, API, panel, trazabilidad, mantenimiento, persistencia, CSRF y escape HTML. Ver [cumplimiento](docs/CUMPLIMIENTO.md), [flujos y mockups](docs/DISENO.md), [arquitectura](docs/ARQUITECTURA.md) y [verificación](docs/VERIFICACION.md).

## Repositorio

Nombre solicitado: `monitoreo-puentes-municipales`, visibilidad pública. Publicar únicamente código y documentación. `.venv/`, `instance/`, fotos, credenciales y claves están excluidos de Git. Con GitHub CLI autenticado:

```powershell
gh repo create monitoreo-puentes-municipales --public --source . --remote origin --push
```
