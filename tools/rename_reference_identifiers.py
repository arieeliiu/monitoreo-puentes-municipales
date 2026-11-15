"""Planifica D7 por defecto. Aplicación solo explícita y con respaldo indicado.

No se invoca desde la web, seed-demo, migraciones de esquema ni despliegues.
"""
import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from database import Postgres
from reference_migration import rename_reference_identifiers


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--sqlite',type=Path)
    source.add_argument('--postgres',action='store_true',help='Usa solo PUENTES_MIGRATION_DATABASE_URL del entorno.')
    parser.add_argument('--schema',choices=['puentes','puentes_test'])
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--backup',type=Path,help='SQLite: archivo nuevo para copia; PostgreSQL: respaldo externo existente y verificado.')
    args=parser.parse_args()
    if args.apply and not args.backup: parser.error('--apply requiere --backup y autorización del entorno.')
    if args.postgres:
        if not args.schema: parser.error('PostgreSQL requiere --schema explícito.')
        url=os.environ.get('PUENTES_MIGRATION_DATABASE_URL')
        if not url: parser.error('Falta PUENTES_MIGRATION_DATABASE_URL; no se utiliza DATABASE_URL automáticamente.')
        if args.apply and (not args.backup.is_file() or args.backup.stat().st_size==0):
            parser.error('Verifica primero el respaldo PostgreSQL externo; debe ser un archivo existente no vacío.')
        connection=Postgres(url,args.schema)
    else:
        path=args.sqlite.resolve()
        if not path.is_file(): parser.error('La base SQLite debe existir; no se crea una nueva.')
        connection=sqlite3.connect(path.as_uri()+('?mode=rw' if args.apply else '?mode=ro'),uri=True)
        connection.row_factory=sqlite3.Row
        connection.execute('PRAGMA foreign_keys=ON')
    try:
        plan=rename_reference_identifiers(connection)
        if args.apply:
            if args.sqlite:
                # O_EXCL impide sustituir una copia anterior o la propia base.
                with args.backup.open('xb'): pass
                backup=sqlite3.connect(args.backup)
                try: connection.backup(backup)
                finally: backup.close()
            plan=rename_reference_identifiers(connection,apply=True)
        print(json.dumps(dict(applied=args.apply,changes=plan),ensure_ascii=False,indent=2))
    finally: connection.close()


if __name__=='__main__':main()
