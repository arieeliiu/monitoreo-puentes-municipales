"""Ubicaciones iniciales del piloto; no modifica inventario ni datos manuales."""
from reference_data import BRIDGE_REFERENCES, reference_inventory

LOCATIONS = {
    'Tablero': {
        'vibracion': 'Tablero: cara inferior, centro del vano, eje longitudinal',
        'inclinacion': 'Tablero: borde lateral, extremo junto al estribo de acceso',
    },
    'Viga': {
        'vibracion': 'Viga: ala inferior, centro del vano',
        'inclinacion': 'Viga: alma, extremo junto al apoyo de acceso',
    },
    'Estribo': {
        'vibracion': 'Estribo: coronamiento, junto al apoyo del tablero',
        'inclinacion': 'Estribo: cara interior del muro, bajo el apoyo del tablero',
    },
}


def complete_demo_locations(connection):
    """Solo sensores canónicos asociados al inventario de referencia verificado.

    Un sensor sin ubicación se reconoce por vacío o por el marcador de migración.
    La ubicación deriva del componente actual; nunca se reasocia el sensor.
    Componentes desconocidos y códigos personalizados requieren criterio de DOM.
    La transacción y la auditoría pertenecen al llamador.
    """
    reference_inventory(connection, BRIDGE_REFERENCES)
    sensors = connection.execute('''
        SELECT s.id, s.kind, s.location, c.name
        FROM sensors s JOIN components c ON c.id=s.component_id
        JOIN bridges b ON b.id=c.bridge_id
        WHERE b.code IN (?,?)
          AND s.code=b.code || '-' || upper(s.kind)
    ''',tuple(item[0] for item in BRIDGE_REFERENCES)).fetchall()
    changed = 0
    for sensor_id, kind, location, component in sensors:
        if (location or '').strip().casefold() not in ('', 'pendiente de precisar'):
            continue
        position = LOCATIONS.get(component, {}).get(kind)
        if position:
            connection.execute('UPDATE sensors SET location=? WHERE id=?', (position, sensor_id))
            changed += 1
    return changed
