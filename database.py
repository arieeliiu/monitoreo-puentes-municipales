"""Conexiones SQLite locales y PostgreSQL transaccional para Supabase."""
import re
import sqlite3
from pathlib import Path


class Record(dict):
    """Interfaz de sqlite3.Row para las vistas existentes."""
    def __getitem__(self, key):
        return list(self.values())[key] if isinstance(key, int) else super().__getitem__(key)
    def __iter__(self):
        return iter(self.values())


def placeholders(sql):
    # Cambiar solo parámetros; no tocar literales SQL ni escapar datos a mano.
    return re.sub(r"'(''|[^'])*'|\?", lambda m: '%s' if m[0] == '?' else m[0], sql)


class Cursor:
    def __init__(self, cursor, lastrowid=None):
        self.cursor = cursor
        self.lastrowid = lastrowid
    def fetchone(self):
        value = self.cursor.fetchone()
        if value is None: return None
        return Record(zip((c.name for c in self.cursor.description), value))
    def fetchall(self):
        return [Record(zip((c.name for c in self.cursor.description), row)) for row in self.cursor.fetchall()]
    def __iter__(self):
        return iter(self.fetchall())


class Postgres:
    def __init__(self, url, schema='puentes'):
        import psycopg
        if not re.fullmatch(r'[a-z][a-z0-9_]{0,62}', schema): raise ValueError('Esquema PostgreSQL inválido.')
        self.schema = schema
        try:
            self.connection = psycopg.connect(url, connect_timeout=10, prepare_threshold=None, sslmode='verify-full', sslrootcert=str(Path(__file__).resolve().parent/'certs/supabase-ca.crt'))
        except psycopg.Error:
            raise sqlite3.OperationalError('No fue posible conectar a PostgreSQL.') from None

    def execute(self, sql, args=()):
        import psycopg
        from psycopg.pq import TransactionStatus
        try:
            if self.connection.info.transaction_status == TransactionStatus.IDLE:
                # SET LOCAL pertenece a cada transacción, compatible con Supavisor.
                self.connection.execute('SET LOCAL search_path TO ' + self.schema)
            if sql.strip().upper() == 'BEGIN IMMEDIATE':
                # La misma exclusión para recepción manual, API y Cron, sin archivo local.
                sql = 'SELECT pg_advisory_xact_lock(26102026)'
            statement = placeholders(sql)
            inserted = re.match(r'\s*INSERT\s+INTO\s+', statement, re.I) and 'RETURNING' not in statement.upper()
            if inserted: statement = statement.rstrip().rstrip(';') + ' RETURNING id'
            cursor = self.connection.execute(statement, args, prepare=False)
            return Cursor(cursor, cursor.fetchone()[0] if inserted else None)
        except psycopg.IntegrityError:
            # No rollback aquí: el llamador restaura su savepoint o transacción.
            raise sqlite3.IntegrityError('Restricción de integridad PostgreSQL.') from None
        except psycopg.Error:
            raise sqlite3.OperationalError('Error de persistencia PostgreSQL.') from None

    def commit(self): self.connection.commit()
    def rollback(self): self.connection.rollback()
    def close(self): self.connection.close()


def connect(config):
    if config.get('DATABASE_URL'):
        return Postgres(config['DATABASE_URL'], config.get('DATABASE_SCHEMA', 'puentes'))
    from migrations import migrate
    connection = sqlite3.connect(config['DATABASE'])
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA foreign_keys=ON')
    migrate(connection)
    return connection
