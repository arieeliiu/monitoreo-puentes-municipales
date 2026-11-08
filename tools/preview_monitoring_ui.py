"""Servidor de evidencia con SQLite temporal; no lee configuración ni datos operativos."""
import os
from pathlib import Path
import secrets
import sqlite3
import sys
import tempfile
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
for key in ('DATABASE_URL','VERCEL','PHOTO_STORAGE','SUPABASE_URL','SUPABASE_SECRET_KEY','CLOUD_PROVIDER','PROJECT_STAGE'):
    os.environ.pop(key,None)
from app import create_app,EV3_STAGE
from migrations import migrate

def main():
    with tempfile.TemporaryDirectory(prefix='puentes-ui-evidence-') as temporary:
        folder=Path(temporary);path=folder/'ui.sqlite'
        with sqlite3.connect(path) as db:
            db.executescript((ROOT/'schema.sql').read_text(encoding='utf-8'));migrate(db)
            for uid,name,role in [(1,'dom','DOM'),(2,'inspector','Inspector'),(3,'mantencion','Mantención')]:
                db.execute('INSERT INTO users(id,username,password,role) VALUES(?,?,?,?)',
                           (uid,name,generate_password_hash('local-ui-evidence-only'),role))
            for bid,code,name in [(1,'EST-01','Puente Estero Norte'),(2,'RIB-02','Puente Ribera Sur')]:
                db.execute("INSERT INTO bridges VALUES(?,?,?,'Biobío','Alta',1)",(bid,code,name))
                db.execute("INSERT INTO components VALUES(?,?,'Tablero')",(bid,bid))
                db.execute("INSERT INTO sensors(id,component_id,code,kind,unit) VALUES(?,?,?,'vibracion','m/s²')",(bid,bid,'S'+str(bid)))
                db.execute("INSERT INTO rules(id,bridge_id,kind,threshold,label,simulated,author_id,created_at,severity,standard,unit) VALUES(?,?,'vibracion',1,'Aceleración vertical',1,1,'2026-01-01T13:00:00+00:00','Alerta','EV2','m/s²')",(bid,bid))
            db.execute("INSERT INTO rules(bridge_id,kind,threshold,label,simulated,active,author_id,created_at,severity,standard,unit) VALUES(1,'vibracion',0.8,'Límite anterior',1,0,1,'2025-12-01T13:00:00+00:00','Alerta','EV2','m/s²')")
            for n in range(1,46):
                bid=1 if n%2 else 2
                stamp=f'2026-01-{1+n//20:02d}T13:00:00+00:00'
                db.execute("INSERT INTO measurements(id,sensor_id,value,unit,measured_at,status,simulated,created_at,evaluation,specification) VALUES(?,?,2,'m/s²',?,'valido',1,?,'Evaluada','EV2')",(n,bid,stamp,stamp))
                db.execute("INSERT INTO alerts(bridge_id,rule_id,measurement_id,created_at,simulated,severity,standard,status) VALUES(?,?,?,?,1,'Alerta','EV2',?)",(bid,bid,n,stamp,'En atención' if n%5==0 else 'Activa'))
                db.execute("INSERT INTO audit(author,action,entity,entity_id,details,created_at) VALUES('DOM','Revisión de registro','measurements',?,'Registro de laboratorio',?)",(n,stamp))
            db.commit()
        db.close()
        app=create_app(dict(TESTING=True,SECRET_KEY=secrets.token_hex(32),DATABASE=str(path),DATABASE_URL='',
                            PHOTO_STORAGE='local',UPLOAD_FOLDER=str(folder/'photos'),PROJECT_STAGE=EV3_STAGE,
                            IOT_API_KEY=None,PROVIDER_URL='http://127.0.0.1:1/disabled',CLOUD_PROVIDER=False))
        server=make_server('127.0.0.1',5290,app)
        print('PREVIEW_READY http://127.0.0.1:5290',flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
        finally:server.server_close()

if __name__=='__main__':main()
