"""Regresión desde formularios renderizados y procesos IoT reales."""
import socket
import subprocess
import sys
import time
import unittest
from html.parser import HTMLParser
from pathlib import Path

from tests.test_app import SystemTests


class Forms(HTMLParser):
    """Valores enviados por los controles HTML (incluye selección por defecto)."""
    def __init__(self, html):
        super().__init__()
        self.forms = []
        self.form = self.select = self.option = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'form':
            self.form = {'fields': {}, 'selects': {}}
            self.forms.append(self.form)
        elif self.form is not None:
            if tag == 'input' and attrs.get('name'):
                self.form['fields'][attrs['name']] = attrs.get('value', '')
            elif tag == 'select':
                self.select = attrs['name']
                self.form['selects'][self.select] = []
            elif tag == 'option' and self.select:
                self.option = {'value': attrs.get('value'), 'selected': 'selected' in attrs, 'text': ''}
                self.form['selects'][self.select].append(self.option)

    def handle_data(self, data):
        if self.option is not None:
            self.option['text'] += data

    def handle_endtag(self, tag):
        if tag == 'option':
            if self.option is not None and self.option['value'] is None:
                self.option['value'] = self.option['text']
            self.option = None
        elif tag == 'select' and self.select:
            options = self.form['selects'][self.select]
            if options:
                self.form['fields'][self.select] = next((o for o in options if o['selected']), options[0])['value']
            self.select = None
        elif tag == 'form':
            self.form = None


