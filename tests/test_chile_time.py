"""Fechas visibles y rangos locales; fixtures temporales, nunca producción."""
from datetime import datetime, timedelta
import re
import unittest
from app import EV3_STAGE
from display_time import chile_datetime, calendar_date, local_date_bounds
from tests.test_app import SystemTests
from tests.test_monitoring_ui import Links


class ChileTimeUnitTests(unittest.TestCase):
    def test_summer_winter_midnight_and_explicit_offsets(self):
        for source,expected in (
            ('2026-01-01T02:30:00Z','31/12/2025 23:30:00 (UTC-03:00)'),
            ('2026-06-01T03:30:00+00:00','31/05/2026 23:30:00 (UTC-04:00)'),
            ('2026-01-01T10:00:00-03:00','01/01/2026 10:00:00 (UTC-03:00)'),
            ('2026-04-05T02:30:00Z','04/04/2026 23:30:00 (UTC-03:00)'),
            ('2026-04-05T03:30:00Z','04/04/2026 23:30:00 (UTC-04:00)'),
            ('2026-09-06T04:00:00Z','06/09/2026 01:00:00 (UTC-03:00)'),
        ):
            self.assertEqual(chile_datetime(source),expected)
            self.assertEqual(chile_datetime(datetime.fromisoformat(source)),expected)

    def test_unknown_zone_bad_values_and_calendar_dates(self):
        for value in ('2026-01-01T12:00:00','2026-01-01'):
            self.assertEqual(chile_datetime(value),value+' (zona horaria no registrada)')
        self.assertEqual(chile_datetime('texto histórico'),'texto histórico (fecha no interpretable)')
        self.assertEqual(chile_datetime(None),'No disponible')
        self.assertEqual(calendar_date('2026-01-01'),'01/01/2026')

    def test_local_bounds_dst_and_invalid_dates(self):
        for day,start,end,hours in (
            ('2026-01-01','2026-01-01T03:00:00+00:00','2026-01-02T03:00:00+00:00',24),
            ('2026-06-01','2026-06-01T04:00:00+00:00','2026-06-02T04:00:00+00:00',24),
            ('2026-09-06','2026-09-06T04:00:00+00:00','2026-09-07T03:00:00+00:00',23),
            ('2026-04-04','2026-04-04T03:00:00+00:00','2026-04-05T04:00:00+00:00',25),
        ):
            self.assertEqual(local_date_bounds(day,day),(start,end))
            self.assertEqual((datetime.fromisoformat(end)-datetime.fromisoformat(start)).total_seconds()/3600,hours)
        self.assertEqual(local_date_bounds(),(None,None))
        self.assertEqual(local_date_bounds('2026-01-01','')[1],None)
        self.assertEqual(local_date_bounds('','2026-01-01')[0],None)
        for start,end in [('2026-02-30',''),('20260101',''),('2026-02-01','2026-01-01'),('','9999-12-31')]:
            with self.assertRaises(ValueError):local_date_bounds(start,end)


