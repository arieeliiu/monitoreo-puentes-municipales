"""Plan de retiro de columnas; aplicación explícita, con respaldo, después de D7."""
import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from database import Postgres
from schema_revision import retire_columns


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--sqlite',type=Path);source.add_argument('--postgres',action='store_true')
    parser.add_argument('--schema',choices=['puentes','puentes_test'])
    parser.add_argument('--apply',action='store_true');parser.add_argument('--backup',type=Path)
    args=parser.parse_args()
    if args.apply and not args.backup:parser.error('--apply requiere --backup.')
    if args.postgres:
        if not args.schema or not os.environ.get('PUENTES_MIGRATION_DATABASE_URL'):parser.error('Requiere --schema y PUENTES_MIGRATION_DATABASE_URL explícitos.')
        if args.apply and (not args.backup.is_file() or not args.backup.stat().st_size):parser.error('Respaldo externo PostgreSQL ausente o vacío.')
        db=Postgres(os.environ['PUENTES_MIGRATION_DATABASE_URL'],args.schema)
    else:
        path=args.sqlite.resolve()
        if not path.is_file():parser.error('La base debe existir.')
        db=sqlite3.connect(path.as_uri()+('?mode=rw' if args.apply else '?mode=ro'),uri=True);db.row_factory=sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
    try:
        result=retire_columns(db)
        if args.apply:
            if args.sqlite:
                with args.backup.open('xb'):pass
                backup=sqlite3.connect(args.backup)
                try:db.backup(backup)
                finally:backup.close()
            result=retire_columns(db,apply=True)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    finally:db.close()


if __name__=='__main__':main()
