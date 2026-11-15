"""Cierre técnico D7/B-11/B-14: fixtures aislados, sin UAT ni producción."""
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import threading
import unittest
from contextlib import closing
from unittest.mock import patch

from PIL import Image
from app import create_app, CUTOFF_STAGE, EV3_STAGE, EV3_CLOSURE_STAGE
from cloud_provider import cloud_records
from mock_provider import make_server, demo_records
from reference_data import BRIDGE_REFERENCES
from reference_migration import LEGACY_CODES, rename_reference_identifiers
from tests.test_app import SystemTests
from tools.migrate_to_supabase import TABLES


def snapshot(test):
    test.db.commit()
    return {name:[dict(row) for row in test.db.execute('SELECT * FROM '+name+' ORDER BY id')] for name in TABLES}


def legacy_inventory(test):
    for bid,old in enumerate(LEGACY_CODES,1):
        test.db.execute('UPDATE bridges SET code=?,name=?,location=? WHERE id=?',(old,BRIDGE_REFERENCES[bid-1][1],BRIDGE_REFERENCES[bid-1][2],bid))
    test.db.execute("UPDATE components SET name='Tablero' WHERE id=2")
    for sid,kind in [(1,'vibracion'),(2,'inclinacion')]:
        test.db.execute('UPDATE sensors SET code=? WHERE id=?',(LEGACY_CODES[0]+'-'+kind.upper(),sid))
    for kind,unit in [('vibracion','m/s²'),('inclinacion','°')]:
        test.db.execute('INSERT INTO sensors(component_id,code,kind,unit) VALUES(2,?,?,?)',(LEGACY_CODES[1]+'-'+kind.upper(),kind,unit))
    test.db.commit()


