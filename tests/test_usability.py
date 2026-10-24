import io
import re
import unittest
from datetime import datetime,timezone
from PIL import Image
from tests.test_app import SystemTests
from pilot_time import form_timestamp

class UsabilityTests(unittest.TestCase):
    setUp=SystemTests.setUp
    tearDown=SystemTests.tearDown
    login=SystemTests.login
    post=SystemTests.post
    count=SystemTests.count

    def test_clean_login_roles_first_post_and_csrf_race(self):
        for user in ('dom','inspector','worker'):
            a=self.app.test_client(); b=self.app.test_client()
            form=a.get('/login'); token=re.search(rb'name="csrf" value="([^"]+)"',form.data)[1].decode()
            cookie=a.get_cookie('session').value
            for path in ('/favicon.ico','/static/app.js','/does-not-exist','/bridges'):
                result=b.get(path)
                self.assertFalse(result.headers.get('Set-Cookie'),path);result.close()
            self.assertEqual(a.post('/login',data=dict(csrf=token,username=user,password='password-test')).status_code,302)
            with a.session_transaction() as s: fresh=s['csrf'];self.assertNotEqual(fresh,token)
            self.assertNotEqual(a.get_cookie('session').value,cookie)
            self.assertEqual(a.post('/logout',data=dict(csrf=fresh)).status_code,302)
            a.get('/login')
            bad=a.post('/login',data=dict(csrf=token,username='dom',password='password-test'))
            self.assertEqual(bad.status_code,400);self.assertIn(b'Volver a cargar el formulario',bad.data)
            self.assertEqual(a.post('/login',data=dict(csrf='wrong')).status_code,400)
        self.post('/logout');self.login('inspector')
        form=self.client.get('/inspections');self.assertIn(b'inspected_date',form.data)
        self.assertEqual(self.post('/inspections',dict(bridge_id=1,component_id=1,condition='Alta',description='Primera operacion',inspected_date='2026-01-02',inspected_time='12:00')).status_code,302)

    def test_filters_persistence_incompatible_sensor_and_details(self):
        self.db.execute("INSERT INTO sensors(component_id,code,kind,unit) VALUES(2,'otro-codigo','vibracion','m/s²')");self.db.commit()
        for code in ('S1','otro-codigo'):
            self.post('/measurements',dict(sensor_code=code,value=1,unit='m/s²',status='valido',measured_date='2026-01-02',measured_time='10:00'))
        html=self.client.get('/measurements').text
        self.assertIn('history-filters" >',html);self.assertIn('data-history-sensors',html)
        self.assertIn('data-bridge="2"',html)
        url='/measurements?bridge_id=1&sensor_id=1&from=2026-01-01&to=2026-01-03'
        html=self.client.get(url).text
        self.assertIn('history-filters" open',html)
        self.assertIn('value="1" selected',html);self.assertIn('value="2026-01-01"',html)
        self.assertIn('Ver detalle',html)
        html=self.client.get('/measurements?bridge_id=1&sensor_id=3').text
        self.assertIn('Sin mediciones disponibles',html)
        mid=self.db.execute('SELECT id FROM measurements WHERE sensor_id=1').fetchone()[0]
        self.assertIn('/inspections?bridge_id=1',self.client.get(f'/measurements/{mid}').text)
        self.assertIn('Sin inspecciones registradas.',self.client.get('/inspections?bridge_id=2').text)
        self.post('/inspections',dict(bridge_id=1,component_id=1,condition='Alta',description='Solo puente uno',inspected_date='2026-01-02',inspected_time='12:00'))
        self.assertIn('Solo puente uno',self.client.get('/inspections?bridge_id=1').text)
        self.assertNotIn('Solo puente uno',self.client.get('/inspections?bridge_id=2').text)

    def test_chilean_time_offsets_gaps_ambiguities_invalid_future(self):
        def legacy(value):
            dt=datetime.fromisoformat(value).astimezone(timezone.utc)
            if dt>datetime.now(timezone.utc):raise ValueError('futura')
            return dt.isoformat(timespec='seconds')
        def convert(day,time):return form_timestamp(dict(measured_date=day,measured_time=time),'measured',legacy)
        self.assertEqual(convert('2026-01-01','10:00'),'2026-01-01T13:00:00+00:00')
        self.assertEqual(convert('2026-06-01','10:00'),'2026-06-01T14:00:00+00:00')
        for day,time,msg in [('2026-09-06','00:30','no existe'),('2026-04-04','23:30','ambigua'),('2026-02-30','12:00','inválida'),('2026-01-01','25:00','inválida'),('2026-01-01','','Completa'),('2099-01-01','12:00','futura'),('9999-12-31','23:59','futura')]:
            with self.assertRaisesRegex(ValueError,msg):convert(day,time)

    def test_split_form_dates_photos_permissions_and_cutoff(self):
        self.app.config['PROJECT_STAGE']='cutoff_2026_10_26'
        self.post('/measurements',dict(sensor_code='S1',value=1,unit='m/s²',status='valido',measured_date='2026-06-01',measured_time='10:00'))
        self.assertEqual(self.db.execute('SELECT measured_at FROM measurements').fetchone()[0],'2026-06-01T14:00:00+00:00')
        self.assertEqual(self.count('alerts'),0)
        image=io.BytesIO();Image.new('RGB',(20,20),'blue').save(image,'PNG');image.seek(0)
        result=self.post('/inspections',dict(bridge_id=1,component_id=1,condition='Alta',description='Con foto',inspected_date='2026-01-01',inspected_time='10:00',photos=(image,'foto.png')))
        self.assertEqual(result.status_code,302);self.assertEqual(self.count('photos'),1)
        for route in ('/alerts','/rules','/maintenance','/inspection-plans'):
            self.assertEqual(self.client.get(route).status_code,404)
        for user in ('inspector','worker'):
            self.login(user)
            self.assertEqual(self.post('/measurements',{}).status_code,403)
        self.assertEqual(self.post('/inspections',{}).status_code,403)
        self.login('dom')
        before=self.count('measurements')
        result=self.post('/measurements',dict(sensor_code='S1',value=1,unit='m/s²',status='valido',measured_date='2026-09-06',measured_time='00:30'))
        self.assertIn('no existe',result.text);self.assertEqual(self.count('measurements'),before)


def load_tests(loader,standard_tests,pattern):
    return loader.loadTestsFromTestCase(UsabilityTests)
