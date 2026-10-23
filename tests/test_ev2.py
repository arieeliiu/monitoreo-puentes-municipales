import sqlite3, unittest
from contextlib import closing
from pathlib import Path
from tests.test_app import SystemTests
from migrations import migrate

class Ev2Tests(SystemTests):
    def config(self):
        result=self.app.test_cli_runner().invoke(args=['configure-ev2-demo'])
        self.assertEqual(result.exit_code,0,result.output)

    def test_numeric_levels_positive_negative_and_exact_limits(self):
        self.config()
        for kind,sensor,unit,values in [('vibracion','S1','m/s²',[(0.499,None),(0.5,'Atención'),(0.999,'Atención'),(1,'Alerta'),(2.499,'Alerta'),(2.5,'Crítico'),(3,'Crítico')]),('inclinacion','S2','°',[(0.114,None),(0.115,'Atención'),(-0.115,'Atención'),(0.229,'Alerta'),(-0.229,'Alerta'),(0.458,'Crítico'),(-0.458,'Crítico')])]:
            for value,expected in values:
                before=self.count('alerts')
                self.assertEqual(self.post('/measurements',self.measurement(sensor_code=sensor,unit=unit,value=str(value))).status_code,302)
                self.assertEqual(self.count('alerts')-before,int(expected is not None),(kind,value))
                if expected:self.assertEqual(self.db.execute('SELECT severity FROM alerts ORDER BY id DESC').fetchone()[0],expected)

    def test_reference_offset_snapshot_missing_and_invalid(self):
        self.config();self.db.execute('UPDATE sensors SET reference_value=10 WHERE id=2');self.db.commit()
        for value,expected in [('10.115','Atención'),('9.771','Alerta'),('10.458','Crítico'),('9.542','Crítico')]:
            self.post('/measurements',self.measurement(sensor_code='S2',unit='°',value=value))
            self.assertEqual(self.db.execute('SELECT severity FROM alerts ORDER BY id DESC').fetchone()[0],expected)
        snapshot=tuple(self.db.execute('SELECT value,reference_value,variation FROM measurements WHERE id=1').fetchone())
        self.assertEqual(snapshot,(10.115,10,0.115))
        self.post('/bridges/1',dict(entity='sensor',id='2',code='S2',component_id='1',kind='inclinacion',location='Tablero',reference_value='11'))
        self.assertEqual(tuple(self.db.execute('SELECT value,reference_value,variation FROM measurements WHERE id=1').fetchone()),snapshot)
        self.db.execute('UPDATE sensors SET reference_value=NULL WHERE id=2');self.db.commit();before=self.count('alerts')
        self.post('/measurements',self.measurement(sensor_code='S2',unit='°',value='20'))
        self.assertEqual(self.count('alerts'),before)
        self.assertIn('Falta referencia',self.db.execute('SELECT evaluation FROM measurements ORDER BY id DESC').fetchone()[0])
        self.assertIn('no evaluable',self.client.get('/measurements').get_data(as_text=True))
        self.post('/bridges/1',dict(entity='sensor',id='2',code='S2',component_id='1',kind='inclinacion',location='Tablero',reference_value='NaN'))
        self.assertIsNone(self.db.execute('SELECT reference_value FROM sensors WHERE id=2').fetchone()[0])

    def test_old_units_are_never_relabelled(self):
        legacy=sqlite3.connect(':memory:');legacy.executescript(Path('schema.sql').read_text(encoding='utf-8'))
        legacy.execute("INSERT INTO users VALUES(1,'old','hash','DOM')")
        legacy.execute("INSERT INTO bridges VALUES(1,'OLD','Viejo','Lugar','Alta',1)")
        legacy.execute("INSERT INTO components VALUES(1,1,'Tablero')")
        legacy.execute("INSERT INTO sensors VALUES(1,1,'OLD-S','vibracion','mm/s')")
        legacy.execute("INSERT INTO measurements VALUES(1,1,7,'mm/s','2026-01-01','valido',1,'old',1,'2026-01-01')")
        legacy.execute("INSERT INTO inspections VALUES(1,1,1,'2026-01-01',1,'Mala','Original',1)")
        legacy.execute("INSERT INTO photos VALUES(1,1,'original.jpg')")
        legacy.execute("INSERT INTO rules VALUES(1,1,'visual',NULL,'Mala','Antigua',1,1,1,'2026-01-01')")
        legacy.execute("INSERT INTO alerts VALUES(1,1,1,NULL,1,'2026-01-01','Activa',1)")
        legacy.commit();migrate(legacy);migrate(legacy)
        self.assertEqual(legacy.execute('SELECT value,unit,specification FROM measurements').fetchone(),(7,'mm/s','historica'))
        self.assertEqual(legacy.execute('SELECT unit,previous_unit FROM sensors').fetchone(),('m/s²','mm/s'))
        self.assertEqual(legacy.execute('SELECT condition,standard FROM inspections').fetchone(),('Mala','historica'))
        self.assertEqual(legacy.execute('SELECT inspection_id,filename FROM photos').fetchone(),(1,'original.jpg'))
        self.assertEqual(legacy.execute('SELECT rule_id,inspection_id,severity FROM alerts').fetchone(),(1,1,'Sin nivel'))
        self.assertEqual(legacy.execute('PRAGMA foreign_key_check').fetchall(),[]);legacy.close()
        response=self.post('/measurements',self.measurement(unit='mm/s'))
        self.assertIn('m/s²',response.get_data(as_text=True));self.assertEqual(self.count('measurements'),0)

    def test_visual_categories_and_configured_alerts(self):
        self.config()
        for condition,expected in [('Baja',None),('Media','Atención'),('Alta','Alerta'),('Crítica','Crítico')]:
            before=self.count('alerts');self.assertEqual(self.inspection(condition=condition).status_code,302)
            self.assertEqual(self.count('alerts')-before,int(expected is not None))
            if expected:self.assertEqual(self.db.execute('SELECT severity FROM alerts ORDER BY id DESC').fetchone()[0],expected)
        count=self.count('inspections');self.inspection(condition='Mala');self.assertEqual(self.count('inspections'),count)

    def test_rule_configuration_versions_and_highest_only(self):
        self.config();self.post('/measurements',self.measurement(value='3'))
        previous=self.db.execute('SELECT * FROM alerts').fetchone();self.assertEqual(previous['severity'],'Crítico');self.assertEqual(self.count('alerts'),1)
        self.rule(threshold='4',severity='Crítico')
        self.post('/measurements',self.measurement(value='3'));self.assertEqual(self.db.execute('SELECT severity FROM alerts ORDER BY id DESC').fetchone()[0],'Alerta')
        self.assertEqual(self.db.execute('SELECT rule_id FROM alerts WHERE id=1').fetchone()[0],previous['rule_id'])
        self.assertEqual(self.db.execute('SELECT active FROM rules WHERE id=?',(previous['rule_id'],)).fetchone()[0],0)
        count=self.count('rules');self.rule(threshold='5',severity='Atención');self.assertEqual(self.count('rules'),count)
        self.login('inspector');self.assertEqual(self.rule().status_code,403)

    def test_demo_setup_is_idempotent_and_customizable(self):
        self.config();counts={table:self.count(table) for table in ['bridges','components','sensors','rules']}
        self.config();self.assertEqual(counts,{table:self.count(table) for table in counts})
        for bid in [1,2]:
            self.assertTrue({'Tablero','Viga','Estribo'}.issubset({r[0] for r in self.db.execute('SELECT name FROM components WHERE bridge_id=?',(bid,))}))
        self.assertEqual(self.count('sensors'),2)  # No invented physical sensors.
        self.db.execute('UPDATE rules SET active=0 WHERE id=1');self.db.commit();self.config()
        self.assertEqual(self.db.execute('SELECT active FROM rules WHERE id=1').fetchone()[0],0)
        self.db.execute('UPDATE sensors SET reference_value=2.5 WHERE id=2');self.db.commit();self.config()
        self.assertEqual(self.db.execute('SELECT reference_value FROM sensors WHERE id=2').fetchone()[0],2.5)

    def test_professional_ui_and_severity_styles_all_roles(self):
        self.config();self.post('/measurements',self.measurement(value='2.5'))
        for role in ['dom','inspector','worker']:
            self.login(role)
            for path in ['/','/bridges','/bridges/1','/measurements','/inspections','/alerts','/alerts/1','/maintenance','/inspection-plans']:
                response=self.client.get(path);self.assertEqual(response.status_code,200,(role,path))
                text=response.get_data(as_text=True)
                self.assertEqual(text.count('Entorno de demostración'),1,(role,path))
                for forbidden in ['PRUEBA','HU-','EDT','26 NOV','piloto académico','Integración IoT real pendiente']:
                    self.assertNotIn(forbidden,text,(role,path,forbidden))
        self.assertIn('severity-critical',self.client.get('/').get_data(as_text=True))
        self.assertIn('Crítico',self.client.get('/alerts').get_data(as_text=True))

    def test_ev2_provider_flow_both_bridges(self):
        import threading
        from mock_provider import make_server
        self.db.execute("INSERT INTO sensors(component_id,code,kind,unit,reference_value) VALUES(2,'S3','inclinacion','°',10)");self.db.commit();self.config()
        records=[self.measurement(external_id='ev2-a',bridge_code='P1',kind='vibracion',value=0.5,simulated=True),self.measurement(external_id='ev2-b',sensor_code='S3',unit='°',bridge_code='P2',kind='inclinacion',value=9.771,simulated=True)]
        server=make_server(port=0,records=records);t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
        try:
            self.app.config['PROVIDER_URL']=f'http://127.0.0.1:{server.server_port}/measurements'
            self.post('/provider/pull');self.post('/provider/pull')
            self.assertEqual(self.count('measurements'),2);self.assertEqual(self.count('alerts'),2)
            self.assertEqual([tuple(r) for r in self.db.execute('SELECT bridge_id,severity FROM alerts ORDER BY id')],[(1,'Atención'),(2,'Alerta')])
            self.assertEqual(tuple(self.db.execute('SELECT reference_value,variation FROM measurements WHERE sensor_id=3').fetchone()),(10,0.229))
        finally:server.shutdown();server.server_close();t.join()

    def test_fresh_demo_has_three_components_per_bridge(self):
        from app import create_app
        fresh=create_app({'TESTING':True,'DATABASE':str(self.path/'fresh.sqlite'),'UPLOAD_FOLDER':str(self.path/'fresh-photos'),'SECRET_KEY':'fresh-test','PROJECT_STAGE':'full'})
        runner=fresh.test_cli_runner()
        self.assertEqual(runner.invoke(args=['init-db']).exit_code,0)
        result=runner.invoke(args=['seed-demo']);self.assertEqual(result.exit_code,0,result.output)
        with closing(sqlite3.connect(fresh.config['DATABASE'])) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM bridges').fetchone()[0],2)
            for bid in [1,2]: self.assertEqual({r[0] for r in db.execute('SELECT name FROM components WHERE bridge_id=?',(bid,))},{'Tablero','Viga','Estribo'})
            self.assertEqual(db.execute('SELECT count(*) FROM sensors').fetchone()[0],4)
            self.assertEqual(db.execute("SELECT count(*) FROM sensors WHERE kind='inclinacion' AND reference_value=0").fetchone()[0],2)

def load_tests(loader,standard_tests,pattern):
    return unittest.TestSuite(Ev2Tests(name) for name in Ev2Tests.__dict__ if name.startswith('test_'))
