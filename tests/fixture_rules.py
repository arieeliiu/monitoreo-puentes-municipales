"""Reglas y componentes de fixtures genéricos; no identifica inventario productivo."""
import json
from pathlib import Path


def install_rules(test):
    config=json.loads(Path('config/ev2_pilot.json').read_text(encoding='utf-8'))
    for bid in (1,2):
        for name in ('Tablero','Viga','Estribo'):
            if not test.db.execute('SELECT id FROM components WHERE bridge_id=? AND name=?',(bid,name)).fetchone():
                test.db.execute('INSERT INTO components(bridge_id,name) VALUES(?,?)',(bid,name))
        for kind,levels in config['thresholds'].items():
            for severity,value in levels.items():
                if not test.db.execute("SELECT id FROM rules WHERE bridge_id=? AND kind=? AND severity=? AND standard='EV2'",(bid,kind,severity)).fetchone():
                    test.db.execute("INSERT INTO rules(bridge_id,kind,threshold,label,author_id,created_at,comparison,severity,standard,unit) VALUES(?,?,?,'Regla de fixture',1,'2026-01-01','gte',?,'EV2',?)",(bid,kind,value,severity,'m/s²' if kind=='vibracion' else '°'))
        for condition,severity in config['visual'].items():
            if not test.db.execute("SELECT id FROM rules WHERE bridge_id=? AND kind='visual' AND condition=? AND standard='EV2'",(bid,condition)).fetchone():
                test.db.execute("INSERT INTO rules(bridge_id,kind,condition,label,author_id,created_at,comparison,severity,standard) VALUES(?,'visual',?,'Visual de fixture',1,'2026-01-01','gte',?,'EV2')",(bid,condition,severity))
    test.db.execute("UPDATE sensors SET reference_value=? WHERE kind='inclinacion' AND reference_value IS NULL",(config['inclination_reference'],))
    test.db.commit()
