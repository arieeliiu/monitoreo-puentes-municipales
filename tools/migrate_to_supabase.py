"""Copia verificable SQLite -> esquema privado PostgreSQL + Storage.

No borra ni modifica el origen. Requiere un destino vacío o idéntico.
Las credenciales se leen exclusivamente del entorno del proceso.
"""
import argparse
import hashlib
import json
import os
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from database import Postgres
from photo_storage import PhotoStorage

TABLES=['users','bridges','components','sensors','measurements','inspections','photos','rules','alerts','alert_notes','tasks','audit','inspection_plans']


def migrate(source, photos, report):
    if not source.is_file():raise ValueError('No existe el archivo SQLite de origen.')
    if not os.environ.get('DATABASE_URL'): raise ValueError('Configura DATABASE_URL del destino.')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
    backup=source.with_name(source.stem+'-antes-supabase-'+stamp+'.sqlite')
    with closing(sqlite3.connect(source)) as origin, closing(sqlite3.connect(backup)) as snapshot:
        origin.backup(snapshot)
        if snapshot.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or snapshot.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('El origen no superó la verificación de integridad.')
        snapshot.row_factory=sqlite3.Row
        rows={table:[dict(row) for row in snapshot.execute(f'SELECT * FROM {table} ORDER BY id')] for table in TABLES}
    config=dict(os.environ);config.update(UPLOAD_FOLDER=str(photos),PHOTO_STORAGE='supabase')
    storage=PhotoStorage(config)
    bucket=json.loads(storage.request('GET','bucket/'+storage.bucket))
    if bucket.get('public') is not False: raise ValueError('El bucket debe ser privado.')
    target=Postgres(os.environ['DATABASE_URL'],os.environ.get('DATABASE_SCHEMA','puentes'))
    uploaded=[];hashes={}
    try:
        target.execute('SELECT pg_advisory_xact_lock(26102026)')
        for table in TABLES:
            existing=[dict(row) for row in target.execute(f'SELECT * FROM {table} ORDER BY id').fetchall()]
            if existing and existing!=rows[table]: raise ValueError(f'El destino {table} contiene datos distintos; no se sobrescriben.')
            if not existing:
                if rows[table]:
                    from psycopg import sql
                    keys=list(rows[table][0])
                    statement=sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,keys)),sql.SQL(',').join(sql.Placeholder() for _ in keys))
                    with target.connection.cursor() as cursor:
                        cursor.executemany(statement,[tuple(record[k] for k in keys) for record in rows[table]])
            actual=[dict(row) for row in target.execute(f'SELECT * FROM {table} ORDER BY id').fetchall()]
            if actual!=rows[table]: raise ValueError('Copia inconsistente de '+table)
        for record in rows['photos']:
            name=record['filename']; data=(photos/name).read_bytes()
            # No sobrescribir un objeto con el mismo nombre y distinto contenido.
            from photo_storage import PhotoStorageError
            try:remote=storage.get(name)
            except PhotoStorageError as error:
                if 'HTTP 404' not in str(error): raise
                storage.put(name,data);uploaded.append(name);remote=storage.get(name)
            if remote!=data: raise ValueError('La fotografía remota difiere: '+name)
            hashes[name]=hashlib.sha256(data).hexdigest()
        for table in TABLES:
            # IDs preservados; las nuevas altas deben continuar por encima del máximo.
            target.execute(f"SELECT setval(pg_get_serial_sequence('{target.schema}.{table}','id'),coalesce((SELECT max(id) FROM {table}),1),(SELECT count(*)>0 FROM {table}))")
        target.commit()
    except Exception:
        target.rollback()
        for name in uploaded:
            try:storage.delete(name)
            except Exception:pass
        raise
    finally:target.close()
    result=dict(backup=str(backup),counts={t:len(r) for t,r in rows.items()},photo_sha256=hashes,all_rows_verified=True,password_hashes_preserved=True)
    report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Migración verificada. Informe privado: '+str(report))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--sqlite',type=Path,default=ROOT/'instance/puentes.sqlite')
    parser.add_argument('--photos',type=Path,default=ROOT/'instance/photos')
    parser.add_argument('--report',type=Path,default=ROOT/'instance/MIGRACION_SUPABASE.json')
    args=parser.parse_args();migrate(args.sqlite,args.photos,args.report)