class ClosureStageTests(SystemTests):
    def setUp(self):
        super().setUp()
        self.app.config['PROJECT_STAGE']=EV3_CLOSURE_STAGE

    def tearDown(self):
        try:
            self.evidence=getattr(self,'evidence',{}) | {
                'measurements':self.count('measurements'),'inspections':self.count('inspections'),
                'rules':self.count('rules'),'alerts':self.count('alerts'),'tasks':self.count('tasks'),
                'task_records':[dict(row) for row in self.db.execute('SELECT id,bridge_id,component_id,alert_id,assignee_id,planned_date,status FROM tasks ORDER BY id')],
                'alert_states':[dict(row) for row in self.db.execute('SELECT id,bridge_id,rule_id,measurement_id,inspection_id,status,severity FROM alerts ORDER BY id')],
            }
        finally:super().tearDown()

    def test_cutoff_configuration_roles_and_no_plan_queries(self):
        config=dict(self.app.config);config.pop('PROJECT_STAGE')
        with patch.dict(os.environ,{'PROJECT_STAGE':EV3_CLOSURE_STAGE}):
            self.assertEqual(create_app(config).config['PROJECT_STAGE'],EV3_CLOSURE_STAGE)
            self.assertEqual(create_app(dict(config,PROJECT_STAGE=EV3_STAGE)).config['PROJECT_STAGE'],EV3_STAGE)
        real_connect=sqlite3.connect;queries=[]
        def traced(*args,**kw):
            connection=real_connect(*args,**kw);connection.set_trace_callback(queries.append);return connection
        for name in ('dom','inspector','worker'):
            self.login(name);before=snapshot(self)
            with patch('app.sqlite3.connect',side_effect=traced):
                for path in ('/','/bridges','/measurements','/alerts','/inspections','/maintenance'):
                    result=self.client.get(path);self.assertEqual(result.status_code,200,(name,path))
                    self.assertNotIn('href="/inspection-plans"',result.text)
                    self.assertNotIn('Próximas inspecciones programadas',result.text)
                    self.assertNotIn('name="plan_id"',result.text)
                self.assertEqual(self.client.get('/rules').status_code,200 if name=='dom' else 403)
                self.assertEqual(self.client.get('/inspection-plans').status_code,404)
                self.assertEqual(self.client.post('/inspection-plans',data={}).status_code,404)
            self.assertEqual(before,snapshot(self))
        self.assertFalse([q for q in queries if q.lstrip().upper().startswith('SELECT') and 'from inspection_plans' in q.lower()])
        self.login('inspector');before=snapshot(self)
        self.assertEqual(self.inspection(plan_id='999').status_code,200)
        self.assertEqual(before,snapshot(self))

    def test_dashboard_latest_readings_alert_states_and_visual_separation(self):
        self.rule();self.rule(bridge_id='2')
        self.post('/measurements',self.measurement(value='1.25'))
        self.post('/measurements',self.measurement(value='6.25',measured_at='2026-01-03T13:00:00Z'))
        self.post('/measurements',self.measurement(sensor_code='S2',unit='°',value='',status='no_disponible'))
        self.db.execute("INSERT INTO sensors(component_id,code,kind,unit) VALUES(2,'S3','vibracion','m/s²')");self.db.commit()
        self.post('/measurements',self.measurement(sensor_code='S3',value='7.5'))
        self.inspection(description='Observación visual específica del tablero')
        for role in ('dom','inspector','worker'):
            self.login(role);before=snapshot(self)
            page=self.client.get('/').text
            for text in ('Panel de monitoreo','Puente de prueba','Segundo puente','6.25','7.5','No disponible','Condiciones visuales','Observación visual específica del tablero'):
                self.assertIn(text,page)
            self.assertNotIn('1.25',page)
            for link in ('/bridges/1','/measurements?bridge_id=1','/inspections?bridge_id=1','/alerts/1','/alerts/2','/inspections/1'):
                self.assertIn('href="'+link+'"',page)
            self.assertEqual(before,snapshot(self))
        self.login('dom');self.post('/alerts/1',dict(note='Revisión explícita DOM',status='Resuelta'))
        page=self.client.get('/').text
        self.assertNotIn('href="/alerts/1"',page);self.assertIn('href="/alerts/2"',page)
        self.assertIn('Sin alertas abiertas',page)

    def test_dashboard_pending_assignments_and_empty_states(self):
        page=self.client.get('/').text
        for text in ('Sin datos','No existen reglas activas','No hay alertas abiertas','Sin actividades pendientes','Sin inspecciones visuales'):
            self.assertIn(text,page)
        self.task(alert_id='',description='Asignada a mantención A')
        self.task(alert_id='',assignee_id='4',description='Asignada a mantención B')
        self.login('worker');page=self.client.get('/').text
        self.assertIn('Asignada a mantención A',page);self.assertNotIn('Asignada a mantención B',page)
        self.post('/maintenance',dict(id='1',status='Completada'))
        self.assertNotIn('Asignada a mantención A',self.client.get('/').text)
        self.login('inspector');self.assertIn('Asignada a mantención B',self.client.get('/').text)
        self.assertEqual(self.post('/maintenance',dict(id='2',status='Completada')).status_code,403)
        self.login('dom');self.assertIn('Asignada a mantención B',self.client.get('/').text)

    def test_dom_forms_edit_reassignment_and_assigned_worker_followup(self):
        self.rule();self.post('/measurements',self.measurement())
        html=self.client.get('/maintenance').text
        for field in ('bridge_id','component_id','alert_id','assignee_id','planned_date','description','csrf'):
            self.assertIn('name="'+field+'"',html)
        self.assertIn('data-bridge="1"',html)
        self.assertEqual(self.task().status_code,302)
        original=dict(self.db.execute('SELECT * FROM tasks WHERE id=1').fetchone())
        self.assertEqual(self.post('/maintenance',dict(id='1',description='Reasignada por DOM',assignee_id='4',planned_date='2026-11-24',status='En ejecución')).status_code,302)
        task=dict(self.db.execute('SELECT * FROM tasks WHERE id=1').fetchone())
        self.assertEqual((task['description'],task['assignee_id'],task['planned_date'],task['status']),('Reasignada por DOM',4,'2026-11-24','En ejecución'))
        for field in ('id','bridge_id','component_id','alert_id','author_id','created_at'):
            self.assertEqual(task[field],original[field])
        self.login('worker');self.assertNotIn('Reasignada por DOM',self.client.get('/maintenance').text)
        self.assertEqual(self.post('/maintenance',dict(id='1',status='Completada')).status_code,403)
        self.login('other');page=self.client.get('/maintenance').text
        self.assertIn('Reasignada por DOM',page);self.assertIn('name="status"',page)
        for field in ('description','planned_date','assignee_id'):
            self.assertNotIn('name="'+field+'"',page)
        self.assertEqual(self.post('/maintenance',dict(id='1',status='Completada',description='Alteración no permitida',assignee_id='3',planned_date='2099-01-01',bridge_id='2',component_id='2',alert_id='')).status_code,302)
        task=dict(self.db.execute('SELECT * FROM tasks WHERE id=1').fetchone())
        self.assertEqual(task['status'],'Completada')
        for field in ('description','planned_date','assignee_id','bridge_id','component_id','alert_id'):
            self.assertEqual(task[field],dict(original,description='Reasignada por DOM',planned_date='2026-11-24',assignee_id=4)[field])
        self.assertEqual(self.db.execute('SELECT status FROM alerts WHERE id=1').fetchone()[0],'Activa')
        self.assertIn('href="/alerts/1"',self.client.get('/maintenance').text)
        self.login('dom');self.assertIn('Reasignada por DOM',self.client.get('/alerts/1').text)

    def test_maintenance_validation_csrf_roles_and_cross_bridge_relations(self):
        self.rule();self.post('/measurements',self.measurement())
        invalid=[dict(description=''),dict(bridge_id='999'),dict(component_id='2'),dict(bridge_id='2',component_id='2'),dict(assignee_id='2'),dict(assignee_id='999'),dict(planned_date='2026-02-30'),dict(planned_date='sin-fecha')]
        for values in invalid:
            before=snapshot(self);self.assertEqual(self.task(**values).status_code,200)
            self.assertEqual(before,snapshot(self),values)
        self.assertEqual(self.client.post('/maintenance',data=dict(csrf='incorrecto',description='Sin token válido')).status_code,400)
        self.assertEqual(self.count('tasks'),0)
        self.assertEqual(self.task(description='<script>no ejecutar</script>').status_code,302)
        self.assertIn('&lt;script&gt;',self.client.get('/maintenance').text)
        for values in [dict(status='Otro'),dict(status='Pendiente',description='',planned_date='2026-11-24',assignee_id='3'),dict(status='Pendiente',description='x',planned_date='bad',assignee_id='3'),dict(status='Pendiente',description='x',planned_date='2026-11-24',assignee_id='1')]:
            before=snapshot(self);self.assertEqual(self.post('/maintenance',dict(id='1',**values)).status_code,200)
            self.assertEqual(before,snapshot(self))
        for role in ('inspector','other'):
            self.login(role);before=snapshot(self)
            self.assertEqual(self.task().status_code,403)
            self.assertEqual(self.post('/maintenance',dict(id='1',status='Completada')).status_code,403)
            self.assertEqual(before,snapshot(self))

    def test_maintenance_filters_inspector_readonly_and_alert_stays_open(self):
        self.rule();self.post('/measurements',self.measurement())
        self.task(description='Actividad primer puente')
        self.task(bridge_id='2',component_id='2',alert_id='',description='Actividad segundo puente',assignee_id='4')
        self.login('inspector')
        page=self.client.get('/maintenance?bridge_id=1').text
        self.assertIn('Actividad primer puente',page);self.assertNotIn('Actividad segundo puente',page)
        self.assertNotIn('Planificar actividad',page);self.assertNotIn('Actualizar actividad',page)
        self.assertIn('Actividad segundo puente',self.client.get('/maintenance?bridge_id=2').text)
        self.assertNotIn('Actividad primer puente',self.client.get('/maintenance?bridge_id=999').text)
        self.login('worker');self.post('/maintenance',dict(id='1',status='En ejecución'));self.post('/maintenance',dict(id='1',status='Completada'))
        self.assertEqual(self.db.execute('SELECT status FROM alerts WHERE id=1').fetchone()[0],'Activa')
        self.assertEqual(self.db.execute('SELECT status FROM tasks WHERE id=1').fetchone()[0],'Completada')

    def test_historical_stages_and_four_mode_switch_preserve_rows(self):
        self.rule();self.post('/measurements',self.measurement());self.inspection();self.task()
        before=snapshot(self)
        for stage in (CUTOFF_STAGE,EV3_STAGE,EV3_CLOSURE_STAGE,'full'):
            candidate=create_app(dict(self.app.config,PROJECT_STAGE=stage));client=candidate.test_client()
            with client.session_transaction() as session:session['user_id']=1;session['csrf']='only-tests'
            home=client.get('/').text
            advanced=stage in (EV3_CLOSURE_STAGE,'full')
            self.assertEqual('Actividades de mantenimiento pendientes' in home,advanced)
            self.assertEqual('Próximas inspecciones programadas' in home,stage=='full')
            self.assertEqual(client.get('/maintenance').status_code,200 if advanced else 404)
            self.assertEqual(client.get('/rules').status_code,404 if stage==CUTOFF_STAGE else 200)
            self.assertEqual(client.get('/inspection-plans').status_code,200 if stage=='full' else 404)
            self.assertEqual(before,snapshot(self))

    def test_reference_seed_providers_identity_and_dedup(self):
        fresh=create_app(dict(self.app.config,DATABASE=str(self.path/'reference.sqlite'),UPLOAD_FOLDER=str(self.path/'reference-photos')))
        runner=fresh.test_cli_runner()
        self.assertEqual(runner.invoke(args=['init-db']).exit_code,0)
        result=runner.invoke(args=['seed-demo']);self.assertEqual(result.exit_code,0,result.output)
        client=fresh.test_client()
        with client.session_transaction() as session:session['user_id']=1;session['csrf']='only-tests'
        batch=demo_records();cloud=cloud_records()
        expected={item[0] for item in BRIDGE_REFERENCES}
        self.assertEqual({row['bridge_code'] for row in batch},expected)
        self.assertEqual({row['bridge_code'] for row in cloud},expected)
        for row in batch+cloud:
            self.assertNotIn('simulated',row)
            self.assertEqual(row['sensor_code'],row['bridge_code']+'-'+row['kind'].upper())
        server=make_server(port=0,records=batch);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            fresh.config['PROVIDER_URL']=f'http://127.0.0.1:{server.server_port}/measurements'
            self.assertEqual(client.post('/provider/pull',data=dict(csrf='only-tests')).status_code,302)
            with closing(sqlite3.connect(fresh.config['DATABASE'])) as connection:
                self.assertEqual(connection.execute('SELECT count(*) FROM measurements').fetchone()[0],4,client.get('/measurements').text)
            self.assertEqual(client.post('/provider/pull',data=dict(csrf='only-tests')).status_code,302)
            fresh.config.update(CLOUD_PROVIDER=True,CRON_SECRET='only-tests')
            with patch('app.cloud_records',return_value=cloud):
                first=client.post('/internal/iot/pull',headers={'Authorization':'Bearer only-tests'})
                second=client.post('/internal/iot/pull',headers={'Authorization':'Bearer only-tests'})
            self.assertEqual(first.json,dict(received=4,duplicates=0,errors=[]))
            self.assertEqual(second.json,dict(received=0,duplicates=4,errors=[]))
            with closing(sqlite3.connect(fresh.config['DATABASE'])) as connection:
                self.assertEqual(connection.execute('SELECT code FROM bridges ORDER BY id').fetchall(),[(item[0],) for item in BRIDGE_REFERENCES])
                counts={table:connection.execute('SELECT count(*) FROM '+table).fetchone()[0] for table in ('bridges','components','sensors','rules','measurements','alerts')}
                self.assertEqual(counts,dict(bridges=2,components=6,sensors=4,rules=18,measurements=8,alerts=8))
                self.assertNotIn('simulated',{r[1] for r in connection.execute('PRAGMA table_info(measurements)')})
                self.assertEqual(connection.execute('PRAGMA foreign_key_check').fetchall(),[])
                self.evidence={'reference_fixture':counts,'provider_first':first.json,'provider_repeat':second.json}
        finally:server.shutdown();server.server_close();thread.join()

    def test_mockups_and_interfaces_remove_identifiers_and_banner(self):
        for name in ('docs/mockups.html','docs/mockups-full.html'):
            page=Path(name).read_text(encoding='utf-8')
            self.assertNotIn('Entorno de demostración',page)
            for code in LEGACY_CODES:self.assertNotIn(code,page)
            for code,_,_ in BRIDGE_REFERENCES:self.assertIn(code,page)
        for path in ('/','/bridges','/measurements','/alerts','/rules','/inspections','/maintenance'):
            self.assertNotIn('Entorno de demostración',self.client.get(path).text)
        for name in ('cloud_provider.py','mock_provider.py','reference_data.py','tools/build_mockups.py'):
            source=Path(name).read_text(encoding='utf-8')
            for code in LEGACY_CODES:self.assertNotIn(code,source)

    def test_d7_migration_dryrun_apply_idempotence_and_history_preservation(self):
        self.rule();self.post('/measurements',self.measurement())
        image=io.BytesIO();Image.new('RGB',(12,12)).save(image,'PNG');image.seek(0)
        self.inspection(photos=(image,'foto.png'));self.task()
        legacy_inventory(self);before=snapshot(self)
        photo_hashes={p.name:p.read_bytes() for p in (self.path/'photos').iterdir()}
        plan=rename_reference_identifiers(self.db)
        self.assertEqual(len(plan),6);self.assertEqual(before,snapshot(self))
        self.assertEqual(rename_reference_identifiers(self.db,apply=True),plan)
        expected=json.loads(json.dumps(before))
        for change in plan:
            record=next(row for row in expected[change['table']] if row['id']==change['id']);record['code']=change['new']
        self.assertEqual(expected,snapshot(self))
        self.assertEqual(rename_reference_identifiers(self.db,apply=True),[])
        self.assertEqual(photo_hashes,{p.name:p.read_bytes() for p in (self.path/'photos').iterdir()})

    def test_d7_migration_rejects_collision_manual_and_partial_inventory(self):
        legacy_inventory(self)
        mutations=[("UPDATE bridges SET code='PM-001' WHERE id=2","UPDATE bridges SET code='DEM-02' WHERE id=2"),
                   ("UPDATE sensors SET code='PM-001-VIBRACION' WHERE id=3","UPDATE sensors SET code='DEM-02-VIBRACION' WHERE id=3"),
                   ("UPDATE bridges SET name='Personalizado' WHERE id=1","UPDATE bridges SET name='Puente Estero Norte' WHERE id=1"),
                   ("UPDATE sensors SET code='PERSONALIZADO' WHERE id=2","UPDATE sensors SET code='DEM-01-INCLINACION' WHERE id=2")]
        for mutate,restore in mutations:
            self.db.execute(mutate);self.db.commit();before=snapshot(self)
            with self.assertRaises(ValueError):rename_reference_identifiers(self.db,apply=True)
            self.assertEqual(before,snapshot(self));self.db.execute(restore);self.db.commit()

    def test_d7_cli_readonly_default_explicit_backup_and_apply(self):
        legacy_inventory(self);path=Path(self.app.config['DATABASE']);before=path.read_bytes()
        command=[sys.executable,'-X','utf8','tools/rename_reference_identifiers.py','--sqlite',str(path)]
        dry=subprocess.run(command,text=True,capture_output=True,encoding='utf-8')
        self.assertEqual(dry.returncode,0,dry.stderr);self.assertFalse(json.loads(dry.stdout)['applied'])
        self.assertEqual(path.read_bytes(),before)
        denied=subprocess.run(command+['--apply'],text=True,capture_output=True,encoding='utf-8')
        self.assertNotEqual(denied.returncode,0);self.assertEqual(path.read_bytes(),before)
        backup=self.path/'before-d7.sqlite'
        applied=subprocess.run(command+['--apply','--backup',str(backup)],text=True,capture_output=True,encoding='utf-8')
        self.assertEqual(applied.returncode,0,applied.stderr)
        self.assertEqual(len(json.loads(applied.stdout)['changes']),6)
        with closing(sqlite3.connect(backup)) as connection:
            self.assertEqual(connection.execute('SELECT code FROM bridges ORDER BY id').fetchall(),[(code,) for code in LEGACY_CODES])
        repeated=subprocess.run(command,text=True,capture_output=True,encoding='utf-8')
        self.assertEqual(repeated.returncode,0,repeated.stderr);self.assertEqual(json.loads(repeated.stdout)['changes'],[])


def load_tests(loader,standard_tests,pattern):
    return unittest.TestSuite(ClosureStageTests(name) for name in ClosureStageTests.__dict__ if name.startswith('test_'))
