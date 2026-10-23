"""Migración aditiva e idempotente. No elimina tablas ni registros."""
def migrate(connection):
    if not connection.execute("SELECT 1 FROM sqlite_master WHERE name='sensors'").fetchone():
        return
    for table, name, definition in [
        ('sensors','location',"TEXT NOT NULL DEFAULT 'Pendiente de precisar'"),
        ('rules','comparison',"TEXT NOT NULL DEFAULT 'gt'"),
        ('measurements','evaluation',"TEXT NOT NULL DEFAULT 'Histórico: evaluación no registrada'"),
    ]:
        if name not in {r[1] for r in connection.execute(f'PRAGMA table_info({table})')}:
            connection.execute(f'ALTER TABLE {table} ADD COLUMN {name} {definition}')
    connection.execute('''CREATE TABLE IF NOT EXISTS inspection_plans(
        id INTEGER PRIMARY KEY, bridge_id INTEGER NOT NULL REFERENCES bridges(id),
        component_id INTEGER NOT NULL REFERENCES components(id), inspector_id INTEGER NOT NULL REFERENCES users(id),
        planned_date TEXT NOT NULL, description TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Programada' CHECK(status IN ('Programada','Realizada','Cancelada')),
        inspection_id INTEGER UNIQUE REFERENCES inspections(id), author_id INTEGER NOT NULL REFERENCES users(id),
        created_at TEXT NOT NULL)''')
    connection.commit()
