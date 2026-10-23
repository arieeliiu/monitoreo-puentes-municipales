import io, json, threading, unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError
from tests.test_app import SystemTests
from mock_provider import make_server, demo_records
from polling import interval_seconds, run_polling, single_worker
from provider_client import fetch_measurements

class IotUpdateTests(SystemTests):
    def test_vibration_nonnegative_finite_threshold(self):
        for value in ['-1','-0.01','NaN','inf','no-numérico','']:
            response=self.rule(threshold=value)
            self.assertEqual(response.status_code,200)
            self.assertEqual(self.count('rules'),0)
            self.assertIn('error',response.get_data(as_text=True))
        response=self.rule(threshold='-1')
        self.assertIn('El umbral de vibración no puede ser negativo.',response.get_data(as_text=True))
        for value in ['0','2.5']:self.assertEqual(self.rule(threshold=value).status_code,302)
        self.assertEqual(self.count('rules'),2)
        # Signed directional inclination thresholds are still allowed.
        self.assertEqual(self.rule('inclinacion',threshold='-2').status_code,200)

    def contract(self,external_id='x',**overrides):
        data=self.measurement(external_id=external_id,bridge_code='P1',kind='vibracion',simulated=True)
        data.update(overrides);return data

    def test_provider_rejects_inconsistent_and_missing_identity_with_evidence(self):
        self.db.execute("INSERT INTO sensors(component_id,code,kind,unit) VALUES(2,'S3','inclinacion','°')");self.db.commit()
        valid=[self.contract('a'),self.contract('b',sensor_code='S3',bridge_code='P2',kind='inclinacion',value='-3',unit='°')]
        records=valid+[self.contract('wrong-bridge',bridge_code='P2'),self.contract('wrong-type',kind='inclinacion'),self.contract('wrong-second',sensor_code='S3',bridge_code='P1',kind='inclinacion',unit='°'),self.contract('missing',bridge_code=None),self.contract('missing-kind',kind=''),self.contract('a',kind='inclinacion')]
        server=make_server(port=0,records=records);t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
        try:
            self.app.config['PROVIDER_URL']=f'http://127.0.0.1:{server.server_port}/measurements'
            self.assertEqual(self.post('/provider/pull').status_code,302)
            self.assertEqual(self.count('measurements'),2)
            self.post('/provider/pull');self.assertEqual(self.count('measurements'),2)
            details=self.db.execute("SELECT details FROM audit WHERE action='Consultar proveedor ficticio' ORDER BY id DESC").fetchone()[0]
            for code in ['wrong-bridge','wrong-type','wrong-second','missing','missing-kind']:self.assertIn(code,details)
            self.assertIn('no coincide',details)
            self.login('dom');self.assertIn('wrong-bridge',self.client.get('/audit').get_data(as_text=True))
        finally:server.shutdown();server.server_close();t.join()

    def test_optional_api_identity_is_validated_without_breaking_legacy(self):
        headers={'Authorization':'Bearer test-key'}
        data=self.contract('api',bridge_code='P2')
        self.assertEqual(self.client.post('/api/v1/measurements',json=data,headers=headers).status_code,400)
        data['bridge_code']='P1';self.assertEqual(self.client.post('/api/v1/measurements',json=data,headers=headers).status_code,201)
        self.assertEqual(self.client.post('/api/v1/measurements',json=self.measurement(external_id='legacy'),headers=headers).status_code,201)

    def test_provider_default_json_includes_two_bridges_and_types(self):
        records=demo_records();self.assertEqual(len(records),4)
        self.assertEqual({item['bridge_code'] for item in records},{'DEM-01','DEM-02'})
        self.assertEqual({item['kind'] for item in records},{'vibracion','inclinacion'})
        for item in records:
            self.assertTrue(item['simulated']);self.assertIn('sensor_code',item);self.assertIn('measured_at',item)

    def test_automatic_worker_recovers_and_deduplicates_real_http(self):
        records=[self.contract('auto')]
        server=make_server(port=0,records=records);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.app.config['PROVIDER_URL']=f'http://127.0.0.1:{server.server_port}/measurements'
        waits=[];errors=[];calls=[]
        class Stop:
            def is_set(self):return False
            def wait(self,seconds):waits.append(seconds);return len(waits)==3
        real_fetch=fetch_measurements
        def fetch(*args,**kwargs):
            calls.append(1)
            if len(calls)==1:raise ValueError('Desconexión simulada después de reintentos')
            return real_fetch(*args,**kwargs)
        def run(poll,interval,on_error):run_polling(poll,interval,stop=Stop(),on_error=lambda error:(errors.append(str(error)),on_error(error)))
        try:
            with patch('app.fetch_measurements',side_effect=fetch),patch('app.run_polling',side_effect=run):
                result=self.app.test_cli_runner().invoke(args=['poll-provider','--interval','7'])
            self.assertEqual(result.exit_code,0,result.output)
            self.assertEqual(len(calls),3);self.assertEqual(waits,[7,7,7]);self.assertEqual(len(errors),1)
            self.assertEqual(self.count('measurements'),1)
            self.assertEqual(self.db.execute("SELECT count(*) FROM audit WHERE action='Error al consultar proveedor ficticio'").fetchone()[0],1)
            self.assertEqual(self.client.get('/').status_code,200)
            self.post('/provider/pull');self.assertEqual(self.count('measurements'),1)
        finally:server.shutdown();server.server_close();thread.join()

    def test_worker_interval_environment_lock_and_bad_json(self):
        for value in ['0','-1','NaN','inf','86401','bad']:
            with self.assertRaises(ValueError):interval_seconds(value)
            result=self.app.test_cli_runner().invoke(args=['poll-provider','--interval',value])
            self.assertNotEqual(result.exit_code,0)
        with patch.dict('os.environ',{'IOT_POLL_INTERVAL':'12'}),patch('app.run_polling') as run:
            result=self.app.test_cli_runner().invoke(args=['poll-provider'])
            self.assertEqual(result.exit_code,0,result.output);self.assertEqual(run.call_args.args[1],12)
        with single_worker(self.app.config['DATABASE']):
            with self.assertRaisesRegex(ValueError,'Ya existe'): 
                with single_worker(self.app.config['DATABASE']):pass
        with single_worker(self.app.config['DATABASE']):pass  # Released for restart.
        with patch('provider_client.urlopen',return_value=io.BytesIO(b'no JSON')) as fetch:
            with self.assertRaises(ValueError):fetch_measurements('http://localhost/test',delay=0)
            self.assertEqual(fetch.call_count,1)

    def test_mockups_cover_current_real_views(self):
        from html.parser import HTMLParser
        class Document(HTMLParser):
            def __init__(self):super().__init__();self.sections=[];self.routes=[]
            def handle_starttag(self,tag,attrs):
                attrs=dict(attrs)
                if tag=='section' and 'id' in attrs:self.sections.append(attrs['id'])
                if tag=='form':self.routes.append(attrs.get('action'))
        html=Path('docs/mockups-full.html').read_text(encoding='utf-8');doc=Document();doc.feed(html)
        self.assertEqual(doc.sections,['infraestructura','captura','alertas','panel','mantenimiento'])
        for label in ['Programar inspección preventiva','Programación que se atiende','Actividades de mantenimiento pendientes','Próximas inspecciones programadas','Condiciones visuales','Ubicación específica','Cambio absoluto','Consultar proveedor']:
            self.assertIn(label,html)
        self.assertTrue(all(route is None for route in doc.routes))
        self.assertNotIn('Umbrales oficiales pendientes',html)

def load_tests(loader,standard_tests,pattern):
    return unittest.TestSuite(IotUpdateTests(name) for name in IotUpdateTests.__dict__ if name.startswith('test_'))
