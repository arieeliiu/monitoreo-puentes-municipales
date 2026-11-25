"""Mapa de sensores: ubicación por componente, sin posiciones inventadas ni escrituras."""
import unittest
from datetime import datetime, timezone

import bridge_schematic
from app import CUTOFF_STAGE, LABELS
from tests.test_app import SystemTests

NOW = datetime(2026, 11, 24, 15, 0, tzinfo=timezone.utc)


def sensor(sid, component_id, kind='vibracion', **reading):
    base = dict(id=sid, code=f'S{sid}', kind=kind, unit='m/s²' if kind == 'vibracion' else '°', location='Cara inferior',
                component_id=component_id, mid=None, value=None, status=None, measured_at=None, variation=None,
                specification='EV2', evaluation=None, alert_severity=None)
    base.update(reading)
    return base


class SchematicUnitTests(unittest.TestCase):
    def test_zones_by_component_name_and_unknown_components_listed_apart(self):
        components = [dict(id=1, name='Tablero'), dict(id=2, name='Viga principal'), dict(id=3, name='Estribo'),
                      dict(id=4, name='Barandas'), dict(id=5, name='Viga secundaria')]
        sensors = [sensor(1, 1), sensor(2, 2), sensor(3, 4)]
        result = bridge_schematic.build(components, sensors, [], LABELS, True, NOW)
        zones = {z['key']: z for z in result['zones']}
        self.assertEqual({k: z['component']['name'] if z['component'] else None for k, z in zones.items()},
                         {'estribo': 'Estribo', 'viga': 'Viga principal', 'tablero': 'Tablero'})
        self.assertNotIn('pila', zones)
        self.assertEqual([o['component']['name'] for o in result['others']], ['Barandas', 'Viga secundaria'])
        self.assertEqual([m['code'] for m in result['others'][0]['markers']], ['S3'])
        self.assertNotIn('x', result['others'][0]['markers'][0])

    def test_zone_matching_uses_whole_first_word(self):
        cases = {'Tablero': 'tablero', 'Vigas': 'viga', 'Viga principal': 'viga', 'Estribo norte': 'estribo',
                 'Pila central': 'pila', 'Pilar de iluminación': None, 'Tablerito': None, 'Luminaria': None, '': None,
                 'Estribos': 'estribo', 'ESTRIBO': 'estribo'}
        self.assertEqual({name: bridge_schematic.zone_key(name) for name in cases}, cases)

    def test_markers_stay_inside_their_component_lane(self):
        components = [dict(id=1, name='Tablero')]
        sensors = [sensor(n, 1) for n in range(1, 12)]
        zone = bridge_schematic.build(components, sensors, [], LABELS, True, NOW)['zones'][-1]
        start, end, y = bridge_schematic.ZONES['tablero']['lane']
        self.assertEqual(len(zone['markers']), 11)
        self.assertTrue(all(start <= m['x'] <= end and m['y'] == y for m in zone['markers']))
        self.assertEqual(len({m['x'] for m in zone['markers']}), 11)

    def test_states_follow_latest_record_and_stage(self):
        components = [dict(id=1, name='Tablero')]
        cases = [
            (sensor(1, 1), 'nodata'),
            (sensor(2, 1, mid=1, status='no_disponible', measured_at='2026-11-24T14:00:00+00:00'), 'invalid'),
            (sensor(3, 1, mid=2, status='valido', value=3.0, measured_at='2026-11-24T14:00:00+00:00', evaluation='Evaluada', alert_severity='Crítico'), 'critical'),
            (sensor(4, 1, mid=3, status='valido', value=0.1, measured_at='2026-11-24T14:00:00+00:00', evaluation='Evaluada'), 'ok'),
            (sensor(5, 1, mid=4, status='valido', value=0.1, measured_at='2026-11-24T14:00:00+00:00', evaluation='Sin regla aplicable'), 'valid'),
        ]
        markers = bridge_schematic.build(components, [c for c, _ in cases], [], LABELS, True, NOW)['zones'][-1]['markers']
        self.assertEqual([m['state'] for m in markers], [s for _, s in cases])
        stage_off = bridge_schematic.build(components, [cases[2][0]], [], LABELS, False, NOW)
        self.assertEqual(stage_off['zones'][-1]['markers'][0]['state'], 'valid')
        self.assertEqual([s for s, _ in stage_off['legend']], ['valid', 'invalid', 'nodata'])

    def test_detail_text_uses_recorded_description_and_flags_stale_data(self):
        old = sensor(1, 1, 'inclinacion', mid=1, status='valido', value=0.3, variation=0.3, location='Borde lateral, apoyo 2',
                     measured_at='2026-11-20T10:00:00+00:00', evaluation='Evaluada')
        title = bridge_schematic.build([dict(id=1, name='Tablero')], [old], [], LABELS, True, NOW)['zones'][-1]['markers'][0]['title']
        for text in ('Ubicación descrita: Borde lateral, apoyo 2', 'cambio absoluto 0,3 °', 'sin lecturas en las últimas 24 horas', 'Componente: Tablero'):
            self.assertIn(text, title)

    def test_latest_inspection_marks_its_component(self):
        inspections = [dict(id=9, component_id=1, condition='Alta', standard='EV2', inspected_at='2026-11-23T10:00:00+00:00'),
                       dict(id=3, component_id=1, condition='Baja', standard='EV2', inspected_at='2026-11-01T10:00:00+00:00')]
        zone = bridge_schematic.build([dict(id=1, name='Tablero')], [], inspections, LABELS, True, NOW)['zones'][-1]
        self.assertEqual((zone['inspection']['id'], zone['inspection']['tone']), (9, 'alert'))


class SchematicPageTests(SystemTests):
    def snapshot(self):
        return {t: [tuple(r) for r in self.db.execute('SELECT * FROM ' + t + ' ORDER BY id')] for t in ('measurements', 'alerts', 'inspections', 'sensors')}

    def test_bridge_page_map_for_all_roles_and_stages_without_writes(self):
        self.rule(); self.post('/measurements', self.measurement()); self.inspection()
        before = self.snapshot()
        for role in ('dom', 'inspector', 'worker'):
            self.login(role)
            html = self.client.get('/bridges/1').text
            self.assertIn('Mapa de sensores', html)
            self.assertIn('href="/measurements?sensor_id=1"', html)
            self.assertIn('map-sensor state-attention', html)
            self.assertIn('map-sensor state-nodata', html)
            self.assertIn('href="/inspections/1"', html)
            self.assertIn('Esquema no a escala', html)
        self.app.config['PROJECT_STAGE'] = CUTOFF_STAGE
        html = self.client.get('/bridges/1').text
        self.assertIn('map-sensor state-valid', html)
        self.assertNotIn('state-attention', html)
        html = self.client.get('/bridges/2').text
        self.assertIn('Pila', html)
        self.assertEqual(before, self.snapshot())


def load_tests(loader, standard_tests, pattern):
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(SchematicUnitTests))
    suite.addTests(SchematicPageTests(n) for n in SchematicPageTests.__dict__ if n.startswith('test_'))
    return suite
