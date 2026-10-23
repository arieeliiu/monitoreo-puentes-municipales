import io, sqlite3, tempfile, unittest
from pathlib import Path
from PIL import Image
from werkzeug.security import generate_password_hash
from app import create_app

class SystemTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)
        self.app=create_app({'TESTING':True,'DATABASE':str(self.path/'test.sqlite'),'UPLOAD_FOLDER':str(self.path/'photos'),'SECRET_KEY':'test','IOT_API_KEY':'test-key'})
        self.db=sqlite3.connect(self.app.config['DATABASE']); self.db.row_factory=sqlite3.Row
        self.db.executescript(Path('schema.sql').read_text(encoding='utf-8'))
        for name,role in [('dom','DOM'),('inspector','Inspector'),('worker','Mantención'),('other','Mantención')]: self.db.execute('INSERT INTO users(username,password,role) VALUES (?,?,?)',(name,generate_password_hash('password-test'),role))
        self.db.execute("INSERT INTO bridges VALUES(1,'P1','Puente de prueba','Biobío','Alta',1)")
        self.db.execute("INSERT INTO bridges VALUES(2,'P2','Segundo puente','Biobío','Media',1)")
        self.db.execute("INSERT INTO components VALUES(1,1,'Tablero')")
        self.db.execute("INSERT INTO components VALUES(2,2,'Pila')")
        self.db.execute("INSERT INTO sensors VALUES(1,1,'S1','vibracion','m/s²')")
        self.db.execute("INSERT INTO sensors VALUES(2,1,'S2','inclinacion','°')")
        self.db.commit(); self.client=self.app.test_client(); self.login('dom')
        self.db.execute("UPDATE sensors SET reference_value=0 WHERE kind='inclinacion'");self.db.commit()
    def tearDown(self): self.db.close(); self.tmp.cleanup()
    def login(self,name):
        self.client.get('/login')
        return self.post('/login',{'username':name,'password':'password-test'})
    def post(self,url,data=None,**kwargs):
        with self.client.session_transaction() as s: token=s.get('csrf','')
        payload=dict(data or {}); payload['csrf']=token
        return self.client.post(url,data=payload,**kwargs)
    def count(self,table): return self.db.execute('SELECT count(*) FROM '+table).fetchone()[0]
    def measurement(self,**extra):
        d=dict(sensor_code='S1',value='9',unit='m/s²',measured_at='2026-01-01T10:00:00-03:00',status='valido');d.update(extra);return d
    def rule(self,kind='vibracion',**extra):
        d=dict(bridge_id='1',kind=kind,severity='Atención',threshold='5',condition='Alta',label='Umbral ficticio',simulated='1');d.update(extra);return self.post('/rules',d)
    def inspection(self,**extra):
        d=dict(bridge_id='1',component_id='1',inspected_at='2026-01-01T10:00:00-03:00',condition='Alta',description='Hallazgo de prueba',simulated='1'); d.update(extra);return self.post('/inspections',d)
    def task(self,**extra):
        d=dict(bridge_id='1',component_id='1',alert_id='1',description='Revisar tablero',assignee_id='3',planned_date='2026-11-26');d.update(extra);return self.post('/maintenance',d)
    def test_bridge_crud_and_duplicates(self):
        d=dict(code='P3',name='Nuevo',location='Ubicación',criticality='Alta')
        self.assertEqual(self.post('/bridges',d).status_code,302)
        self.assertEqual(self.count('bridges'),3)
        self.post('/bridges',d);self.assertEqual(self.count('bridges'),3)
        d.update(id='3',name='Editado');self.post('/bridges',d)
        self.assertIn(b'Editado',self.client.get('/bridges/3').data)
        d.update(code='',id='');self.post('/bridges',d);self.assertEqual(self.count('bridges'),3)
    def test_components_sensors_validation_and_edits(self):
        self.post('/bridges/1',dict(entity='component',name='Estribo'))
        self.post('/bridges/1',dict(entity='component',name='Estribo'));self.assertEqual(self.count('components'),3)
        self.post('/bridges/1',dict(entity='component',id='3',name='Estribo norte'))
        self.post('/bridges/1',dict(entity='sensor',location='Apoyo de prueba',code='S3',component_id='3',kind='inclinacion'))
        self.assertEqual(self.count('sensors'),3)
        self.post('/bridges/1',dict(entity='sensor',location='Apoyo de prueba',code='S4',component_id='2',kind='vibracion'))
        self.assertEqual(self.count('sensors'),3)
        self.post('/measurements',self.measurement())
        self.post('/bridges/1',dict(entity='sensor',location='Apoyo de prueba',id='1',code='S1',component_id='1',kind='inclinacion'))
        self.assertEqual(self.db.execute('SELECT kind FROM sensors WHERE id=1').fetchone()[0],'vibracion')
    def test_role_permissions(self):
        self.login('inspector')
        for url,data in [('/bridges',{}),('/bridges/1',{}),('/measurements',{}),('/rules',{}),('/maintenance',{})]: self.assertEqual(self.post(url,data).status_code,403,url)
        self.assertEqual(self.client.get('/rules').status_code,403)
        self.assertEqual(self.inspection().status_code,302)
        self.login('worker');self.assertEqual(self.inspection().status_code,403)
        self.assertEqual(self.client.get('/audit').status_code,403)
    def test_measurement_validation_and_history(self):
        self.assertEqual(self.post('/measurements',self.measurement()).status_code,302)
        for extra in [dict(value='NaN'),dict(value='-1'),dict(unit='g'),dict(sensor_code='unknown'),dict(measured_at='bad'),dict(measured_at='2999-01-01T00:00:00Z'),dict(measured_at='2026-01-01T00:00:00'),dict(value='')]:
            self.post('/measurements',self.measurement(**extra))
        self.assertEqual(self.count('measurements'),1)
        self.post('/measurements',self.measurement(value='',status='no_disponible'))
        self.post('/measurements',self.measurement(value='-3',status='invalido'))
        self.assertEqual(self.count('measurements'),3)
        page=self.client.get('/measurements?bridge_id=1&from=2026-01-01&to=2026-01-02')
        self.assertIn(b'S1',page.data);self.assertIn(b'no disponible',page.data)
    def test_alert_threshold_and_simulation(self):
        self.rule();self.post('/measurements',self.measurement(value='4.999'));self.assertEqual(self.count('alerts'),0)
        self.post('/measurements',self.measurement());self.assertEqual(self.count('alerts'),1)
        self.post('/measurements',self.measurement(status='invalido'));self.assertEqual(self.count('alerts'),1)
        a=self.db.execute('SELECT * FROM alerts').fetchone();self.assertEqual(a['bridge_id'],1);self.assertEqual(a['simulated'],1);self.assertIsNotNone(a['measurement_id'])
        self.post('/rules',dict(disable='1'));self.post('/measurements',self.measurement());self.assertEqual(self.count('alerts'),1)
    def test_inclination_and_visual_alert(self):
        self.rule('inclinacion',threshold='2');self.rule('visual')
        self.post('/measurements',self.measurement(sensor_code='S2',value='3',unit='°'))
        self.inspection();self.assertEqual(self.count('alerts'),2)
    def test_academic_rule_without_real_reference(self):
        self.rule(simulated='0');self.assertEqual(self.count('rules'),1)
        self.assertEqual(self.db.execute('SELECT simulated FROM rules').fetchone()[0],1)
    def test_photo_upload_and_authorization(self):
        self.login('inspector'); buf=io.BytesIO();Image.new('RGB',(24,24),'blue').save(buf,'PNG');buf.seek(0)
        response=self.inspection(photos=(buf,'puente.png'))
        self.assertEqual(response.status_code,302)
        self.assertEqual(self.count('photos'),1)
        p=self.db.execute('SELECT * FROM photos').fetchone()
        page=self.client.get(response.location);self.assertIn(p['filename'].encode(),page.data)
        response=self.client.get('/photos/'+p['filename'])
        self.assertEqual(response.status_code,200);response.close()
        with self.client.session_transaction() as s:s.clear()
        self.assertEqual(self.client.get('/photos/'+p['filename']).status_code,302)
    def test_bad_photo_and_cross_bridge_inspection_rollback(self):
        self.inspection(photos=(io.BytesIO(b'not a photo'),'bad.jpg'));self.assertEqual(self.count('inspections'),0)
        self.inspection(component_id='2');self.assertEqual(self.count('inspections'),0)
        self.inspection(description=' ');self.assertEqual(self.count('inspections'),0)
        self.assertEqual(list((self.path/'photos').iterdir()),[])
    def test_iot_auth_idempotency_and_unavailable_configuration(self):
        data=self.measurement(external_id='x1',simulated=True)
        self.assertEqual(self.client.post('/api/v1/measurements',json=data).status_code,401)
        headers={'Authorization':'Bearer test-key'}
        self.assertEqual(self.client.post('/api/v1/measurements',json=data,headers=headers).status_code,201)
        self.assertEqual(self.client.post('/api/v1/measurements',json=data,headers=headers).status_code,400)
        self.assertEqual(self.count('measurements'),1)
        self.app.config['IOT_API_KEY']=None
        self.assertEqual(self.client.post('/api/v1/measurements',json=data,headers=headers).status_code,503)
    def test_malformed_api_fields(self):
        headers={'Authorization':'Bearer test-key'}
        for override in [dict(value={}),dict(value=True),dict(sensor_code=None),dict(unit=[]),dict(external_id=['x']),dict(simulated='false')]:
            data=self.measurement(external_id='bad',simulated=True);data.update(override)
            self.assertEqual(self.client.post('/api/v1/measurements',json=data,headers=headers).status_code,400)
        self.assertEqual(self.count('measurements'),0)
    def test_dom_task_edit_and_inspector_followup(self):
        self.rule();self.post('/measurements',self.measurement());self.task();self.inspection()
        self.post('/maintenance',dict(id='1',description='Reasignada',assignee_id='4',planned_date='2026-11-25',status='Pendiente'))
        task=self.db.execute('SELECT * FROM tasks').fetchone();self.assertEqual(task['assignee_id'],4)
        self.login('inspector')
        self.assertEqual(self.post('/alerts/1',dict(note='Inspección vinculada',inspection_id='1')).status_code,302)
        self.assertEqual(self.post('/alerts/1',dict(note='Cerrar',status='Resuelta')).status_code,403)
        self.assertEqual(self.db.execute('SELECT status FROM alerts').fetchone()[0],'Activa')
        self.assertEqual(self.client.get('/measurements/1').status_code,200)
    def test_maintenance_assignment_tracking_and_explicit_resolution(self):
        self.rule();self.post('/measurements',self.measurement());self.inspection()
        self.assertEqual(self.task().status_code,302)
        self.assertEqual(self.db.execute('SELECT status FROM alerts').fetchone()[0],'Activa')
        self.login('other');self.assertNotIn(b'Revisar tablero',self.client.get('/maintenance').data)
        self.assertEqual(self.post('/maintenance',dict(id='1',status='Completada')).status_code,403)
        self.login('worker')
        self.post('/maintenance',dict(id='1',status='En ejecución'));self.post('/maintenance',dict(id='1',status='Completada'))
        self.assertEqual(self.db.execute('SELECT status FROM tasks').fetchone()[0],'Completada')
        self.assertEqual(self.db.execute('SELECT status FROM alerts').fetchone()[0],'Activa')
        self.login('dom');self.post('/alerts/1',dict(note='Revisado y atendido',inspection_id='1',status='Resuelta'))
        self.assertEqual(self.db.execute('SELECT status FROM alerts').fetchone()[0],'Resuelta')
        page=self.client.get('/alerts/1');self.assertIn(b'Revisar tablero',page.data);self.assertIn(b'Revisado y atendido',page.data)
        self.assertGreater(self.count('audit'),5)
    def test_cross_bridge_task_and_bad_assignee(self):
        self.rule();self.post('/measurements',self.measurement())
        self.task(bridge_id='2',component_id='2');self.task(assignee_id='2');self.task(planned_date='bad')
        self.assertEqual(self.count('tasks'),0)
    def test_dashboard_empty_and_missing_latest(self):
        page=self.client.get('/');self.assertIn(b'Sin datos',page.data);self.assertIn(b'No existen reglas activas',page.data)
        self.post('/measurements',self.measurement())
        self.post('/measurements',self.measurement(measured_at='2026-01-02T00:00:00Z',status='no_disponible',value=''))
        self.assertIn(b'No disponible',self.client.get('/').data)
    def test_csrf_and_xss(self):
        self.assertEqual(self.client.post('/bridges',data={'name':'x'}).status_code,400)
        self.inspection(description='<script>alert(1)</script>')
        data=self.client.get('/inspections/1').data
        self.assertNotIn(b'<script>alert(1)</script>',data);self.assertIn(b'&lt;script&gt;',data)
    def test_all_pages_render(self):
        self.rule();self.post('/measurements',self.measurement());self.inspection();self.task()
        for path in ['/','/bridges','/bridges/1','/measurements','/inspections','/inspections/1','/rules','/alerts','/alerts/1','/maintenance','/audit']:
            self.assertEqual(self.client.get(path).status_code,200,path)
    def test_persistence_after_app_recreation(self):
        self.post('/measurements',self.measurement())
        app2=create_app(dict(self.app.config));client=app2.test_client()
        with client.session_transaction() as s:s['user_id']=1
        self.assertIn(b'9.0',client.get('/measurements').data)

if __name__=='__main__': unittest.main()
