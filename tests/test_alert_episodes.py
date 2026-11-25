"""Episodios de alertas: agrupación por sensor sin perder el registro de cada lectura (CA-04.4/04.5)."""
import re
import unittest

from tests.test_app import SystemTests


class AlertEpisodeTests(SystemTests):
    def readings(self, *values, sensor='S1'):
        for value in values:
            stamp = f'2026-01-01T10:{len(self.posted):02d}:00-03:00'
            self.posted.append(stamp)
            self.assertEqual(self.post('/measurements', self.measurement(sensor_code=sensor, value=str(value), measured_at=stamp)).status_code, 302)

    def setUp(self):
        super().setUp(); self.posted = []
        self.rule(severity='Atención', threshold='5'); self.rule(severity='Crítico', threshold='20')

    def api(self, suffix=''):
        return self.client.get('/api/v1/alert-notifications' + suffix).json

    def statuses(self):
        return [r['status'] for r in self.db.execute('SELECT status FROM alerts ORDER BY id')]

    def test_each_reading_keeps_its_alert_and_dashboard_groups_by_sensor(self):
        self.readings(9, 9, 9)
        self.assertEqual(self.count('alerts'), 3)
        linked = self.db.execute('SELECT count(DISTINCT measurement_id) FROM alerts').fetchone()[0]
        self.assertEqual(linked, 3)  # CA-04.5: cada alerta conserva su medición de origen.
        page = self.client.get('/').text
        self.assertEqual(page.count('data-episode-count="3"'), 1)
        self.assertIn('3 alertas abiertas agrupadas en 1 episodio', page)
        self.assertIn('sensor S1', page)

    def test_dashboard_prioritizes_the_episode_level_and_keeps_visual_findings_separate(self):
        self.readings(9, 25, 9)
        self.rule('visual', severity='Alerta', condition='Alta'); self.inspection()
        page = self.client.get('/').text
        rows = re.findall(r'href="/alerts/(\d+)"><div class="record-main">', page)
        # El episodio se representa por su alerta de mayor nivel (Crítico, #2) y precede al hallazgo visual.
        self.assertEqual(rows[:2], ['2', '4'])
        self.assertIn('4 alertas abiertas agrupadas en 2 episodios', page)

    def test_resolving_the_episode_starts_a_new_one(self):
        self.readings(9, 9)
        self.post('/alerts/1', dict(note='Revisado en terreno', status='Resuelta', apply_episode='1', episode_until='2'))
        self.assertEqual(self.statuses(), ['Resuelta', 'Resuelta'])
        self.readings(9)
        self.assertNotIn('data-episode=', self.client.get('/alerts/3').text)
        self.assertNotIn('data-episode-count', self.client.get('/').text)

    def test_follow_up_applies_to_the_episode_shown_with_individual_traceability(self):
        self.readings(9, 9, 9)
        detail = self.client.get('/alerts/1').text
        self.assertIn('data-episode="3"', detail); self.assertIn('name="episode_until" value="3"', detail)
        # Una tercera lectura llegó después de cargar la página: el usuario vio hasta la #2.
        response = self.post('/alerts/1', dict(note='Cuadrilla en camino', status='En atención', apply_episode='1', episode_until='2'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.statuses(), ['En atención', 'En atención', 'Activa'])
        notes = self.db.execute('SELECT alert_id,note,author_id FROM alert_notes ORDER BY alert_id').fetchall()
        self.assertEqual([(n['alert_id'], n['note'], n['author_id']) for n in notes], [(1, 'Cuadrilla en camino', 1), (2, 'Cuadrilla en camino', 1)])
        audit = self.db.execute("SELECT entity_id,author,details FROM audit WHERE action='Seguimiento de alerta' ORDER BY entity_id").fetchall()
        self.assertEqual([a['entity_id'] for a in audit], [1, 2])
        self.assertTrue(all(a['author'] == 'dom' and 'episodio del sensor S1, desde alerta #1' in a['details'] for a in audit))
        self.assertEqual(self.count('alerts'), 3)  # No se crean ni eliminan alertas.

    def test_follow_up_without_episode_flag_keeps_single_alert_behaviour(self):
        self.readings(9, 9)
        self.post('/alerts/2', dict(note='Solo esta lectura', status='Resuelta'))
        self.assertEqual(self.statuses(), ['Activa', 'Resuelta'])
        self.assertEqual(self.count('alert_notes'), 1)

    def test_episode_follow_up_validation_and_permissions(self):
        self.readings(9, 9)
        before = (self.statuses(), self.count('alert_notes'), self.count('audit'))
        for until in ('', 'abc', '-1'):
            self.post('/alerts/1', dict(note='x', status='Resuelta', apply_episode='1', episode_until=until))
        self.post('/alerts/2', dict(note='x', status='Resuelta', apply_episode='1', episode_until='1'))
        self.assertEqual((self.statuses(), self.count('alert_notes'), self.count('audit')), before)
        self.login('inspector')
        self.assertEqual(self.post('/alerts/1', dict(note='x', status='Resuelta', apply_episode='1', episode_until='2')).status_code, 403)
        self.post('/alerts/1', dict(note='Observado', apply_episode='1', episode_until='2'))
        self.assertEqual(self.statuses(), ['Activa', 'Activa']); self.assertEqual(self.count('alert_notes'), 2)
        self.login('worker')
        self.assertEqual(self.post('/alerts/1', dict(note='x', apply_episode='1', episode_until='2')).status_code, 403)
        self.assertNotIn('name="apply_episode"', self.client.get('/alerts/1').text)

    def test_notifications_skip_repeats_and_announce_escalations(self):
        cursor = self.api()['cursor']
        self.readings(9, 9, 25, 9, 30)
        batch = self.api('?after=' + cursor)
        self.assertEqual([a['id'] for a in batch['alerts']], ['1', '3'])
        self.assertNotIn('sube de nivel', batch['alerts'][0]['title']); self.assertIn('sube de nivel', batch['alerts'][1]['title'])
        self.assertEqual(batch['cursor'], '5'); self.assertFalse(batch['has_more'])
        self.assertEqual(batch['open_count'], 5)  # El contador sigue informando alertas abiertas, no episodios.
        self.assertEqual(self.api('?after=5')['alerts'], [])

    def test_notifications_after_resolution_and_for_visual_findings(self):
        self.readings(9)
        self.post('/alerts/1', dict(note='Cerrada', status='Resuelta'))
        cursor = self.api()['cursor']
        self.readings(9)
        self.rule('visual', severity='Alerta', condition='Alta'); self.inspection()
        self.assertEqual([a['id'] for a in self.api('?after=' + cursor)['alerts']], ['2', '3'])

    def test_alert_list_filters_by_sensor_and_open_status(self):
        self.readings(9, 9)
        self.post('/alerts/1', dict(note='Cerrada', status='Resuelta'))
        page = self.client.get('/alerts?sensor_id=1&status=abiertas').text
        self.assertEqual(re.findall(r'class="row-link alert-row" href="/alerts/(\d+)"', page), ['2'])
        self.assertIn('value="abiertas" selected', page)
        self.assertIn('No hay alertas', self.client.get('/alerts?sensor_id=2').text)
        for query in ('sensor_id=abc', 'sensor_id=0', 'status=cerradas'):
            self.assertEqual(self.client.get('/alerts?' + query).status_code, 400)


def load_tests(loader, standard_tests, pattern):
    return unittest.TestSuite(AlertEpisodeTests(name) for name in AlertEpisodeTests.__dict__ if name.startswith('test_'))
