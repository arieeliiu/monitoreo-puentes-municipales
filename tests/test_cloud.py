import io
import json
import os
import sqlite3
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from app import create_app, CUTOFF_STAGE, PENDING_EVALUATION
from cloud_provider import cloud_records
from database import Postgres, placeholders
from tests.test_app import SystemTests


class CloudTests(SystemTests):
    def test_serverless_requires_stable_secret_and_no_local_files(self):
        with patch.dict(os.environ,{'VERCEL':'1'},clear=True):
            with self.assertRaisesRegex(ValueError,'SECRET_KEY'):create_app()
            with patch('pathlib.Path.mkdir',side_effect=AssertionError('No debe escribir en disco')):
                app=create_app({'SECRET_KEY':'stable','DATABASE_URL':'postgres://unused','PHOTO_STORAGE':'supabase','SUPABASE_URL':'https://example.supabase.co','SUPABASE_SECRET_KEY':'sb_secret_test'})
                self.assertEqual(app.config['PROJECT_STAGE'],CUTOFF_STAGE)

    def test_private_storage_upload_read_authorization_and_compensation(self):
        objects={}
        def request(req,timeout=15):
            path=req.full_url.split('/storage/v1/')[1]
            self.assertEqual(req.headers['Apikey'],'sb_secret_test')
            if path.startswith('object/sign/'):
                return io.BytesIO(json.dumps({'signedURL':'/object/sign/puentes-fotos/photo.jpg?token=temporary'}).encode())
            if req.method=='POST':objects[path.rsplit('/',1)[1]]=req.data;return io.BytesIO(b'{}')
            if req.method=='DELETE':
                for name in json.loads(req.data)['prefixes']:objects.pop(name,None)
                return io.BytesIO(b'{}')
            return io.BytesIO(objects[path.rsplit('/',1)[1]])
        config=dict(self.app.config,PHOTO_STORAGE='supabase',SUPABASE_URL='https://example.supabase.co',SUPABASE_SECRET_KEY='sb_secret_test')
        self.app=create_app(config);self.client=self.app.test_client()
        with patch('photo_storage.urlopen',side_effect=request):
            self.login('inspector')
            from PIL import Image
            image=io.BytesIO();Image.new('RGB',(24,24),'blue').save(image,'PNG');image.seek(0)
            self.assertEqual(self.inspection(photos=(image,'image.png')).status_code,302)
            self.assertEqual(len(objects),1)
            self.login('inspector')
            filename=self.db.execute('SELECT filename FROM photos').fetchone()[0]
            response=self.client.get('/photos/'+filename)
            self.assertEqual(response.status_code,302);self.assertTrue(response.location.startswith('https://example.supabase.co/storage/v1/object/sign/'));response.close()
            self.db.execute("CREATE TRIGGER fail_photo BEFORE INSERT ON photos BEGIN SELECT RAISE(ABORT,'test'); END");self.db.commit()
            from PIL import Image
            data=io.BytesIO();Image.new('RGB',(10,10),'blue').save(data,'PNG');data.seek(0)
            before=self.count('inspections');self.inspection(photos=(data,'image.png'))
            self.assertEqual(self.count('inspections'),before);self.assertEqual(len(objects),1)
        with patch('photo_storage.urlopen',side_effect=HTTPError('https://example',503,'failed',{},None)):
            self.assertEqual(self.client.get('/photos/'+filename).status_code,502)

    def test_direct_uploads_authorization_limits_validation_and_cleanup(self):
        from photo_storage import PhotoStorage
        from PIL import Image
        data=io.BytesIO();Image.new('RGB',(24,24),'green').save(data,'PNG')
        self.app=create_app(dict(self.app.config,PHOTO_STORAGE='supabase',SUPABASE_URL='https://example.supabase.co',SUPABASE_SECRET_KEY='sb_secret_test'))
        self.client=self.app.test_client();self.login('inspector')
        with patch.object(PhotoStorage,'signed_upload',return_value='https://example.supabase.co/upload?token=temporary'),patch.object(PhotoStorage,'delete_staged') as cleanup,patch.object(PhotoStorage,'staged',return_value=data.getvalue()),patch.object(PhotoStorage,'put') as upload:
            self.assertEqual(self.post('/uploads/prepare',{'files':json.dumps([{'size':21*1024*1024}])}).status_code,400)
            self.assertEqual(self.post('/uploads/prepare',{'files':json.dumps([{'size':1}]*6)}).status_code,400)
            response=self.post('/uploads/prepare',{'files':json.dumps([{'size':5*1024*1024}])})
            self.assertEqual(response.status_code,200)
            name=response.json['uploads'][0]['name']
            before=self.count('inspections')
            self.inspection(staged_uploads=json.dumps(['other-user.upload']))
            self.assertEqual(self.count('inspections'),before)
            self.assertEqual(self.inspection(staged_uploads=json.dumps([name])).status_code,302)
            self.assertEqual(self.count('inspections'),before+1);self.assertEqual(self.count('photos'),1)
            self.assertEqual(upload.call_count,1);cleanup.assert_called_with([name])
            self.inspection(staged_uploads=json.dumps([name]))
            self.assertEqual(self.count('inspections'),before+1)
            self.login('worker')
            self.assertEqual(self.post('/uploads/prepare',{'files':'[{"size":1}]'}).status_code,403)

    def test_cron_secret_cloud_provider_dedup_and_cutoff(self):
        from tests.test_final_fixes import FinalFixTests
        FinalFixTests.setup_pilot(self)
        self.app.config.update(CLOUD_PROVIDER=True,CRON_SECRET='cron-test-secret',PROJECT_STAGE=CUTOFF_STAGE)
        self.assertEqual(self.client.post('/internal/iot/pull').status_code,401)
        self.assertEqual(self.client.post('/internal/iot/pull',headers={'Authorization':'Bearer wrong'}).status_code,401)
        # Estabilizar el lote de prueba para no depender de un cambio de minuto.
        from datetime import datetime, timezone
        batch=cloud_records(datetime(2026,1,1,tzinfo=timezone.utc))
        with patch('app.cloud_records',return_value=batch):
            headers={'Authorization':'Bearer cron-test-secret'}
            first=self.client.post('/internal/iot/pull',headers=headers);second=self.client.post('/internal/iot/pull',headers=headers)
            self.assertEqual(first.json['received'],4);self.assertEqual(second.json['duplicates'],4)
        self.assertEqual(self.count('measurements'),4);self.assertEqual(self.count('alerts'),0)
        self.assertEqual({r[0] for r in self.db.execute('SELECT evaluation FROM measurements')},{PENDING_EVALUATION})
        self.assertEqual(self.post('/provider/pull').status_code,302)

    def test_parameters_do_not_rewrite_sql_literals(self):
        self.assertEqual(placeholders("SELECT '?' AS literal, x FROM t WHERE id=? AND label='it''s ?'"),"SELECT '?' AS literal, x FROM t WHERE id=%s AND label='it''s ?'")


