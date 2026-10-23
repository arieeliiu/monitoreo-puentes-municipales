"""EV2: columnas nuevas y ampliación de categorías, sin reinterpretar históricos."""
def migrate_ev2(db):
    if 'specification' in {r[1] for r in db.execute('PRAGMA table_info(measurements)')}: return
    db.commit()
    enabled=db.execute('PRAGMA foreign_keys').fetchone()[0]
    db.execute('PRAGMA foreign_keys=OFF')
    try:
        db.execute('BEGIN IMMEDIATE')
        additions=[('sensors','reference_value','REAL'),('sensors','previous_unit','TEXT'),
                   ('measurements','reference_value','REAL'),('measurements','variation','REAL'),
                   ('rules','standard',"TEXT NOT NULL DEFAULT 'historica'"),('rules','severity',"TEXT NOT NULL DEFAULT 'Sin nivel'"),('rules','unit','TEXT'),
                   ('alerts','severity',"TEXT NOT NULL DEFAULT 'Sin nivel'"),('alerts','standard',"TEXT NOT NULL DEFAULT 'historica'"),
                   ('inspections','standard',"TEXT NOT NULL DEFAULT 'historica'")]
        for table,name,definition in additions: db.execute(f'ALTER TABLE {table} ADD COLUMN {name} {definition}')
        # Widen the old CHECK; old labels remain verbatim and carry standard=historica.
        sql=db.execute("SELECT sql FROM sqlite_master WHERE name='inspections'").fetchone()[0]
        sql=sql.replace('CREATE TABLE inspections','CREATE TABLE inspections_ev2',1).replace("'Buena','Regular','Mala','Crítica'", "'Buena','Regular','Mala','Crítica','Baja','Media','Alta'")
        db.execute(sql)
        columns=','.join(r[1] for r in db.execute('PRAGMA table_info(inspections)'))
        db.execute(f'INSERT INTO inspections_ev2 ({columns}) SELECT {columns} FROM inspections')
        db.execute('DROP TABLE inspections');db.execute('ALTER TABLE inspections_ev2 RENAME TO inspections')
        db.execute("UPDATE rules SET unit=CASE kind WHEN 'vibracion' THEN 'mm/s' WHEN 'inclinacion' THEN '°' ELSE NULL END")
        db.execute("UPDATE sensors SET previous_unit=unit,unit='m/s²' WHERE kind='vibracion' AND unit='mm/s'")
        db.execute("ALTER TABLE measurements ADD COLUMN specification TEXT NOT NULL DEFAULT 'historica'")
        if db.execute('PRAGMA foreign_key_check').fetchall(): raise ValueError('La migración EV2 detectó relaciones inválidas.')
        db.commit()
    except Exception:
        db.rollback();raise
    finally: db.execute(f'PRAGMA foreign_keys={enabled}')
