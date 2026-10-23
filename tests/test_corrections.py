import json, sqlite3, threading, unittest
from unittest.mock import patch
from urllib.error import URLError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from migrations import migrate
from mock_provider import make_server
from provider_client import fetch_measurements
from tests.test_app import SystemTests

class CorrectionsTests(SystemTests):
    # Reuse the original fixtures and regression checks as well as the new scenarios.
    def plan(self,**overrides):
        data=dict(bridge_id='1',component_id='1',inspector_id='2',planned_date='2026-11-24',description='Inspección preventiva')
        data.update(overrides);return self.post('/inspection-plans',data)

    def test_sensor_location_and_variable(self):
        self.post('/bridges/1',dict(entity='sensor',code='S3',component_id='1',kind='inclinacion',location='Cara oeste / apoyo 2'))
        sensor=self.db.execute("SELECT * FROM sensors WHERE code='S3'").fetchone()
        self.assertEqual(sensor['location'],'Cara oeste / apoyo 2')
        self.post('/bridges/1',dict(entity='sensor',id=str(sensor['id']),code='S3',component_id='1',kind='inclinacion',location='Apoyo 3'))
        text=self.client.get('/bridges/1').get_data(as_text=True)
        self.assertIn('Apoyo 3',text);self.assertIn('Variable: Inclinación',text)
        self.post('/bridges/1',dict(entity='sensor',code='MISSING',component_id='1',kind='vibracion'))
        self.assertIsNone(self.db.execute("SELECT * FROM sensors WHERE code='MISSING'").fetchone())

    def test_migration_preserves_every_existing_table_row(self):
        self.rule();self.inspection();self.post('/measurements',self.measurement());self.task()
        tables=['users','bridges','components','sensors','measurements','inspections','rules','alerts','tasks','audit','photos','alert_notes']
        before={table:[tuple(r) for r in self.db.execute('SELECT * FROM '+table)] for table in tables}
        migrate(self.db);migrate(self.db)
        after={table:[tuple(r) for r in self.db.execute('SELECT * FROM '+table)] for table in tables}
        self.assertEqual(before,after)
        legacy=sqlite3.connect(':memory:');legacy.executescript(Path('schema.sql').read_text(encoding='utf-8'))
        legacy.execute("INSERT INTO bridges VALUES(99,'OLD','Conservado','Sur','Alta',0)")
        legacy.execute("INSERT INTO components VALUES(99,99,'Viejo')")
        legacy.execute("INSERT INTO sensors VALUES(99,99,'OLD-S','inclinacion','°')")
        legacy.commit();migrate(legacy);migrate(legacy)
        self.assertEqual(legacy.execute('SELECT code,location FROM sensors').fetchone(),('OLD-S','Pendiente de precisar'));legacy.close()

    def test_no_rule_received_notice(self):
        response=self.post('/measurements',self.measurement(),follow_redirects=True)
        self.assertIn('Sin regla aplicable',response.get_data(as_text=True))
        self.rule('visual');self.post('/measurements',self.measurement())
        self.assertEqual(self.db.execute('SELECT evaluation FROM measurements ORDER BY id DESC').fetchone()[0],'Sin regla aplicable')
        response=self.client.post('/api/v1/measurements',json=self.measurement(external_id='api-no-rule'),headers={'Authorization':'Bearer test-key'})
        self.assertEqual(response.json['evaluation'],'Sin regla aplicable')

    def test_signed_and_absolute_inclination_boundaries(self):
        self.rule('inclinacion',threshold='2')
        for value in [2,-2,1,-1,3,-3]:
            self.post('/measurements',self.measurement(sensor_code='S2',unit='°',value=str(value)))
        self.assertEqual(self.count('alerts'),4)  # EV2: both signs, inclusive limits.
        before=self.count('rules');self.rule('inclinacion',threshold='-1');self.assertEqual(self.count('rules'),before)

    def test_provider_http_end_to_end_two_bridges_dedup_and_errors(self):
        self.db.execute("INSERT INTO sensors(component_id,code,kind,unit) VALUES(2,'S3','inclinacion','°')");self.db.commit()
        self.db.execute("UPDATE sensors SET reference_value=0 WHERE code='S3'");self.db.commit()
        self.rule();self.rule('inclinacion',bridge_id='2',comparison='abs_gt',threshold='2')
        records=[self.measurement(external_id='provider-a',bridge_code='P1',kind='vibracion',simulated=True),self.measurement(external_id='provider-b',bridge_code='P2',kind='inclinacion',sensor_code='S3',unit='°',value='-3',simulated=True),self.measurement(external_id='provider-bad',bridge_code='P1',kind='vibracion',unit='wrong',simulated=True)]
        server=make_server(port=0,records=records);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            self.app.config['PROVIDER_URL']=f'http://127.0.0.1:{server.server_port}/measurements'
            response=self.post('/provider/pull',follow_redirects=True)
            self.assertIn('2 recibidas',response.get_data(as_text=True));self.assertEqual(self.count('measurements'),2);self.assertEqual(self.count('alerts'),2)
            self.post('/provider/pull');self.assertEqual(self.count('measurements'),2)
            self.assertEqual({r[0] for r in self.db.execute('SELECT bridge_id FROM alerts')},{1,2})
            for name in ['inspector','worker']:
                self.login(name);self.assertEqual(self.post('/provider/pull').status_code,403)
        finally:server.shutdown();server.server_close();thread.join()

    def test_retry_connection_and_bad_json(self):
        with patch('provider_client.urlopen',side_effect=URLError('offline')) as mock:
            with self.assertRaisesRegex(ValueError,'3 intentos'):fetch_measurements('http://localhost:1',delay=0)
            self.assertEqual(mock.call_count,3)
        self.app.config['PROVIDER_URL']='bad-url';self.assertIn('Configura una URL',self.post('/provider/pull',follow_redirects=True).get_data(as_text=True))
        class Handler(BaseHTTPRequestHandler):
            attempts=0
            def do_GET(self):
                Handler.attempts+=1
                self.send_response(503 if Handler.attempts<3 else 200);self.end_headers();self.wfile.write(b'{"measurements":[]}')
            def log_message(self,*args):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
        try:
            self.assertEqual(fetch_measurements(f'http://127.0.0.1:{server.server_port}/',delay=0),[]);self.assertEqual(Handler.attempts,3)
        finally:server.shutdown();server.server_close();t.join()

    def test_schedule_roles_result_and_dashboard(self):
        self.assertEqual(self.plan().status_code,302)
        self.assertIn('Inspección preventiva',self.client.get('/').get_data(as_text=True))
        self.login('worker');self.assertEqual(self.plan().status_code,403)
        self.login('inspector');self.assertEqual(self.plan().status_code,403)
        self.assertEqual(self.inspection(plan_id='1').status_code,302)
        plan=self.db.execute('SELECT * FROM inspection_plans').fetchone()
        self.assertEqual(plan['status'],'Realizada');self.assertEqual(plan['inspection_id'],1)
        self.inspection(plan_id='1');self.assertEqual(self.count('inspections'),1)
        text=self.client.get('/').get_data(as_text=True);self.assertIn('Hallazgo de prueba',text);self.assertIn('fotografías y observaciones',text)
        self.assertIn('/inspections/1',self.client.get('/inspection-plans').get_data(as_text=True))

    def test_schedule_validations_and_cancel(self):
        self.plan(component_id='2');self.plan(inspector_id='3');self.plan(planned_date='bad');self.assertEqual(self.count('inspection_plans'),0)
        self.plan();self.login('inspector');self.inspection(plan_id='1',bridge_id='2',component_id='2');self.assertEqual(self.count('inspections'),0)
        self.login('dom');self.post('/inspection-plans',dict(cancel='1'));self.assertEqual(self.db.execute('SELECT status FROM inspection_plans').fetchone()[0],'Cancelada')
        self.login('inspector');self.inspection(plan_id='1');self.assertEqual(self.count('inspections'),0)

    def test_unassigned_inspector_cannot_record_plan(self):
        from werkzeug.security import generate_password_hash
        self.plan()
        self.db.execute("INSERT INTO users(username,password,role) VALUES(?,?,'Inspector')",('alternate',generate_password_hash('password-test')));self.db.commit()
        self.login('alternate');self.assertEqual(self.inspection(plan_id='1').status_code,403)
        self.assertEqual(self.count('inspections'),0)
        self.assertEqual(self.db.execute('SELECT status FROM inspection_plans').fetchone()[0],'Programada')

    def test_official_views_and_required_fields(self):
        self.rule();self.post('/measurements',self.measurement());self.task()
        page=self.client.get('/alerts/1').get_data(as_text=True)
        self.assertIn('/measurements/1',page);self.assertIn('2026-',page)
        self.assertIn('Entorno de demostración',page)
        self.assertNotIn('PRUEBA',page)
        page=self.client.get('/measurements?bridge_id=1').get_data(as_text=True)
        for value in ['Puente de prueba','S1','Aceleración vertical pico','9.0','2026-01-01T13:00:00+00:00']:self.assertIn(value,page)
        count=self.count('tasks')
        response=self.task(description='',follow_redirects=True)
        self.assertIn('obligatorio',response.get_data(as_text=True));self.assertEqual(self.count('tasks'),count)
        self.login('inspector')
        response=self.inspection(description='',follow_redirects=True)
        self.assertIn('obligatorio',response.get_data(as_text=True))

    def test_maintenance_filter_and_missing_alert_relations(self):
        self.rule();self.post('/measurements',self.measurement());self.task();self.task(bridge_id='2',component_id='2',alert_id='',description='Solo segundo')
        self.assertNotIn('Solo segundo',self.client.get('/maintenance?bridge_id=1').get_data(as_text=True))
        self.assertIn('Solo segundo',self.client.get('/maintenance?bridge_id=2').get_data(as_text=True))
        self.assertIn('Revisar tablero',self.client.get('/').get_data(as_text=True))
        page=self.client.get('/alerts/1').get_data(as_text=True);self.assertIn('Sin inspección relacionada',page);self.assertNotIn('Sin actividad de mantenimiento relacionada',page)
        self.inspection();self.post('/alerts/1',dict(note='Vinculada',inspection_id='1'))
        self.assertNotIn('Sin inspección relacionada',self.client.get('/alerts/1').get_data(as_text=True))
        self.post('/measurements',self.measurement());self.assertIn('Sin actividad de mantenimiento relacionada',self.client.get('/alerts/2').get_data(as_text=True))
        for role in ['dom','inspector','worker']:
            self.login(role)
            for path in ['/','/bridges','/measurements','/inspections','/alerts','/maintenance','/inspection-plans']:
                self.assertEqual(self.client.get(path).status_code,200,(role,path))

def load_tests(loader, standard_tests, pattern):
    # The original 18 cases are discovered in test_app.py; run only additions here.
    return unittest.TestSuite(CorrectionsTests(name) for name in CorrectionsTests.__dict__ if name.startswith('test_'))
