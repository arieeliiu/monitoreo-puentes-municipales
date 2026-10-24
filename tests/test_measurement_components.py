import unittest
from html.parser import HTMLParser
from tests.test_app import SystemTests

class Selects(HTMLParser):
    def __init__(self,html):
        super().__init__();self.select=None;self.current=None;self.fields={};self.feed(html)
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='select':self.select=attrs.get('name');self.fields.setdefault(self.select,[])
        if tag=='option' and self.select:
            self.current=dict(attrs,text='');self.fields[self.select].append(self.current)
    def handle_data(self,data):
        if self.current is not None:self.current['text']+=data
    def handle_endtag(self,tag):
        if tag=='option':self.current=None
        if tag=='select':self.select=None

class MeasurementComponentTests(unittest.TestCase):
    setUp=SystemTests.setUp
    tearDown=SystemTests.tearDown
    post=SystemTests.post
    login=SystemTests.login
    count=SystemTests.count

    def pilot(self):
        self.app.config['PROJECT_STAGE']='cutoff_2026_10_26'
        self.db.execute("UPDATE components SET name='Tablero'")
        for bridge in (1,2):
            for name in ('Viga','Estribo'):self.db.execute('INSERT INTO components(bridge_id,name) VALUES (?,?)',(bridge,name))
        self.db.execute("INSERT INTO sensors(component_id,code,kind,unit) VALUES(2,'codigo-independiente','vibracion','m/s²')")
        self.db.commit()

    def data(self,**extra):
        result=dict(bridge_id='1',component_id='1',sensor_code='S1',value='1',unit='m/s²',status='valido',measured_date='2026-01-01',measured_time='10:00');result.update(extra);return result

    def test_components_from_database_and_forms(self):
        self.pilot()
        fields=Selects(self.client.get('/measurements').text).fields
        components=fields['component_id']
        for bridge in ('1','2'):
            names={o['text'].split(' · ')[0] for o in components if o.get('data-bridge')==bridge}
            self.assertEqual(names,{'Tablero','Viga','Estribo'})
        self.assertEqual(self.count('components'),6);self.assertEqual(self.count('sensors'),3)
        self.assertTrue(any(o['text']=='Todos los componentes' for o in components))
        self.assertTrue(any(o.get('value')=='codigo-independiente' and o.get('data-component')=='2' for o in fields['sensor_code']))
        self.assertIn('data-measurement-bridge',self.client.get('/measurements').text)
        self.assertIn('name="component_id"',self.client.get('/inspections').text)

    def test_combined_history_filters_and_empty_component(self):
        self.pilot()
        self.post('/measurements',self.data())
        self.post('/measurements',self.data(bridge_id='2',component_id='2',sensor_code='codigo-independiente'))
        for query in ('bridge_id=1&component_id=1&sensor_id=1','component_id=1','sensor_id=1'):
            html=self.client.get('/measurements?'+query).text
            table=html.split('<tbody>')[1].split('</tbody>')[0]
            self.assertIn('Tablero · S1',table);self.assertNotIn('codigo-independiente',table)
        for query in ('bridge_id=1&component_id=2','bridge_id=2&component_id=1&sensor_id=1','component_id=1&sensor_id=3','component_id=3'):
            self.assertIn('Sin mediciones disponibles',self.client.get('/measurements?'+query).text)
        html=self.client.get('/measurements?bridge_id=1&component_id=1&sensor_id=1&from=2026-01-01&to=2026-01-02').text
        fields=Selects(html).fields
        for name in ('bridge_id','component_id','sensor_id'):
            self.assertTrue(any(o.get('value')=='1' and 'selected' in o for o in fields[name]))
        self.assertIn('value="2026-01-02"',html);self.assertIn('history-filters" open',html)
        self.assertEqual(self.count('measurements'),2);self.assertEqual(self.count('alerts'),0)

    def test_manual_rejects_mismatched_relationships_and_preserves_permissions(self):
        self.pilot()
        for extra in (dict(bridge_id='2'),dict(component_id='2'),dict(sensor_code='codigo-independiente'),dict(component_id='3'),dict(bridge_id=''),dict(component_id='')):
            self.post('/measurements',self.data(**extra));self.assertEqual(self.count('measurements'),0)
        result=self.post('/measurements',self.data());self.assertEqual(result.status_code,302)
        self.assertEqual(self.count('measurements'),1)
        for role in ('inspector','worker'):
            self.login(role);self.assertEqual(self.post('/measurements',self.data()).status_code,403)
            self.assertNotIn('data-measurement-bridge',self.client.get('/measurements').text)
        for route in ('/rules','/alerts','/maintenance','/inspection-plans'):self.assertEqual(self.client.get(route).status_code,404)

    def test_dom_actions_before_history_closed_form_and_role_restrictions(self):
        html=self.client.get('/measurements').text
        self.assertLess(html.index('Registrar medición manual'),html.index('Consultar proveedor'))
        self.assertLess(html.index('Consultar proveedor'),html.index('history-filters'))
        self.assertLess(html.index('history-filters'),html.index('<tbody>'))
        self.assertEqual(html.count('action="/provider/pull"'),1)
        self.assertEqual(html.count('name="sensor_code"'),1)
        self.assertIn('id="manual-measurement" hidden',html)
        self.assertIn('aria-expanded="false"',html)
        for role in ('inspector','worker'):
            self.login(role);html=self.client.get('/measurements').text
            self.assertNotIn('Registrar medición manual',html)
            self.assertNotIn('Consultar proveedor',html)
            self.assertIn('history-filters',html)
            self.assertIn('<tbody>',html)
            self.assertEqual(self.post('/provider/pull').status_code,403)

def load_tests(loader,standard_tests,pattern):return loader.loadTestsFromTestCase(MeasurementComponentTests)
