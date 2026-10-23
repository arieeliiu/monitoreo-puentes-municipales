"""Genera bocetos navegables desde las plantillas reales, en una base temporal."""
import re, sqlite3, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app import create_app
from migrations import migrate

def build():
    with tempfile.TemporaryDirectory() as temp:
        database=Path(temp)/'mockups.sqlite'
        db=sqlite3.connect(database);db.executescript((ROOT/'schema.sql').read_text(encoding='utf-8'));migrate(db)
        db.executemany('INSERT INTO users(id,username,password,role) VALUES(?,?,?,?)',[(1,'dom','sin acceso','DOM'),(2,'inspector','sin acceso','Inspector'),(3,'mantencion','sin acceso','Mantención')])
        db.executemany('INSERT INTO bridges VALUES(?,?,?,?,?,1)',[(1,'DEM-01','Puente Estero Norte','Ubicación ficticia · Biobío','Alta'),(2,'DEM-02','Puente Ribera Sur','Ubicación ficticia · Biobío','Alta')])
        db.executemany('INSERT INTO components VALUES(?,?,?)',[(1,1,'Tablero · prueba'),(2,2,'Tablero · prueba')])
        for bid in (1,2):
            for kind,unit in [('vibracion','mm/s'),('inclinacion','°')]:
                db.execute('INSERT INTO sensors(component_id,code,kind,unit,location) VALUES(?,?,?,?,?)',(bid,f'DEM-0{bid}-{kind.upper()}',kind,unit,'Apoyo central · ubicación ficticia'))
        stamp='2026-10-22T13:00:00+00:00'
        db.execute("INSERT INTO rules(bridge_id,kind,threshold,label,simulated,author_id,created_at,comparison) VALUES(1,'vibracion',5,'Supuesto de contraparte ficticia',1,1,?,'gt')",(stamp,))
        db.execute("INSERT INTO measurements(sensor_id,value,unit,measured_at,status,simulated,external_id,created_at,evaluation) VALUES(1,7,'mm/s',?,'valido',1,'mockup-1',?,'Evaluada')",(stamp,stamp))
        db.execute("INSERT INTO alerts(bridge_id,rule_id,measurement_id,created_at,simulated) VALUES(1,1,1,?,1)",(stamp,))
        db.execute("INSERT INTO inspections(bridge_id,component_id,inspected_at,inspector_id,condition,description,simulated) VALUES(1,1,?,2,'Regular','Hallazgo ficticio: revisar apoyo del tablero.',1)",(stamp,))
        db.execute("INSERT INTO tasks(bridge_id,component_id,alert_id,description,assignee_id,planned_date,author_id,created_at) VALUES(1,1,1,'Revisión preventiva ficticia',3,'2026-11-20',1,?)",(stamp,))
        db.execute("INSERT INTO inspection_plans(bridge_id,component_id,inspector_id,planned_date,description,author_id,created_at) VALUES(2,2,2,'2026-11-23','Inspección preventiva ficticia',1,?)",(stamp,))
        db.commit();db.close()
        app=create_app({'TESTING':True,'DATABASE':str(database),'UPLOAD_FOLDER':str(Path(temp)/'photos'),'SECRET_KEY':'mockup-not-a-session-key'})
        client=app.test_client()
        with client.session_transaction() as session:session['user_id']=1
        sections=[('infraestructura','1 · Infraestructura',[('/bridges','Inventario'),('/bridges/1','Ficha, edición, componentes y sensores')]),('captura','2 · Mediciones e inspecciones visuales',[('/measurements','Historial, consulta manual y captura automática IoT'),('/inspections','Registro visual con fotografías opcionales'),('/inspections/1','Resultado, observaciones y fotografías')]),('alertas','3 · Reglas y seguimiento de alertas',[('/rules','Umbrales académicos y comparaciones'),('/alerts/1','Origen, inspección relacionada, tareas y cierre explícito')]),('panel','4 · Panel de monitoreo',[('/','Sensores, alertas, pendientes, programación y últimas inspecciones')]),('mantenimiento','5 · Mantenimiento y programación de inspecciones',[('/maintenance','Asignación, estados y filtro por puente'),('/inspection-plans','DOM programa; inspector asignado registra resultado')])]
        body=[]
        for anchor,title,pages in sections:
            body.append(f'<section id="{anchor}"><h2>{title}</h2>')
            for route,label in pages:
                role='Inspector' if route=='/inspections' else 'DOM'
                with client.session_transaction() as session:session['user_id']=2 if role=='Inspector' else 1
                response=client.get(route)
                assert response.status_code==200,route
                content=re.search(r'<main\b[^>]*>(.*?)</main>',response.get_data(as_text=True),re.S).group(1)
                content=re.sub(r'<footer>.*?</footer>','',content,flags=re.S)
                content=re.sub(r'<input type="hidden" name="csrf"[^>]*>','',content)
                content=re.sub(r'<form\b[^>]*>','<form>',content)
                content=re.sub(r'<button\b','<button disabled',content)
                # Keep mockups static; navigation uses the five functional sections.
                def link(match):
                    href=match.group(1)
                    target='captura' if href.startswith(('/measurements','/inspections','/provider')) else 'mantenimiento' if href.startswith(('/maintenance','/inspection-plans')) else 'alertas' if href.startswith(('/alerts','/rules')) else 'infraestructura' if href.startswith('/bridges') else 'panel'
                    return 'href="#'+target+'"'
                content=re.sub(r'href="([^"]+)"',link,content)
                body.append(f'<article><h3>{label}</h3><small>Vista real: {route} · Rol {role} en este boceto. El inspector registra el resultado desde Inspecciones visuales, seleccionando su programación.</small>{content}</article>')
            body.append('</section>')
        nav=''.join(f'<a href="#{anchor}">{title}</a>' for anchor,title,_ in sections)
        html='<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Mockups actuales · Puentes</title><link rel="stylesheet" href="../static/app.css"></head><body><aside><div class="brand">╫ PUENTES</div><nav>'+nav+'</nav></aside><main><h1>Mockups de las cinco funcionalidades</h1><p class="notice warning">Bocetos estáticos generados desde las plantillas reales. Todos los datos y umbrales son supuestos académicos. Botones desactivados; usa los enlaces de navegación. Las fotografías son opcionales.</p><p>Término EDT 1.4.5/1.4.6: 24/11/2026 · Presentación: 26/11/2026.</p>'+''.join(body)+'</main></body></html>'
        (ROOT/'docs/mockups.html').write_text(html.replace('><','>\n<'),encoding='utf-8')

if __name__=='__main__':build()
