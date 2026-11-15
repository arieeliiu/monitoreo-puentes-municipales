"""Revisión Christian: contrato v1, esquema y migraciones aisladas reproducibles."""
from contextlib import closing
import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import threading
import unittest

from PIL import Image
from app import create_app, EV3_CLOSURE_STAGE
from migrations import migrate
from mock_provider import make_server
from reference_migration import rename_reference_identifiers
from schema_revision import columns, require_current_schema, retire_columns, RETIRED, TABLES
from tests.test_app import SystemTests
from tests.test_ev3_closure import legacy_inventory, snapshot


def populated_legacy(test):
    test.rule();test.post('/measurements',test.measurement())
    image=io.BytesIO();Image.new('RGB',(12,12),'blue').save(image,'PNG');image.seek(0)
    test.inspection(photos=(image,'foto.png'));test.task()
    legacy_inventory(test)
    db=sqlite3.connect(test.path/'legacy.sqlite');db.row_factory=sqlite3.Row
    db.executescript(Path('tests/fixtures/schema_pre_christian.sql').read_text(encoding='utf-8'));migrate(db)
    for table in TABLES:
        for row in test.db.execute('SELECT * FROM '+table+' ORDER BY id'):
            item=dict(row)
            if table in RETIRED:item['simulated']=1
            db.execute('INSERT INTO '+table+' ('+','.join(item)+') VALUES ('+','.join('?' for _ in item)+')',tuple(item.values()))
    db.commit();return db


