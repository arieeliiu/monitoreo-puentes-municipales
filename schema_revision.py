"""Retiro explícito y transaccional de las cinco columnas fuera de SMPMRB v1."""
import hashlib
import json

TABLES=('users','bridges','components','sensors','measurements','inspections','photos','rules','alerts','alert_notes','tasks','audit','inspection_plans')
RETIRED=('bridges','measurements','inspections','rules','alerts')


def columns(db,table):
    if hasattr(db,'schema'):
        return [r['column_name'] for r in db.execute('SELECT column_name FROM information_schema.columns WHERE table_schema=? AND table_name=? ORDER BY ordinal_position',(db.schema,table))]
    return [r[1] for r in db.execute('PRAGMA table_info('+table+')')]


def require_current_schema(db):
    legacy=(db.execute("SELECT 1 FROM information_schema.columns WHERE table_schema=? AND column_name='simulated' AND table_name IN ('bridges','measurements','inspections','rules','alerts') LIMIT 1",(db.schema,)).fetchone() if hasattr(db,'schema') else any('simulated' in columns(db,t) for t in RETIRED))
    if legacy:
        raise ValueError('Esquema anterior: ejecutar el procedimiento explícito D7 y retiro de columnas antes de activar esta versión.')


def retire_columns(db,apply=False):
    """Plan por defecto; D7 debe preceder al retiro. No se llama desde la web."""
    try:
        db.execute('BEGIN IMMEDIATE' if apply else 'BEGIN')
        if hasattr(db,'schema') and apply:
            db.execute('LOCK TABLE '+','.join(TABLES)+' IN ACCESS EXCLUSIVE MODE')
        inventory={table:columns(db,table) for table in TABLES}
        if any(not value for value in inventory.values()):raise ValueError('Faltan tablas del esquema; no se modifica un inventario parcial.')
        pending=[table for table in RETIRED if 'simulated' in inventory[table]]
        if pending and len(pending)!=5:raise ValueError('Retiro parcial de columnas: requiere revisión manual.')
        if db.execute("SELECT id FROM bridges WHERE code IN ('DEM-01','DEM-02')").fetchone():
            raise ValueError('D7 debe completarse antes del retiro de columnas.')
        def digest_rows():
            output={}
            for table,names in inventory.items():
                names=[name for name in names if name!='simulated']
                rows=[tuple(row) for row in db.execute('SELECT '+','.join(names)+' FROM '+table+' ORDER BY id')]
                output[table]=dict(rows=len(rows),sha256=hashlib.sha256(json.dumps(rows,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()).hexdigest())
            return output
        before=digest_rows()
        def structure():
            if hasattr(db,'schema'):
                queries=[("SELECT indexname,indexdef FROM pg_indexes WHERE schemaname=? ORDER BY indexname",(db.schema,)),
                         ("SELECT conname,pg_get_constraintdef(oid) AS definition FROM pg_constraint WHERE connamespace=?::regnamespace ORDER BY conname",(db.schema,)),
                         ("SELECT tablename,policyname,roles,qual,with_check FROM pg_policies WHERE schemaname=? ORDER BY tablename,policyname",(db.schema,))]
            else:
                queries=[("SELECT name,sql FROM sqlite_master WHERE type IN ('index','trigger','view') ORDER BY name",())]
            return [[tuple(row) for row in db.execute(sql,args)] for sql,args in queries]
        original_structure=structure()
        if apply:
            for table in pending:db.execute('ALTER TABLE '+table+' DROP COLUMN simulated')
            if digest_rows()!=before:raise ValueError('El contenido conservado no coincide; se revierte el retiro.')
            if structure()!=original_structure:raise ValueError('El retiro alteraría índices, restricciones o políticas; se revierte todo.')
            if not hasattr(db,'schema') and db.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Relaciones inválidas; se revierte el retiro.')
        result=dict(applied=apply,columns_to_remove=[table+'.simulated' for table in pending],preserved_rows=before,
                    tables=len(inventory),columns_before=sum(map(len,inventory.values())),columns_after=sum(map(len,inventory.values()))-len(pending))
        if apply:db.commit()
        else:db.rollback()
        return result
    except Exception:
        db.rollback();raise
