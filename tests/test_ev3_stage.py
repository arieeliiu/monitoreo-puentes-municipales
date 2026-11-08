"""B-11: etapa intermedia, motor existente y conservación de EV2/full."""
import io
import os
import sqlite3
import threading
import unittest
from unittest.mock import patch
from PIL import Image
from app import create_app, CUTOFF_STAGE, EV3_STAGE, PENDING_EVALUATION
from tests.test_ev2 import Ev2Tests
from tests.test_project_stage import Navigation

class Ev3StageTests(Ev2Tests):
    def setUp(self):
        super().setUp()
        self.app.config['PROJECT_STAGE']=EV3_STAGE

    def tearDown(self):
        try:
            self.evidence={
                'measurements':self.count('measurements'),'inspections':self.count('inspections'),
                'rule_versions':self.count('rules'),'alerts':self.count('alerts'),
                'alert_notes':self.count('alert_notes'),
                'evaluations':[r[0] for r in self.db.execute('SELECT DISTINCT evaluation FROM measurements ORDER BY evaluation')],
                'alert_sources':[dict(r) for r in self.db.execute('SELECT bridge_id,measurement_id,inspection_id,rule_id,severity,status FROM alerts ORDER BY id')],
            }
        finally:super().tearDown()

    def snapshot(self):
        self.db.commit()
        names=[r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        return {n:[tuple(r) for r in self.db.execute('SELECT * FROM '+n+' ORDER BY id')] for n in names}

    def test_stage_configuration_navigation_permissions_and_blocked_writes(self):
        config=dict(self.app.config);config.pop('PROJECT_STAGE')
        with patch.dict(os.environ,{'PROJECT_STAGE':EV3_STAGE}):
            self.assertEqual(create_app(config).config['PROJECT_STAGE'],EV3_STAGE)
            self.assertEqual(create_app(dict(config,PROJECT_STAGE=CUTOFF_STAGE)).config['PROJECT_STAGE'],CUTOFF_STAGE)
        self.config();self.post('/measurements',self.measurement(value='2.5'))
        for role in ('dom','inspector','worker'):
            self.login(role)
            expected=['Inicio','Infraestructura','Monitoreo','Inspecciones visuales']
            if role=='dom':expected+=['Reglas de alerta','Historial de operaciones']
            for path in ('/','/bridges/1','/measurements','/inspections','/alerts','/alerts/1'):
                result=self.client.get(path);self.assertEqual(result.status_code,200,(role,path))
                text=result.text;self.assertEqual(Navigation(text).labels,expected)
                for link in ('/maintenance','/inspection-plans'):
                    self.assertNotIn('href="'+link,text)
                self.assertNotIn('name="plan_id"',text)
                self.assertEqual(text.count('Entorno de demostración'),0)
            home=self.client.get('/').text
            for future in ('Panel de monitoreo','Actividades de mantenimiento','Próximas inspecciones','<canvas','bridge-drawing'):
                self.assertNotIn(future,home)
            self.assertEqual(self.client.get('/rules').status_code,200 if role=='dom' else 403)
            self.assertEqual(self.rule(threshold='0.4').status_code,302 if role=='dom' else 403)
            before=self.snapshot()
            for path in ('/maintenance','/inspection-plans'):
                self.assertEqual(self.client.get(path).status_code,404)
                self.assertEqual(self.post(path,dict(cancel='1')).status_code,404)
                self.assertEqual(self.client.post(path,data={}).status_code,404)
            self.assertEqual(self.snapshot(),before)

    def test_numeric_boundaries_engine_reused(self):
        Ev2Tests.test_numeric_levels_positive_negative_and_exact_limits(self)

    def test_reference_snapshot_engine_reused(self):
        Ev2Tests.test_reference_offset_snapshot_missing_and_invalid(self)

    def test_visual_engine_reused(self):
        Ev2Tests.test_visual_categories_and_configured_alerts(self)

    def test_configurable_thresholds_versions_disable_and_invalid_rules(self):
        for severity,threshold in [('Atención','7'),('Alerta','11'),('Crítico','19')]:
            self.assertEqual(self.rule(severity=severity,threshold=threshold).status_code,302)
        self.post('/measurements',self.measurement(value='7'))
        previous=dict(self.db.execute('SELECT * FROM alerts').fetchone())
        old_rule=dict(self.db.execute('SELECT * FROM rules WHERE id=?',(previous['rule_id'],)).fetchone())
        self.rule(severity='Atención',threshold='8')
        self.assertEqual(dict(self.db.execute('SELECT * FROM alerts').fetchone()),previous)
        old=dict(self.db.execute('SELECT * FROM rules WHERE id=?',(previous['rule_id'],)).fetchone())
        self.assertEqual({k:v for k,v in old.items() if k!='active'},{k:v for k,v in old_rule.items() if k!='active'})
        self.assertEqual(old['active'],0)
        for value,expected in [('7',None),('8','Atención'),('11','Alerta'),('19','Crítico')]:
            before=self.count('alerts');self.post('/measurements',self.measurement(value=value))
            self.assertEqual(self.count('alerts')-before,int(expected is not None))
            if expected:self.assertEqual(self.db.execute('SELECT severity FROM alerts ORDER BY id DESC').fetchone()[0],expected)
        active=self.db.execute("SELECT id FROM rules WHERE severity='Crítico' AND active=1").fetchone()[0]
        self.assertEqual(self.post('/rules',dict(disable=str(active))).status_code,302)
        self.post('/measurements',self.measurement(value='30'))
        self.assertEqual(self.db.execute('SELECT severity FROM alerts ORDER BY id DESC').fetchone()[0],'Alerta')
        before=self.count('rules')
        for value in ('-1','nan','inf','no-numero','12'):
            self.rule(threshold=value,severity='Atención');self.assertEqual(self.count('rules'),before)

    def test_capture_invalid_missing_no_rule_and_api_dedup_traceability(self):
        self.rule(threshold='5')
        headers={'Authorization':'Bearer test-key'}
        data=self.measurement(value='5',external_id='ev3-api',simulated=True)
        result=self.client.post('/api/v1/measurements',json=data,headers=headers)
        self.assertEqual(result.status_code,201)
        self.assertEqual(self.client.post('/api/v1/measurements',json=data,headers=headers).status_code,400)
        a=self.db.execute('SELECT a.*,c.bridge_id AS sensor_bridge FROM alerts a JOIN measurements m ON m.id=a.measurement_id JOIN sensors s ON s.id=m.sensor_id JOIN components c ON c.id=s.component_id').fetchone()
        self.assertEqual(a['measurement_id'],result.json['id']);self.assertEqual(a['bridge_id'],a['sensor_bridge'])
        self.assertEqual(self.count('alerts'),1)
        for status in ('invalido','no_disponible'):
            self.post('/measurements',self.measurement(value='500' if status=='invalido' else '',status=status))
        self.assertEqual(self.count('measurements'),3);self.assertEqual(self.count('alerts'),1)
        before=self.count('measurements')
        for changes in (dict(value='-1'),dict(value='nan'),dict(unit='mm/s'),dict(measured_at='2099-01-01T00:00:00Z'),dict(bridge_code='P2',kind='vibracion')):
            self.assertEqual(self.client.post('/api/v1/measurements',json=self.measurement(external_id='bad',**changes),headers=headers).status_code,400)
            self.assertEqual(self.count('measurements'),before)
        self.post('/measurements',self.measurement(sensor_code='S2',unit='°',value='1'))
        self.assertEqual(self.db.execute('SELECT evaluation FROM measurements ORDER BY id DESC').fetchone()[0],'Sin regla aplicable')
        self.assertEqual(self.count('alerts'),1)

    def test_http_provider_two_bridges_dedup(self):
        Ev2Tests.test_ev2_provider_flow_both_bridges(self)

    def test_provider_inconsistent_records_and_savepoints(self):
        from tests.test_iot_update import IotUpdateTests
        self.contract=lambda *args,**kw:IotUpdateTests.contract(self,*args,**kw)
        IotUpdateTests.test_provider_rejects_inconsistent_and_missing_identity_with_evidence(self)

    def test_alert_followup_roles_and_csrf(self):
        self.rule();self.post('/measurements',self.measurement())
        self.assertEqual(self.client.post('/rules',data=dict(disable='1',csrf='wrong')).status_code,400)
        self.login('inspector')
        self.assertEqual(self.post('/alerts/1',dict(note='Observación documentada')).status_code,302)
        self.assertEqual(self.post('/alerts/1',dict(note='No autorizado',status='Resuelta')).status_code,403)
        self.assertEqual(self.db.execute('SELECT status FROM alerts WHERE id=1').fetchone()[0],'Activa')
        self.login('worker');self.assertEqual(self.client.get('/alerts/1').status_code,200)
        self.assertEqual(self.post('/alerts/1',dict(note='No autorizado')).status_code,403)
        self.login('dom')
        for status in ('En atención','Resuelta'):
            self.assertEqual(self.post('/alerts/1',dict(note='Revisión y justificación',status=status)).status_code,302)
        self.assertEqual(self.count('alert_notes'),3)
        self.assertEqual(self.db.execute('SELECT status FROM alerts WHERE id=1').fetchone()[0],'Resuelta')
        self.assertNotIn('Planificar actividad',self.client.get('/alerts/1').text)

    def test_forged_plan_rejected_before_inspection_and_photos(self):
        self.app.config['PROJECT_STAGE']='full'
        self.post('/inspection-plans',dict(bridge_id='1',component_id='1',inspector_id='2',planned_date='2026-11-10',description='Futura'))
        self.app.config['PROJECT_STAGE']=EV3_STAGE
        self.login('inspector');before=self.snapshot()
        image=io.BytesIO();Image.new('RGB',(16,16)).save(image,'PNG');image.seek(0)
        self.assertEqual(self.inspection(plan_id='1',photos=(image,'foto.png')).status_code,200)
        self.assertEqual(self.snapshot(),before);self.assertEqual(list((self.path/'photos').iterdir()),[])

    def test_switching_three_modes_preserves_rows_and_has_no_future_queries(self):
        self.config();self.post('/measurements',self.measurement(value='3'))
        before=self.snapshot();real_connect=sqlite3.connect;statements=[]
        def traced(*args,**kwargs):
            c=real_connect(*args,**kwargs);c.set_trace_callback(statements.append);return c
        for stage in (CUTOFF_STAGE,EV3_STAGE,'full'):
            candidate=create_app(dict(self.app.config,PROJECT_STAGE=stage));client=candidate.test_client()
            with client.session_transaction() as session:session['user_id']=1;session['csrf']='check'
            with patch('app.sqlite3.connect',side_effect=traced):
                self.assertEqual(client.get('/').status_code,200)
                self.assertEqual(client.get('/alerts/1').status_code,404 if stage==CUTOFF_STAGE else 200)
                self.assertEqual(client.get('/inspections').status_code,200)
            self.assertEqual(before,self.snapshot())
            if stage==EV3_STAGE:
                forbidden=[q for q in statements if q.lstrip().upper().startswith('SELECT') and any(x in q.lower() for x in ('from tasks','from inspection_plans'))]
                self.assertEqual(forbidden,[])
            statements.clear()

    def test_cron_ev3_evaluates_both_bridges_and_deduplicates(self):
        self.db.execute("INSERT INTO sensors(component_id,code,kind,unit) VALUES(2,'S3','vibracion','m/s²')");self.db.commit()
        self.rule(bridge_id='1',threshold='5');self.rule(bridge_id='2',threshold='5')
        records=[dict(self.measurement(sensor_code=code,value='6',external_id='cron-'+code),bridge_code=bridge,kind='vibracion',simulated=True) for code,bridge in [('S1','P1'),('S3','P2')]]
        self.app.config.update(CLOUD_PROVIDER=True,CRON_SECRET='only-for-tests')
        client=self.app.test_client()
        self.assertEqual(client.post('/internal/iot/pull').status_code,401)
        with patch('app.cloud_records',return_value=records):
            first=client.post('/internal/iot/pull',headers={'Authorization':'Bearer only-for-tests'})
            second=client.post('/internal/iot/pull',headers={'Authorization':'Bearer only-for-tests'})
        self.assertEqual(first.json,dict(received=2,duplicates=0,errors=[]))
        self.assertEqual(second.json,dict(received=0,duplicates=2,errors=[]))
        self.assertEqual(self.count('measurements'),2);self.assertEqual(self.count('alerts'),2)
        self.assertEqual([tuple(row) for row in self.db.execute('SELECT bridge_id,severity FROM alerts ORDER BY bridge_id')],[(1,'Atención'),(2,'Atención')])

def load_tests(loader,standard_tests,pattern):
    return unittest.TestSuite(Ev3StageTests(name) for name in Ev3StageTests.__dict__ if name.startswith('test_'))
