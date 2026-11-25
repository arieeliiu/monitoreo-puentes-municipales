"""Coma decimal, planificación desde una alerta y formato único del puente."""
import re
import unittest

from number_format import decimal
from tests.test_app import SystemTests


class DecimalFormatTests(unittest.TestCase):
    def test_decimal_comma_without_noise(self):
        cases = [(2.5, '2,5'), (0.115, '0,115'), (3.0, '3'), (-0.229, '-0,229'), (-0.0, '0'), ('9', '9'),
                 (1234.5, '1234,5'), (0.1 + 0.2, '0,3')]
        for value, expected in cases:
            self.assertEqual(decimal(value), expected, value)
        for passthrough in (None, '', 'No disponible'):
            self.assertEqual(decimal(passthrough), passthrough)


class PresentationPageTests(SystemTests):
    def setUp(self):
        super().setUp()
        self.rule(threshold='2.5')
        self.post('/measurements', self.measurement(value='2.75'))

    def test_pages_show_decimal_comma_but_forms_keep_dot(self):
        self.assertIn('≥ 2,5 m/s²', self.client.get('/rules').text)
        detail = self.client.get('/alerts/1').text
        self.assertIn('≥ 2,5 m/s²', detail); self.assertIn('2,75 m/s²', detail)
        self.assertIn('2,75', self.client.get('/measurements').text)
        self.assertIn('2,75', self.client.get('/measurements/1').text)
        for page in ('/rules', '/alerts/1', '/measurements/1'):
            self.assertNotRegex(self.client.get(page).text, r'\b2\.75\b|≥ 2\.5\b')
        self.assertIn('type="number"', self.client.get('/measurements').text)  # Los formularios siguen aceptando punto.

    def test_plan_activity_link_prefills_alert_bridge_and_component(self):
        detail = self.client.get('/alerts/1').text
        self.assertIn('href="/maintenance?alert_id=1#nueva-actividad"', detail)
        page = self.client.get('/maintenance?alert_id=1').text
        self.assertIn('<details class="panel" open>', page)
        self.assertRegex(page, r'<option value="1" data-bridge="1" selected>#1 · P1 · Puente de prueba')
        self.assertRegex(page, r'name="bridge_id"[^>]*>.*?<option value="1" selected>P1 · Puente de prueba</option>')
        self.assertRegex(page, r'<option value="1" data-bridge="1" selected>Tablero · P1</option>')
        response = self.post('/maintenance', dict(bridge_id='1', component_id='1', alert_id='1', description='Revisar', assignee_id='3', planned_date='2026-12-01'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.db.execute('SELECT alert_id,component_id FROM tasks').fetchone()[:], (1, 1))

    def test_plan_activity_prefill_validation_and_role(self):
        self.assertEqual(self.client.get('/maintenance?alert_id=999').status_code, 404)
        for value in ('abc', '0', '-1'):
            self.assertEqual(self.client.get('/maintenance?alert_id=' + value).status_code, 400)
        self.assertNotIn(' selected>#', self.client.get('/maintenance').text)
        self.login('worker')
        self.assertNotIn('nueva-actividad', self.client.get('/maintenance?alert_id=1').text)

    def test_resolved_alerts_are_not_offered_for_new_activities(self):
        self.post('/alerts/1', dict(note='Cerrada', status='Resuelta'))
        self.assertNotIn('>#1 · P1', self.client.get('/maintenance').text)
        self.assertIn('>#1 · P1', self.client.get('/maintenance?alert_id=1').text)

    def test_bridge_label_is_consistent_across_pages(self):
        self.inspection(); self.task()
        expected = 'P1 · Puente de prueba'
        for page in ('/alerts', '/alerts/1', '/rules', '/inspections', '/inspections/1', '/maintenance', '/measurements', '/measurements/1', '/'):
            text = self.client.get(page).text
            self.assertIn(expected, text, page)
        for page in ('/alerts', '/inspections', '/measurements', '/maintenance'):
            options = re.findall(r'name="bridge_id"[^>]*>(.*?)</select>', self.client.get(page).text)
            self.assertTrue(options, page)
            self.assertIn('P2 · Segundo puente', options[0], page)
        self.assertIn('P1 · S1 (', self.client.get('/measurements').text)

    def test_notification_title_includes_bridge_code(self):
        cursor = self.client.get('/api/v1/alert-notifications').json['cursor']
        self.post('/measurements', self.measurement(value='3', measured_at='2026-01-01T11:00:00-03:00'))
        self.post('/alerts/1', dict(note='Cerrada', status='Resuelta'))
        self.post('/measurements', self.measurement(value='3', measured_at='2026-01-01T12:00:00-03:00'))
        titles = [a['title'] for a in self.client.get('/api/v1/alert-notifications?after=' + cursor).json['alerts']]
        self.assertTrue(titles and all(t.startswith('P1 · Puente de prueba · ') for t in titles), titles)


def load_tests(loader, standard_tests, pattern):
    suite = unittest.TestSuite(loader.loadTestsFromTestCase(DecimalFormatTests))
    suite.addTests(PresentationPageTests(n) for n in PresentationPageTests.__dict__ if n.startswith('test_'))
    return suite