@unittest.skipUnless(os.environ.get('PUENTES_TEST_DATABASE_URL'),'Requiere PostgreSQL de pruebas aislado')
class PostgresTests(SystemTests):
    def setUp(self):
        super().setUp()
        import psycopg
        url=os.environ['PUENTES_TEST_DATABASE_URL']
        if 'puentes_test.' not in url:raise ValueError('Las pruebas solo aceptan el usuario restringido puentes_test.')
        source=self.db
        schema=Path('sql/postgres.sql').read_text(encoding='utf-8')
        with psycopg.connect(url,prepare_threshold=None) as raw:
            raw.execute('SET search_path TO puentes_test')
            exists=raw.execute("SELECT to_regclass('puentes_test.users')").fetchone()[0]
            if not exists:
                for statement in schema.split(';'):
                    statement=statement.strip()
                    if not statement or statement.startswith(('CREATE SCHEMA','SET search_path','GRANT','REVOKE')):continue
                    raw.execute(statement)
            from tools.migrate_to_supabase import TABLES
            raw.execute('TRUNCATE '+','.join(TABLES)+' RESTART IDENTITY CASCADE')
            for table in TABLES:
                for row in source.execute('SELECT * FROM '+table):
                    record=dict(row);keys=list(record)
                    raw.execute(f'INSERT INTO {table} ({",".join(keys)}) VALUES ({",".join("%s" for _ in keys)})',tuple(record.values()))
                raw.execute(f"SELECT setval(pg_get_serial_sequence('puentes_test.{table}','id'),coalesce((SELECT max(id) FROM {table}),1),(SELECT count(*)>0 FROM {table}))")
        source.close()
        self.db=Postgres(url,'puentes_test')
        self.app=create_app(dict(self.app.config,DATABASE_URL=url,DATABASE_SCHEMA='puentes_test'))
        self.client=self.app.test_client();self.login('dom')

    def count(self,table):
        self.db.commit() # ver commits de las peticiones desde la conexión de inspección
        return super().count(table)

    def test_postgres_infrastructure_and_sensors(self):
        SystemTests.test_bridge_crud_and_duplicates(self)
        SystemTests.test_components_sensors_validation_and_edits(self)

    def test_postgres_measurements_and_alerts_full(self):
        SystemTests.test_measurement_validation_and_history(self)
        SystemTests.test_alert_threshold_and_simulation(self)

    def test_postgres_private_photos_and_permissions(self):
        SystemTests.test_photo_upload_and_authorization(self)

    def test_postgres_cutoff_receipt_and_duplicate_cron(self):
        CloudTests.test_cron_secret_cloud_provider_dedup_and_cutoff(self)

    def test_postgres_migration_preserves_rows_hashes_photos_and_ids(self):
        from tools.migrate_to_supabase import TABLES,migrate
        from photo_storage import PhotoStorageError
        from PIL import Image
        original=create_app(dict(self.app.config,DATABASE_URL='',PHOTO_STORAGE='local'))
        client=original.test_client()
        with client.session_transaction() as session:session['user_id']=2;session['csrf']='migration-test'
        image=io.BytesIO();Image.new('RGB',(32,32),'blue').save(image,'PNG');image.seek(0)
        response=client.post('/inspections',data=dict(csrf='migration-test',bridge_id='1',component_id='1',inspected_at='2026-01-01T10:00:00Z',condition='Alta',description='Foto de migración',photos=(image,'image.png')))
        self.assertEqual(response.status_code,302)
        self.db.execute('TRUNCATE '+','.join(TABLES)+' RESTART IDENTITY CASCADE');self.db.commit()
        objects={}
        class Storage:
            bucket='test-private'
            def request(self,*args):return b'{"public":false}'
            def get(self,name):
                if name not in objects:raise PhotoStorageError('Storage HTTP 404')
                return objects[name]
            def put(self,name,data):objects[name]=data
            def delete(self,name):objects.pop(name,None)
        env={'DATABASE_URL':os.environ['PUENTES_TEST_DATABASE_URL'],'DATABASE_SCHEMA':'puentes_test'}
        with patch.dict(os.environ,env),patch('tools.migrate_to_supabase.PhotoStorage',return_value=Storage()):
            report=migrate(self.path/'test.sqlite',self.path/'photos',self.path/'migration-report.json')
            self.assertTrue(report['password_hashes_preserved']);self.assertEqual(report['counts']['photos'],1)
            self.assertEqual(len(objects),1)
            self.db.commit();self.assertEqual(self.count('users'),4)
            again=migrate(self.path/'test.sqlite',self.path/'photos',self.path/'migration-report.json')
            self.assertEqual(report['counts'],again['counts'])
            new_id=self.db.execute("INSERT INTO bridges(code,name,location,criticality,simulated) VALUES('NEXT','Next','Lugar','Alta',1)").lastrowid
            self.db.commit();self.assertEqual(new_id,3)
            with self.assertRaisesRegex(ValueError,'datos distintos'):migrate(self.path/'test.sqlite',self.path/'photos',self.path/'migration-report.json')

    def test_postgres_provider_savepoints_and_evidence(self):
        from tests.test_iot_update import IotUpdateTests
        self.contract=lambda *args,**kwargs:IotUpdateTests.contract(self,*args,**kwargs)
        IotUpdateTests.test_provider_rejects_inconsistent_and_missing_identity_with_evidence(self)

    def test_postgres_usability_filters(self):
        from tests.test_usability import UsabilityTests
        UsabilityTests.test_filters_persistence_incompatible_sensor_and_details(self)

    def test_postgres_usability_dates_photos(self):
        from tests.test_usability import UsabilityTests
        UsabilityTests.test_split_form_dates_photos_permissions_and_cutoff(self)


def load_tests(loader,standard_tests,pattern):
    return unittest.TestSuite(cls(name) for cls in [CloudTests,PostgresTests] for name in cls.__dict__ if name.startswith('test_'))