class ChristianTests(SystemTests):
    def test_push_eight_field_contract_without_simulation_marker(self):
        self.rule()
        record=dict(self.measurement(external_id='v1-push'),bridge_code='P1',kind='vibracion')
        self.assertEqual(len(record),8)
        headers={'Authorization':'Bearer test-key'}
        self.assertEqual(self.client.post('/api/v1/measurements',json=record,headers=headers).status_code,201)
        self.assertEqual(self.client.post('/api/v1/measurements',json=record,headers=headers).status_code,400)
        for change in ({'bridge_code':'P2'},{'kind':'inclinacion'},{'unit':'mm/s'},{'value':-1},{'status':'otro'},{'measured_at':'sin-fecha'}):
            bad=dict(record,external_id='invalid-'+str(change));bad.update(change)
            self.assertEqual(self.client.post('/api/v1/measurements',json=bad,headers=headers).status_code,400)
        self.assertEqual(self.count('measurements'),1);self.assertEqual(self.count('alerts'),1)

    def test_pull_eight_field_contract_and_dedup(self):
        record=dict(self.measurement(external_id='v1-pull'),bridge_code='P1',kind='vibracion')
        server=make_server(port=0,records=[record]);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            self.app.config['PROVIDER_URL']=f'http://127.0.0.1:{server.server_port}/measurements'
            for _ in range(2):self.assertEqual(self.post('/provider/pull').status_code,302)
            self.assertEqual(self.count('measurements'),1)
            self.assertIn('proveedor de referencia',self.db.execute("SELECT details FROM audit WHERE action='Consultar proveedor IoT' ORDER BY id DESC LIMIT 1").fetchone()[0])
        finally:server.shutdown();server.server_close();thread.join()

    def test_new_sqlite_has_thirteen_tables_ninety_nine_columns(self):
        counts={t:len(columns(self.db,t)) for t in TABLES}
        self.assertEqual(len(counts),13);self.assertEqual(sum(counts.values()),99)
        require_current_schema(self.db)
        self.assertTrue(all('simulated' not in columns(self.db,t) for t in TABLES))
        self.evidence={'tables':13,'columns':99,'columns_by_table':counts}

    def test_sqlite_old_d7_then_retire_preserves_rows_photos_and_integrity(self):
        with closing(populated_legacy(self)) as db:
            photos={p.name:p.read_bytes() for p in (self.path/'photos').iterdir()}
            self.assertEqual(sum(len(columns(db,t)) for t in TABLES),104)
            with self.assertRaisesRegex(ValueError,'D7'):retire_columns(db,apply=True)
            with self.assertRaisesRegex(ValueError,'Esquema anterior'):require_current_schema(db)
            before={t:[{k:r[k] for k in r.keys() if k!='simulated'} for r in db.execute('SELECT * FROM '+t+' ORDER BY id')] for t in TABLES}
            plan=rename_reference_identifiers(db);self.assertEqual(len(plan),6)
            rename_reference_identifiers(db,apply=True)
            for change in plan:next(row for row in before[change['table']] if row['id']==change['id'])['code']=change['new']
            dry=retire_columns(db);self.assertEqual(len(dry['columns_to_remove']),5)
            result=retire_columns(db,apply=True);self.assertEqual(result['columns_after'],99)
            self.assertEqual(before,{t:[dict(r) for r in db.execute('SELECT * FROM '+t+' ORDER BY id')] for t in TABLES})
            self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])
            self.assertEqual(retire_columns(db,apply=True)['columns_to_remove'],[])
            self.assertEqual(rename_reference_identifiers(db),[])
            self.assertEqual(photos,{p.name:p.read_bytes() for p in (self.path/'photos').iterdir()})
            self.evidence=result

    def test_importer_explicitly_rejects_legacy_source(self):
        from unittest.mock import patch
        from tools.migrate_to_supabase import migrate as import_data
        with closing(populated_legacy(self)):pass
        with patch.dict('os.environ',{'DATABASE_URL':'postgresql://unused'}):
            with self.assertRaisesRegex(ValueError,'Esquema anterior'):
                import_data(self.path/'legacy.sqlite',self.path/'photos',self.path/'report.json')

    def test_cli_retirement_is_explicit_readonly_and_requires_backup(self):
        with closing(populated_legacy(self)) as db:rename_reference_identifiers(db,apply=True)
        path=self.path/'legacy.sqlite';before=path.read_bytes()
        cmd=[sys.executable,'-X','utf8','tools/retire_legacy_columns.py','--sqlite',str(path)]
        dry=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(dry.returncode,0,dry.stderr);self.assertFalse(json.loads(dry.stdout)['applied']);self.assertEqual(path.read_bytes(),before)
        denied=subprocess.run(cmd+['--apply'],capture_output=True);self.assertNotEqual(denied.returncode,0);self.assertEqual(path.read_bytes(),before)
        backup=self.path/'before-retirement.sqlite'
        applied=subprocess.run(cmd+['--apply','--backup',str(backup)],capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(applied.returncode,0,applied.stderr)
        with closing(sqlite3.connect(backup)) as db:self.assertEqual(sum(len(columns(db,t)) for t in TABLES),104)
        with closing(sqlite3.connect(path)) as db:self.assertEqual(sum(len(columns(db,t)) for t in TABLES),99)

    def test_partial_retirement_rejected_without_more_changes(self):
        with closing(populated_legacy(self)) as db:
            rename_reference_identifiers(db,apply=True);db.execute('ALTER TABLE bridges DROP COLUMN simulated');db.commit()
            before=db.iterdump();before=list(before)
            with self.assertRaisesRegex(ValueError,'parcial'):retire_columns(db,apply=True)
            self.assertEqual(before,list(db.iterdump()))

    def test_sqlite_dependent_index_rolls_back_all_five_columns(self):
        with closing(populated_legacy(self)) as db:
            rename_reference_identifiers(db,apply=True)
            db.execute('CREATE INDEX custom_legacy_index ON alerts(simulated)');db.commit()
            before=list(db.iterdump())
            with self.assertRaises((ValueError,sqlite3.Error)):retire_columns(db,apply=True)
            self.assertEqual(before,list(db.iterdump()))
            self.assertTrue(all('simulated' in columns(db,t) for t in RETIRED))

    def test_explicit_reference_load_complete_and_non_destructive(self):
        fresh=create_app(dict(self.app.config,DATABASE=str(self.path/'reference.sqlite'),PROJECT_STAGE=EV3_CLOSURE_STAGE))
        cli=fresh.test_cli_runner();self.assertEqual(cli.invoke(args=['init-db']).exit_code,0)
        result=cli.invoke(args=['seed-reference-data','--confirm-isolated']);self.assertEqual(result.exit_code,0,result.output)
        with closing(sqlite3.connect(fresh.config['DATABASE'])) as db:
            counts={t:db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in TABLES}
            self.assertEqual((counts['bridges'],counts['sensors'],counts['measurements'],counts['inspections'],counts['tasks']),(2,4,8,2,2))
            self.assertGreater(counts['alerts'],0)
            self.assertEqual(set(r[0] for r in db.execute('SELECT status FROM tasks')),{'Pendiente','Completada'})
            self.assertEqual(db.execute("SELECT a.status FROM tasks t JOIN alerts a ON a.id=t.alert_id WHERE t.status='Completada'").fetchone()[0],'En atención')
            before=list(db.iterdump())
            self.assertNotEqual(cli.invoke(args=['seed-reference-data','--confirm-isolated']).exit_code,0)
            self.assertEqual(before,list(db.iterdump()));self.evidence={'reference_counts':counts}

    def test_no_functional_dependency_or_visible_simulation_text(self):
        source=Path('app.py').read_text(encoding='utf-8')
        self.assertNotIn('simulated',source)
        for name in ('dom','inspector','worker'):
            self.login(name)
            for url in ('/','/bridges','/measurements','/inspections','/alerts','/maintenance'):
                page=self.client.get(url);self.assertEqual(page.status_code,200)
                self.assertNotIn('simulad',page.text.lower());self.assertNotIn('name="simulated"',page.text)


def load_tests(loader,standard_tests,pattern):
    return unittest.TestSuite(ChristianTests(name) for name in ChristianTests.__dict__ if name.startswith('test_'))
