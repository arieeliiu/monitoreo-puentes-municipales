# Publicación temporal con Cloudflare Quick Tunnel

Desde la carpeta del proyecto en PowerShell:

```powershell
.\publicar-demo.ps1
```

Requisitos: Windows, Python del entorno `.venv`, dependencias de `requirements.txt` y `cloudflared`. Si falta este último: `winget install --id Cloudflare.cloudflared --exact`, abrir otra terminal y repetir. También se reconoce el binario instalado mediante el paquete npm `cloudflared`. El script informa requisitos faltantes sin instalar programas ni cambiar otras aplicaciones.

Inicia Waitress en **127.0.0.1:5000**, proveedor en **127.0.0.1:5100**, worker cada **60 segundos** y un Quick Tunnel apuntando únicamente al servidor web. Muestra la URL HTTPS asignada. Fuerza `COOKIE_SECURE=1`, `PROJECT_STAGE=cutoff_2026_10_26` y `PROVIDER_URL=http://127.0.0.1:5100/measurements` en los procesos iniciados. No instala servicios ni habilita debug. El acceso por HTTPS conserva login, roles, CSRF, sesiones y fotografías privadas. Las cookies Secure requieren HTTPS para iniciar sesión desde un navegador; la comprobación local de disponibilidad usa `/login` sin autenticarse.

Mantener el computador encendido, conectado a internet y sin suspender. La URL es temporal y cambia al reiniciar el túnel. Quick Tunnels no ofrecen garantía de disponibilidad: [documentación oficial](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).

Para detener:

```powershell
.\detener-demo.ps1
```

Solo detiene los árboles de procesos registrados por este inicio, verificando PID, fecha de creación y comando. Un PID reutilizado o estado de otra carpeta no autoriza detenerlo. Conserva SQLite, cuentas, fotos e históricos. Repetir publicar reutiliza los cuatro procesos activos; repetir detener no afecta otros servidores. Si los puertos están ocupados por procesos no registrados, el inicio se detiene y pide cerrar ese servidor expresamente. Un error parcial revierte únicamente los procesos iniciados por los scripts. Un bloqueo de archivo impide inicios/detenciones simultáneos.

La información de procesos y URL está en `instance/publicacion-demo.json`; logs de cada proceso en `instance/demo-*.out.log` / `instance/demo-*.err.log`. Se usa nivel info, sin registrar cabeceras de sesión ni contraseñas. La configuración vacía privada del Quick Tunnel evita usar otra configuración personal de Cloudflare.

La base existente se conserva sin ejecutar `seed-demo`. Solo si falta `instance/puentes.sqlite` se ejecutan `init-db` y `seed-demo`; las contraseñas generadas se guardan únicamente en **instance/ACCESO_LOCAL.txt**, excluido de Git. En una instalación existente se conserva ese archivo y las cuentas sin cambios. No compartir logs o ese archivo en GitHub; entrega las credenciales individualmente.

Pruebas reproducibles:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
node --test tests/frontend.test.cjs
.\tests\test_publicacion.ps1
```

Las pruebas funcionales usan bases temporales y cubren formularios DOM, sensores, mediciones manuales/API/proveedor/worker, consulta manual, fotos de Inspector, permisos de Mantención, corte sin alertas y persistencia. La prueba PowerShell verifica sintaxis, identidad de procesos, estado vacío/repetido y protección de procesos ajenos. La publicación real se verifica además por HTTPS, repetición del inicio y detención/reinicio con conservación de filas y fotografías. Una dirección impresa por cloudflared por sí sola no acredita acceso público: comprobar `/login` y la sesión desde la URL HTTPS.


## Verificación de la entrega

Se ejecutó la aplicación real por Quick Tunnel, sin cambiar el backend. Regresión: **63 pruebas Python y 3 JavaScript aprobadas**. Además, **4 comprobaciones PowerShell aprobadas**, incluida identidad conservada tras guardar/leer JSON (marca temporal numérica para evitar conversión automática de fechas). El ciclo real publicar → publicar → detener → detener → publicar reutilizó procesos en el inicio repetido y liberó los anteriores al detener.

Se comprobaron las tres cuentas por la URL HTTPS pública mediante peticiones HTTP reales: login, redirección al inicio, cookies Secure, cuatro rutas disponibles, rutas futuras 404 y redirección a login sin sesión. El proveedor y el worker reciben mediciones automáticamente sin crear alertas; la integridad SQLite se verifica tras reiniciar. Los formularios de infraestructura/sensores, captura manual/consulta del proveedor, inspecciones/fotos, permisos y persistencia se prueban en bases temporales de la suite. La URL vigente se consulta en el registro privado o ejecutando publicar de nuevo; no se fija en este documento porque cambia con cada túnel.
