"""Corte de presentación y reversibilidad sin alterar datos EV2."""
import io
import os
import re
import sqlite3
import unittest
from html.parser import HTMLParser
from unittest.mock import patch

from PIL import Image
from app import create_app, CUTOFF_STAGE, PENDING_EVALUATION
from tests.test_app import SystemTests
from tests.test_final_fixes import FinalFixTests


class Navigation(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.in_nav = False; self.labels = []
        self.feed(html)
    def handle_starttag(self, tag, attrs):
        if tag == 'nav': self.in_nav = True
    def handle_endtag(self, tag):
        if tag == 'nav': self.in_nav = False
    def handle_data(self, text):
        if self.in_nav and text.strip(): self.labels.append(text.strip())


class ProjectStageTests(FinalFixTests):
    def setUp(self):
        super().setUp()
        self.app.config['PROJECT_STAGE'] = CUTOFF_STAGE

    def configure_demo(self):
        result = self.app.test_cli_runner().invoke(args=['configure-ev2-demo'])
        self.assertEqual(result.exit_code, 0, result.output)

    def snapshot(self):
        names = [r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        return {name: [tuple(r) for r in self.db.execute(f'SELECT * FROM {name} ORDER BY id')] for name in names}

    def test_default_environment_explicit_full_and_invalid_stage(self):
        config = dict(self.app.config); config.pop('PROJECT_STAGE')
        before = self.snapshot()
        with patch.dict(os.environ):
            os.environ.pop('PROJECT_STAGE', None)
            self.assertEqual(create_app(config).config['PROJECT_STAGE'], CUTOFF_STAGE)
            os.environ['PROJECT_STAGE'] = 'full'
            self.assertEqual(create_app(config).config['PROJECT_STAGE'], 'full')
            self.assertEqual(create_app(dict(config, PROJECT_STAGE=CUTOFF_STAGE)).config['PROJECT_STAGE'], CUTOFF_STAGE)
            os.environ['PROJECT_STAGE'] = 'invalid'
            with self.assertRaisesRegex(ValueError, 'PROJECT_STAGE'): create_app(config)
        self.assertEqual(before, self.snapshot())

    def test_three_roles_four_navigation_links_simple_home_and_logout(self):
        for role in ['dom', 'inspector', 'worker']:
            self.assertEqual(self.login(role).status_code, 302)
            for url in ['/', '/bridges', '/bridges/1', '/measurements', '/inspections']:
                response = self.client.get(url); self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                self.assertEqual(Navigation(html).labels, ['Inicio', 'Infraestructura', 'Mediciones', 'Inspecciones visuales'])
                for link in ['/rules', '/alerts', '/maintenance', '/inspection-plans']:
                    self.assertNotIn('href="' + link, html)
                self.assertNotIn('name="plan_id"', html)
            home = self.client.get('/').get_data(as_text=True)
            self.assertIn('Sistema de monitoreo de puentes municipales', home)
            self.assertIn('mediciones almacenadas', home)
            for future in ['alerta', 'mantenimiento', 'programada', 'reglas', '<svg', '<canvas']:
                self.assertNotIn(future, home.lower())
            self.assertEqual(self.post('/logout').status_code, 302)
            self.assertEqual(self.client.get('/').status_code, 302)

    def test_future_routes_block_get_post_with_or_without_csrf_no_database_changes(self):
        self.configure_demo()
        paths = ['/rules', '/alerts', '/alerts/1', '/maintenance', '/inspection-plans']
        for role in ['dom', 'inspector', 'worker']:
            self.login(role)
            before = self.snapshot()
            for url in paths:
                self.assertEqual(self.client.get(url).status_code, 404, (role, url))
                self.assertEqual(self.post(url, dict(disable='1', cancel='1', status='Resuelta', note='forged')).status_code, 404, (role, url))
                self.assertEqual(self.client.post(url, data={}).status_code, 404)
            self.assertEqual(before, self.snapshot())
        self.login('dom')
        self.assertEqual(self.client.get('/audit').status_code, 200)
        self.login('inspector'); self.assertEqual(self.client.get('/audit').status_code, 403)

    def test_manual_and_api_store_pending_without_reading_rules(self):
        self.configure_demo()
        real_connect = sqlite3.connect; statements = []
        def trace_connection(*args, **kwargs):
            connection = real_connect(*args, **kwargs)
            connection.set_trace_callback(statements.append)
            return connection
        rules = [tuple(r) for r in self.db.execute('SELECT * FROM rules')]
        with patch('app.sqlite3.connect', side_effect=trace_connection):
            for value in ['0.5', '1', '2.5']:
                self.assertEqual(self.post('/measurements', self.measurement(value=value)).status_code, 302)
            self.assertEqual(self.post('/measurements', self.measurement(sensor_code='S2', unit='°', value='-0.458')).status_code, 302)
            self.post('/measurements', self.measurement(value='', status='no_disponible'))
            result = self.client.post('/api/v1/measurements', json=self.measurement(external_id='cutoff-api', value='9', simulated=True), headers={'Authorization': 'Bearer test-key'})
            self.assertEqual(result.status_code, 201)
            self.assertEqual(result.json['evaluation'], PENDING_EVALUATION)
        self.assertFalse(any(re.search(r'SELECT\b.*\bFROM\s+rules\b', sql, re.I) for sql in statements))
        self.assertEqual(self.count('measurements'), 6)
        self.assertEqual(self.count('alerts'), 0)
        self.assertEqual({r[0] for r in self.db.execute('SELECT evaluation FROM measurements')}, {PENDING_EVALUATION})
        self.assertEqual(tuple(self.db.execute('SELECT reference_value,variation FROM measurements WHERE sensor_id=2').fetchone()), (0, 0.458))
        self.assertEqual(rules, [tuple(r) for r in self.db.execute('SELECT * FROM rules')])
        self.assertIn(PENDING_EVALUATION, self.client.get('/measurements/1').get_data(as_text=True))
        self.assertEqual(self.client.post('/api/v1/measurements', json=self.measurement(external_id='cutoff-api'), headers={'Authorization': 'Bearer test-key'}).status_code, 400)

    def test_cutoff_dom_sensor_forms_create(self):
        FinalFixTests.test_create_both_types_from_rendered_forms(self)

    def test_cutoff_dom_sensor_forms_edit_and_permissions(self):
        FinalFixTests.test_edit_both_types_keeps_selection_and_updates_data(self)
        FinalFixTests.test_rendered_sensor_forms_role_permissions(self)

    def test_cutoff_dom_bridges_create_edit_and_permissions(self):
        SystemTests.test_bridge_crud_and_duplicates(self)
        self.login('inspector'); self.assertEqual(self.post('/bridges', {}).status_code, 403)
        self.login('worker'); self.assertEqual(self.post('/bridges', {}).status_code, 403)

    def test_cutoff_inspection_photos_and_visual_categories_no_alerts(self):
        self.configure_demo()
        SystemTests.test_photo_upload_and_authorization(self)
        self.login('inspector')
        for condition in ['Baja', 'Media', 'Alta', 'Crítica']:
            self.assertEqual(self.inspection(condition=condition).status_code, 302)
        self.assertEqual(self.count('alerts'), 0)
        self.login('worker'); self.assertEqual(self.inspection().status_code, 403)

    def test_forged_plan_cannot_create_inspection_or_complete_plan(self):
        self.app.config['PROJECT_STAGE'] = 'full'
        self.assertEqual(self.post('/inspection-plans', dict(bridge_id='1', component_id='1', inspector_id='2', planned_date='2026-11-10', description='Programación futura')).status_code, 302)
        self.app.config['PROJECT_STAGE'] = CUTOFF_STAGE
        self.login('inspector')
        before = self.snapshot()
        photo = io.BytesIO(); Image.new('RGB', (20, 20), 'blue').save(photo, 'PNG'); photo.seek(0)
        response = self.inspection(plan_id='1', photos=(photo, 'image.png'))
        self.assertIn('no está disponible en esta etapa', response.get_data(as_text=True))
        self.assertEqual(before, self.snapshot())
        self.assertFalse(list(self.path.joinpath('photos').glob('*')))
        self.assertNotIn('name="plan_id"', self.client.get('/inspections').get_data(as_text=True))

    def test_cutoff_real_provider_worker_retries_deduplicates_without_alerts(self):
        self.run_real_provider_and_worker(expected_alerts=False)

    def test_cutoff_mockups_match_enabled_routes_only(self):
        from pathlib import Path
        html=Path('docs/mockups.html').read_text(encoding='utf-8')
        self.assertEqual(Navigation(html).labels, ['1 · Inicio','2 · Infraestructura','3 · Mediciones','4 · Inspecciones visuales'])
        for forbidden in ['Programación que se atiende','Alertas activas','Actividades de mantenimiento','No existen reglas activas','name="plan_id"','Evaluada']:
            self.assertNotIn(forbidden, html)
        self.assertIn(PENDING_EVALUATION, html)
        self.assertIn('Sistema de monitoreo de puentes municipales', html)

    def test_switching_preserves_populated_history_photos_rules_and_full_engine(self):
        self.configure_demo()
        self.app.config['PROJECT_STAGE'] = 'full'
        self.post('/measurements', self.measurement())
        photo = io.BytesIO(); Image.new('RGB', (20,20), 'green').save(photo,'PNG'); photo.seek(0)
        self.inspection(photos=(photo,'old.png'))
        self.task()
        self.post('/inspection-plans', dict(bridge_id='1', component_id='1', inspector_id='2', planned_date='2026-11-10', description='Futura'))
        before = self.snapshot()
        photo_bytes = {p.name:p.read_bytes() for p in self.path.joinpath('photos').iterdir()}
        for stage in [CUTOFF_STAGE, 'full', CUTOFF_STAGE, 'full']:
            self.app.config['PROJECT_STAGE'] = stage
            for path in ['/', '/bridges/1', '/measurements', '/inspections/1']:
                self.assertEqual(self.client.get(path).status_code, 200)
            self.assertEqual(before, self.snapshot())
            self.assertEqual(photo_bytes, {p.name:p.read_bytes() for p in self.path.joinpath('photos').iterdir()})
        for path in ['/rules','/alerts','/alerts/1','/maintenance','/inspection-plans']:
            self.assertEqual(self.client.get(path).status_code, 200)
        self.assertIn('Panel de monitoreo', self.client.get('/').get_data(as_text=True))
        self.post('/measurements', self.measurement())
        self.assertEqual(self.count('alerts'), len(before['alerts'])+1)
        self.assertEqual(self.db.execute('SELECT evaluation FROM measurements ORDER BY id DESC').fetchone()[0], 'Evaluada')
        self.login('inspector')
        self.assertIn('name="plan_id"', self.client.get('/inspections').get_data(as_text=True))
        self.assertEqual(self.inspection(plan_id='1').status_code, 302)
        self.assertEqual(self.db.execute('SELECT status FROM inspection_plans WHERE id=1').fetchone()[0], 'Realizada')


def load_tests(loader, standard_tests, pattern):
    return unittest.TestSuite(ProjectStageTests(name) for name in ProjectStageTests.__dict__ if name.startswith('test_'))