class ChileTimeViewTests(unittest.TestCase):
    setUp=SystemTests.setUp
    tearDown=SystemTests.tearDown
    post=SystemTests.post
    login=SystemTests.login
    count=SystemTests.count
    rule=SystemTests.rule
    inspection=SystemTests.inspection

    def test_local_day_filters_pagination_and_unchanged_utc(self):
        self.app.config['PROJECT_STAGE']=EV3_STAGE
        self.rule()
        rid=self.db.execute('SELECT id FROM rules ORDER BY id DESC').fetchone()[0]
        for day in ('2026-01-01','2026-06-01','2026-09-06','2026-04-04'):
            self.db.execute('DELETE FROM alerts');self.db.execute('DELETE FROM measurements')
            lower,upper=map(datetime.fromisoformat,local_date_bounds(day,day))
            stamps=[lower-timedelta(seconds=1),lower,lower+timedelta(seconds=1),upper-timedelta(seconds=1),upper]
            stamps.extend(lower+timedelta(minutes=n) for n in range(1,21))
            expected=[]
            for instant in stamps:
                stamp=instant.isoformat(timespec='seconds')
                mid=self.db.execute("INSERT INTO measurements(sensor_id,value,unit,measured_at,status,simulated,created_at) VALUES(1,9,'m/s²',?,'valido',1,?)",(stamp,stamp)).lastrowid
                aid=self.db.execute("INSERT INTO alerts(bridge_id,rule_id,measurement_id,created_at,simulated,standard,severity,status) VALUES(1,?,?,?,1,'EV2','Atención','Activa')",(rid,mid,stamp)).lastrowid
                if lower<=instant<upper:expected.append((instant,mid,aid))
            self.db.commit()
            before=[tuple(row) for row in self.db.execute('SELECT * FROM measurements ORDER BY id')]
            expected.sort(reverse=True)
            for path,column,pattern in (('/measurements',1,r'aria-label="Ver detalle de medición (\d+)"'),('/alerts',2,r'class="row-link alert-row" href="/alerts/(\d+)"')):
                query=f'{path}?bridge_id=1&from={day}&to={day}'
                first=self.client.get(query);self.assertEqual(first.status_code,200)
                ids=[int(i) for i in re.findall(pattern,first.text)];self.assertEqual(ids,[row[column] for row in expected[:20]])
                link=next(a['href'] for a in Links(first.text).links if a.get('rel')=='next')
                for part in ('bridge_id=1','from='+day,'to='+day,'page=2'):self.assertIn(part,link)
                second=self.client.get(link).text
                self.assertEqual([int(i) for i in re.findall(pattern,second)],[row[column] for row in expected[20:]])
                self.assertNotIn('rel="next"',second)
                self.assertIn(chile_datetime(expected[0][0]),first.text)
                # Abiertos por un solo extremo: borde incluido y fin excluido.
                for suffix in ('from='+day,'to='+day):self.assertEqual(self.client.get(path+'?'+suffix).status_code,200)
                for suffix in ('from=2026-02-30','from=2026-02-02&to=2026-01-01','to=9999-12-31'):self.assertEqual(self.client.get(path+'?'+suffix).status_code,400)
            self.assertEqual(before,[tuple(row) for row in self.db.execute('SELECT * FROM measurements ORDER BY id')])

    def test_all_visible_timestamps_and_unknown_history_are_preserved(self):
        self.app.config['PROJECT_STAGE']=EV3_STAGE
        self.rule();rid=self.db.execute('SELECT id FROM rules ORDER BY id DESC').fetchone()[0]
        stamp='2026-01-01T02:30:00+00:00';text='31/12/2025 23:30:00 (UTC-03:00)'
        mid=self.db.execute("INSERT INTO measurements(sensor_id,value,unit,measured_at,status,simulated,created_at) VALUES(1,9,'m/s²',?,'valido',1,?)",(stamp,stamp)).lastrowid
        aid=self.db.execute("INSERT INTO alerts(bridge_id,rule_id,measurement_id,created_at,simulated,standard,severity,status) VALUES(1,?,?,?,1,'EV2','Atención','Activa')",(rid,mid,stamp)).lastrowid
        self.db.execute('UPDATE rules SET created_at=?',(stamp,))
        self.db.execute("INSERT INTO alert_notes(alert_id,author_id,created_at,note) VALUES(?,1,?,'Seguimiento histórico')",(aid,stamp))
        self.db.execute("INSERT INTO audit(author,action,entity,details,created_at) VALUES('DOM','Revisión','alerts','Detalle original',?)",(stamp,))
        self.db.execute("INSERT INTO inspections(bridge_id,component_id,inspected_at,inspector_id,condition,description,simulated,standard) VALUES(1,1,?,2,'Alta','Hallazgo conservado',1,'EV2')",(stamp,))
        iid=self.db.execute('SELECT id FROM inspections ORDER BY id DESC').fetchone()[0]
        self.db.commit()
        tables=('measurements','alerts','rules','alert_notes','inspections','audit')
        before={t:[tuple(row) for row in self.db.execute('SELECT * FROM '+t+' ORDER BY id')] for t in tables}
        for path in ('/measurements',f'/measurements/{mid}','/alerts',f'/alerts/{aid}','/rules','/inspections',f'/inspections/{iid}','/audit'):
            response=self.client.get(path);self.assertEqual(response.status_code,200)
            self.assertIn(text,response.text,path);self.assertNotIn(stamp,response.text,path)
        self.app.config['PROJECT_STAGE']='full'
        self.assertIn(text,self.client.get('/').text)
        self.assertEqual(before,{t:[tuple(row) for row in self.db.execute('SELECT * FROM '+t+' ORDER BY id')] for t in tables})
        self.db.execute('UPDATE measurements SET measured_at=? WHERE id=?',('2026-01-01T01:00:00',mid));self.db.commit()
        self.assertIn('2026-01-01T01:00:00 (zona horaria no registrada)',self.client.get(f'/measurements/{mid}').text)
        self.assertNotIn(f'aria-label="Ver detalle de medición {mid}"',self.client.get('/measurements?from=2026-01-01&to=2026-01-01').text)


def load_tests(loader, standard_tests, pattern):
    return unittest.TestSuite(loader.loadTestsFromTestCase(cls) for cls in (ChileTimeUnitTests,ChileTimeViewTests))