class FinalFixTests(SystemTests):
    def sensor_forms(self):
        page = self.client.get('/bridges/1')
        self.assertEqual(page.status_code, 200)
        return [f for f in Forms(page.get_data(as_text=True)).forms if f['fields'].get('entity') == 'sensor']

    def form_for(self, sensor_id=''):
        return next(f for f in self.sensor_forms() if f['fields'].get('id', '') == str(sensor_id))

    def submit_form(self, form):
        # Keep the CSRF token and actual selected values rendered by the server.
        return self.client.post('/bridges/1', data=form['fields'], follow_redirects=True)

    def test_create_both_types_from_rendered_forms(self):
        for kind, label, unit in [('vibracion', 'Aceleración vertical pico', 'm/s²'), ('inclinacion', 'Inclinación', '°')]:
            form = self.form_for()
            option = next(o for o in form['selects']['kind'] if o['text'].startswith(label))
            self.assertEqual(option['value'], kind)
            form['fields'].update(code='UI-' + kind.upper(), location='Tablero: centro del vano', kind=option['value'], reference_value='1.25')
            form['fields']['component_id'] = next(o['value'] for o in form['selects']['component_id'] if o['text'] == 'Tablero')
            response = self.submit_form(form)
            self.assertIn('Registro guardado.', response.get_data(as_text=True))
            row = self.db.execute('SELECT * FROM sensors WHERE code=?', (form['fields']['code'],)).fetchone()
            self.assertEqual((row['kind'], row['unit'], row['component_id']), (kind, unit, 1))
            self.assertEqual(row['reference_value'], 1.25 if kind == 'inclinacion' else None)
            self.assertEqual(self.form_for(row['id'])['fields']['kind'], kind)
            self.assertIn(form['fields']['location'], response.get_data(as_text=True))

    def test_edit_both_types_keeps_selection_and_updates_data(self):
        for sensor_id, kind in [(1, 'vibracion'), (2, 'inclinacion')]:
            form = self.form_for(sensor_id)
            selected = [o for o in form['selects']['kind'] if o['selected']]
            self.assertEqual([o['value'] for o in selected], [kind])
            form['fields'].update(location='Tablero: extremo actualizado', reference_value='2.5')
            self.assertIn('Registro guardado.', self.submit_form(form).get_data(as_text=True))
            updated = self.form_for(sensor_id)
            self.assertEqual(updated['fields']['kind'], kind)
            self.assertEqual(updated['fields']['location'], 'Tablero: extremo actualizado')
            if kind == 'inclinacion':
                self.assertEqual(float(updated['fields']['reference_value']), 2.5)
        # A DOM may change a type before measurements exist; the next form selects it.
        form = self.form_for(1)
        form['fields']['kind'] = next(o['value'] for o in form['selects']['kind'] if o['text'] == 'Inclinación')
        self.submit_form(form)
        self.assertEqual(self.form_for(1)['fields']['kind'], 'inclinacion')
        self.assertEqual(self.db.execute('SELECT unit FROM sensors WHERE id=1').fetchone()[0], '°')

    def test_rendered_sensor_forms_role_permissions(self):
        create = self.form_for()['fields']
        create.update(code='FORBIDDEN', location='Tablero: centro')
        edit = self.form_for(1)['fields']
        edit['location'] = 'Cambio no permitido'
        before = [tuple(r) for r in self.db.execute('SELECT * FROM sensors ORDER BY id')]
        for user in ['inspector', 'worker']:
            self.login(user)
            self.assertEqual(self.sensor_forms(), [])
            for payload in [create, edit]:
                self.assertEqual(self.post('/bridges/1', payload).status_code, 403)
            self.assertEqual([tuple(r) for r in self.db.execute('SELECT * FROM sensors ORDER BY id')], before)

    def setup_pilot(self):
        self.db.execute("UPDATE bridges SET code='DEM-01' WHERE id=1")
        self.db.execute("UPDATE bridges SET code='DEM-02' WHERE id=2")
        self.db.execute("UPDATE components SET name='Tablero' WHERE id=2")
        self.db.execute("UPDATE sensors SET code='DEM-01-VIBRACION' WHERE id=1")
        self.db.execute("UPDATE sensors SET code='DEM-01-INCLINACION' WHERE id=2")
        self.db.execute("INSERT INTO sensors(component_id,code,kind,unit) VALUES(2,'DEM-02-VIBRACION','vibracion','m/s²')")
        self.db.execute("INSERT INTO sensors(component_id,code,kind,unit,reference_value) VALUES(2,'DEM-02-INCLINACION','inclinacion','°',0)")
        self.db.commit()
        result = self.app.test_cli_runner().invoke(args=['configure-ev2-demo'])
        self.assertEqual(result.exit_code, 0, result.output)

    def test_pilot_locations_preserve_manual_data_associations_and_rules(self):
        self.setup_pilot()
        self.db.execute("UPDATE sensors SET location='Pendiente de precisar' WHERE id IN (1,2)")
        self.db.execute("UPDATE sensors SET location='Ubicación manual exacta' WHERE id=3")
        self.db.execute("UPDATE sensors SET location='   ' WHERE id=4")
        for sensor_id, component in [(2, 'Viga'), (4, 'Estribo')]:
            self.db.execute('UPDATE sensors SET component_id=(SELECT id FROM components WHERE bridge_id=? AND name=?) WHERE id=?', (1 if sensor_id == 2 else 2, component, sensor_id))
        self.db.execute('UPDATE rules SET threshold=0.6 WHERE id=1')
        self.db.commit()
        before = [tuple(r) for r in self.db.execute('SELECT id,component_id,code,kind,unit,reference_value FROM sensors ORDER BY id')]
        rules = [tuple(r) for r in self.db.execute('SELECT * FROM rules ORDER BY id')]
        runner = self.app.test_cli_runner()
        result = runner.invoke(args=['configure-demo-locations'])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn('3.', result.output)
        locations = [r[0] for r in self.db.execute('SELECT location FROM sensors ORDER BY id')]
        self.assertTrue(locations[0].startswith('Tablero:'))
        self.assertTrue(locations[1].startswith('Viga:'))
        self.assertEqual(locations[2], 'Ubicación manual exacta')
        self.assertTrue(locations[3].startswith('Estribo:'))
        self.assertEqual(before, [tuple(r) for r in self.db.execute('SELECT id,component_id,code,kind,unit,reference_value FROM sensors ORDER BY id')])
        self.assertEqual(rules, [tuple(r) for r in self.db.execute('SELECT * FROM rules ORDER BY id')])
        self.assertIn('0.', runner.invoke(args=['configure-demo-locations']).output)

    def test_locations_skip_nonpilot_and_unknown_components(self):
        self.setup_pilot()
        self.db.execute("UPDATE sensors SET location='' ")
        self.db.execute("UPDATE bridges SET simulated=0 WHERE id=2")
        self.db.execute("UPDATE sensors SET code='MANUAL-SENSOR' WHERE id=1")
        self.db.execute("UPDATE components SET name='Otro componente' WHERE id=1")
        self.db.commit()
        result = self.app.test_cli_runner().invoke(args=['configure-demo-locations'])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn('0.', result.output)
        self.assertTrue(all(r[0] == '' for r in self.db.execute('SELECT location FROM sensors')))

    def test_real_provider_and_periodic_worker_restart_recovery(self):
        self.setup_pilot()
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        url = f'http://127.0.0.1:{port}/measurements'
        self.app.config['PROVIDER_URL'] = url
        config = {key: self.app.config[key] for key in ['DATABASE', 'UPLOAD_FOLDER', 'SECRET_KEY', 'PROVIDER_URL']}
        code = ('from app import create_app\n'
                f'app=create_app({config!r})\n'
                "with app.app_context(): app.cli.main(args=['poll-provider','--interval','1'])\n")
        processes = []

        def launch(args):
            process = subprocess.Popen([sys.executable, *args], cwd=Path(__file__).resolve().parents[1], stdout=log, stderr=log)
            processes.append(process)
            return process

        def wait_for(predicate, label):
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if predicate():
                    return
                self.assertIsNone(worker.poll(), 'El worker terminó inesperadamente')
                time.sleep(0.1)
            self.fail('Tiempo agotado: ' + label)

        def errors():
            return self.db.execute("SELECT count(*) FROM audit WHERE action='Error al consultar proveedor ficticio'").fetchone()[0]

        with (self.path / 'processes.log').open('w', encoding='utf-8') as log:
            try:
                worker = launch(['-c', code])
                wait_for(lambda: errors() >= 1, 'error inicial de conexión auditado')
                provider = launch(['mock_provider.py', '--port', str(port)])
                wait_for(lambda: self.count('measurements') == 4, 'captura automática de ambos puentes')
                wait_for(lambda: self.db.execute("SELECT count(*) FROM audit WHERE action='Consultar proveedor ficticio'").fetchone()[0] >= 2, 'segunda consulta automática')
                self.assertEqual(self.count('measurements'), 4)
                self.assertEqual(self.count('alerts'), 4)
                provider.terminate(); provider.wait(timeout=10)
                previous = errors()
                wait_for(lambda: errors() > previous, 'error tras desconectar proveedor')
                self.assertEqual(self.client.get('/').status_code, 200)
                provider = launch(['mock_provider.py', '--port', str(port)])
                wait_for(lambda: self.count('measurements') == 8, 'recuperación automática sin reiniciar worker')
                self.assertEqual(self.count('alerts'), 8)
                self.assertEqual([tuple(r) for r in self.db.execute('SELECT bridge_id,count(*),min(severity),max(severity) FROM alerts GROUP BY bridge_id')], [(1,4,'Alerta','Alerta'),(2,4,'Alerta','Alerta')])
                self.assertEqual(self.post('/provider/pull').status_code, 302)
                self.assertEqual(self.count('measurements'), 8)
                self.assertEqual(self.count('alerts'), 8)
                self.assertIsNone(worker.poll())
            finally:
                for process in processes:
                    if process.poll() is None:
                        process.terminate()
                    process.wait(timeout=10)


def load_tests(loader, standard_tests, pattern):
    return unittest.TestSuite(FinalFixTests(name) for name in FinalFixTests.__dict__ if name.startswith('test_'))
