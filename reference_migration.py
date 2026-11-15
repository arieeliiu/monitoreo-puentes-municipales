"""Migración D7 explícita, transaccional y ajena al arranque de la aplicación.

Los identificadores retirados solo se admiten aquí como origen de migración.
No cambia IDs, relaciones, lecturas, umbrales, simulated ni históricos de auditoría.
"""
from reference_data import BRIDGE_REFERENCES

LEGACY_CODES = ('DEM-01', 'DEM-02')


def rename_reference_identifiers(connection, apply=False):
    """Devuelve el plan; sin apply revierte la transacción sin escribir datos.

    El llamador debe usar una conexión dedicada y detener los escritores antes
    de aplicar. Inventarios parciales, manuales o destinos ocupados se rechazan.
    """
    try:
        connection.execute('BEGIN IMMEDIATE' if apply else 'BEGIN')
        changes=[]
        for old,(new,_,_) in zip(LEGACY_CODES,BRIDGE_REFERENCES):
            bridge=connection.execute('SELECT id,simulated FROM bridges WHERE code=?',(old,)).fetchone()
            if not bridge: continue
            if not bridge['simulated']:
                raise ValueError('El puente de origen no está marcado como dato de prueba; requiere revisión manual.')
            if connection.execute('SELECT id FROM bridges WHERE code=?',(new,)).fetchone():
                raise ValueError('Identificador de destino ocupado; no se fusionan puentes.')
            changes.append(dict(table='bridges',id=bridge['id'],old=old,new=new))
            for kind in ('vibracion','inclinacion'):
                source=old+'-'+kind.upper();target=new+'-'+kind.upper()
                sensor=connection.execute('SELECT s.id,s.kind,c.bridge_id FROM sensors s JOIN components c ON c.id=s.component_id WHERE s.code=?',(source,)).fetchone()
                if not sensor or sensor['bridge_id']!=bridge['id'] or sensor['kind']!=kind:
                    raise ValueError('El inventario de sensores de origen no coincide; requiere revisión manual.')
                if connection.execute('SELECT id FROM sensors WHERE code=?',(target,)).fetchone():
                    raise ValueError('Código de sensor de destino ocupado; no se sustituyen sensores.')
                changes.append(dict(table='sensors',id=sensor['id'],old=source,new=target))
        if apply:
            for change in changes:
                # table solo puede provenir de las dos constantes internas anteriores.
                connection.execute('UPDATE '+change['table']+' SET code=? WHERE id=? AND code=?',(change['new'],change['id'],change['old']))
                current=connection.execute('SELECT code FROM '+change['table']+' WHERE id=?',(change['id'],)).fetchone()
                if not current or current['code']!=change['new']:
                    raise ValueError('El inventario cambió durante la migración; se revierte todo.')
            connection.commit()
        else: connection.rollback()
        return changes
    except Exception:
        connection.rollback()
        raise
