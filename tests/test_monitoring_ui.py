"""Regresiones de interfaz EV3 sobre SQLite temporal, sin datos operativos."""
import re
import sqlite3
import unittest
from html.parser import HTMLParser
from unittest.mock import patch
from app import CUTOFF_STAGE, EV3_STAGE
from tests.test_app import SystemTests
from tests.test_project_stage import Navigation

class Links(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.links=[]; self.feed(text)
    def handle_starttag(self, tag, attrs):
        if tag=='a': self.links.append(dict(attrs))

class MonitoringUiTests(SystemTests):
    def setUp(self):
        super().setUp(); self.app.config['PROJECT_STAGE']=EV3_STAGE

    def populated(self, count=45):
        self.rule(label='Límite operativo')
        rid=self.db.execute('SELECT id FROM rules ORDER BY id DESC').fetchone()[0]
        for n in range(count):
            # Registros nuevos exclusivamente en la base temporal del caso.
            mid=self.db.execute("INSERT INTO measurements(sensor_id,value,unit,measured_at,status,simulated,created_at) VALUES(1,9,'m/s²',?,'valido',1,?)",
                                (f'2026-01-{1+n//20:02d}T10:00:00+00:00',)*2).lastrowid
            self.db.execute("INSERT INTO alerts(bridge_id,rule_id,measurement_id,created_at,simulated,standard,severity,status) VALUES(1,?,?,?,1,'EV2','Atención','Activa')",
                            (rid,mid,f'2026-01-{1+n//20:02d}T10:00:00+00:00'))
        self.db.commit()

    def api(self, suffix=''):
        return self.client.get('/api/v1/alert-notifications'+suffix)

    def snapshot(self):
        return {t:[tuple(r) for r in self.db.execute('SELECT * FROM '+t+' ORDER BY id')]
                for t in ['rules','measurements','alerts','inspections','audit']}

    def test_pagination_real_limits_newest_first_and_boundaries(self):
        self.populated()
        original=sqlite3.connect; statements=[]
        def trace(*a,**kw):
            c=original(*a,**kw);c.set_trace_callback(statements.append);return c
        with patch('app.sqlite3.connect',side_effect=trace):
            pages=[self.client.get('/alerts?page='+str(p)).text for p in (1,2,3,999)]
        ids=[[int(i) for i in re.findall(r'class="row-link alert-row" href="/alerts/(\d+)"',p)] for p in pages]
        self.assertEqual(ids,[list(range(45,25,-1)),list(range(25,5,-1)),[5,4,3,2,1],[5,4,3,2,1]])
        self.assertIn('Página 1 de 3',pages[0]);self.assertNotIn('rel="prev"',pages[0]);self.assertNotIn('rel="next"',pages[2])
        selects=[q for q in statements if 'SELECT a.*' in q]
        self.assertEqual(len(selects),4);self.assertTrue(all('LIMIT 20 OFFSET' in q for q in selects))
        for value in ('0','-1','bad','999999999999999999999999999999'):
            self.assertEqual(self.client.get('/alerts?page='+value).status_code,400)

    def test_filters_persist_dates_severity_status_bridge_and_empty(self):
        self.populated(45)
        query='/alerts?bridge_id=1&severity=Atenci%C3%B3n&status=Activa&from=2026-01-01&to=2026-01-02'
        first=self.client.get(query);self.assertEqual(first.status_code,200)
        next_link=next(a['href'] for a in Links(first.text).links if a.get('rel')=='next')
        for part in ('bridge_id=1','severity=Atenci%C3%B3n','status=Activa','from=2026-01-01','to=2026-01-02','page=2'):
            self.assertIn(part,next_link)
        second=self.client.get(next_link).text
        self.assertIn('Página 2 de 2',second)
        for name,value in [('bridge_id','1'),('status','Activa'),('severity','Atención')]:
            self.assertRegex(second,r'(?:value="'+re.escape(value)+r'" selected|<option selected>'+re.escape(value)+r'</option>)')
        self.assertIn('No hay alertas',self.client.get('/alerts?bridge_id=2').text)
        self.assertIn('No hay alertas',self.client.get('/alerts?severity=Cr%C3%ADtico').text)
        for query in ('status=falso','severity=falsa','from=2026-02-30','from=2026-02-01&to=2026-01-01','bridge_id=1%27%20OR%201=1'):
            self.assertEqual(self.client.get('/alerts?'+query).status_code,400)
        self.db.execute("UPDATE alerts SET standard='historica' WHERE id=1");self.db.commit()
        self.assertIn('#1 ·',self.client.get('/alerts?severity=historica').text)

    def test_audit_pagination_and_roles(self):
        self.db.execute('DELETE FROM audit')
        for n in range(45):
            self.db.execute("INSERT INTO audit(author,action,entity,details,created_at) VALUES('DOM',?,'bridges','',?)",(f'Operación {n}',f'2026-01-{1+n//20:02d}'))
        self.db.commit()
        pages=[self.client.get('/audit?page='+str(p)).text for p in (1,2,3)]
        ids=[[int(i) for i in re.findall('data-audit-id="(\d+)"',p)] for p in pages]
        self.assertEqual([len(x) for x in ids],[20,20,5]);self.assertEqual(len(set(sum(ids,[]))),45)
        self.assertEqual(ids[0],sorted(ids[0],reverse=True))
        for user in ('inspector','worker'):
            self.login(user);self.assertEqual(self.client.get('/audit?page=2').status_code,403)
        self.login('dom');self.db.execute('DELETE FROM audit');self.db.commit()
        self.assertIn('No hay operaciones registradas',self.client.get('/audit').text)

    def test_notifications_baseline_batched_monotonic_and_no_writes(self):
        self.populated(25);before=self.snapshot()
        initial=self.api();self.assertEqual(initial.status_code,200)
        self.assertEqual(initial.json['alerts'],[]);self.assertEqual(initial.json['cursor'],'25')
        self.assertEqual(initial.json['open_count'],25);self.assertFalse(initial.json['has_more'])
        one=self.api('?after=0').json;two=self.api('?after='+one['cursor']).json
        self.assertTrue(one['has_more']);self.assertFalse(two['has_more'])
        self.assertEqual([len(one['alerts']),len(two['alerts'])],[20,5]);self.assertEqual(two['cursor'],'25')
        self.assertEqual(self.api('?after=25').json['alerts'],[])
        self.assertEqual(self.api('?after=9999').json['cursor'],'25');self.assertTrue(self.api('?after=9999').json['reset'])
        self.assertEqual(before,self.snapshot());self.assertIn('no-store',initial.headers['Cache-Control'])
        for cursor in ('-1','bad','1%27','999999999999999999999999999'):
            self.assertEqual(self.api('?after='+cursor).status_code,400)

    def test_notification_roles_login_reset_stage_gate_and_query_budget(self):
        self.populated(1)
        epoch=None
        for name in ('dom','inspector','worker'):
            self.login(name)
            self.assertEqual(self.api().status_code,200)
            self.assertEqual(self.api().json['alerts'],[])
            self.assertNotEqual(epoch,self.api().json['session_epoch']);epoch=self.api().json['session_epoch']
            self.assertIn('notification-bell',self.client.get('/').text)
        self.client=self.app.test_client();self.assertEqual(self.api().status_code,401)
        self.assertEqual(self.client.post('/api/v1/alert-notifications').status_code,400) # CSRF no se omite
        self.login('dom');original=sqlite3.connect;statements=[]
        def trace(*a,**kw):
            c=original(*a,**kw);c.set_trace_callback(statements.append);return c
        with patch('app.sqlite3.connect',side_effect=trace): self.api('?after=1')
        alert_reads=[q for q in statements if q.lstrip().upper().startswith('SELECT') and 'FROM alerts' in q]
        self.assertEqual(len(alert_reads),1)
        self.app.config['PROJECT_STAGE']=CUTOFF_STAGE
        before=self.snapshot()
        with patch('app.sqlite3.connect',side_effect=AssertionError('EV2 API no debe abrir la BD')):
            self.assertEqual(self.api().status_code,404)
        self.assertNotIn('notification-bell',self.client.get('/').text);self.assertEqual(before,self.snapshot())

    def test_measurement_and_visual_alert_traceability_and_tabs(self):
        self.rule();self.post('/measurements',self.measurement())
        for name in ('dom','inspector','worker'):
            self.login(name)
            self.assertIn('Alertas asociadas',self.client.get('/measurements/1').text)
            self.assertIn('href="/alerts/1"',self.client.get('/measurements/1').text)
            self.assertIn('/measurements/1',self.client.get('/alerts/1').text)
            self.assertIn('aria-label="Monitoreo"',self.client.get('/measurements/1').text)
            self.assertIn('Monitoreo',Navigation(self.client.get('/alerts/1').text).labels)
            self.assertNotIn('Reglas de alerta',Navigation(self.client.get('/alerts/1').text).labels) if name!='dom' else None
        self.login('dom');self.rule(kind='visual',label='Condición visual',condition='Alta')
        self.inspection();aid=self.db.execute('SELECT id FROM alerts WHERE inspection_id=1').fetchone()[0]
        self.assertIn('/inspections/1',self.client.get(f'/alerts/{aid}').text)
        self.app.config['PROJECT_STAGE']=CUTOFF_STAGE
        self.assertNotIn('Alertas asociadas',self.client.get('/measurements/1').text)

    def test_rules_versions_stay_separate_and_records_unchanged(self):
        self.rule(label='Versión anterior');self.rule(label='Versión vigente',threshold='6')
        before=self.snapshot();html=self.client.get('/rules').text
        current,history=html.split('<details class="panel rule-history">')
        self.assertIn('Reglas vigentes',current);self.assertIn('Versión vigente',current);self.assertNotIn('Versión anterior',current)
        self.assertIn('Versión anterior',history);self.assertIn('No vigente',history)
        self.assertEqual(before,self.snapshot())
        for name in ('inspector','worker'):
            self.login(name);self.assertEqual(self.client.get('/rules').status_code,403)

    def test_institutional_future_audit_preserves_historical_rows(self):
        self.db.execute("INSERT INTO audit(author,action,entity,details,created_at) VALUES('DOM','Consultar proveedor ficticio','provider','Descripción histórica original','2026-01-01')")
        self.db.commit()
        old=tuple(self.db.execute("SELECT * FROM audit WHERE action='Consultar proveedor ficticio'").fetchone())
        with patch('app.fetch_measurements',return_value=[]):
            self.assertEqual(self.post('/provider/pull').status_code,302)
        self.assertEqual(tuple(self.db.execute('SELECT * FROM audit WHERE id=?',(old[0],)).fetchone()),old)
        current=self.db.execute("SELECT details FROM audit WHERE action='Consultar proveedor IoT' ORDER BY id DESC").fetchone()
        self.assertIsNotNone(current);self.assertIn('Origen: proveedor simulado.',current[0])
        html=self.client.get('/audit').text
        self.assertIn('Consultar proveedor ficticio',html);self.assertIn('Descripción histórica original',html)
        for path in ('/','/measurements','/alerts','/rules','/audit'):
            html=self.client.get(path).text
            self.assertNotIn('Entorno de demostración',html)
            self.assertNotIn('proveedor académico',html)

def load_tests(loader, standard, pattern):
    return unittest.TestSuite(MonitoringUiTests(n) for n in MonitoringUiTests.__dict__ if n.startswith('test_'))
