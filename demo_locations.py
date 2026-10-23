"""Ubicaciones iniciales del piloto; no modifica inventario ni datos manuales."""

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
    """Solo los cuatro códigos originales en puentes marcados como simulados.

    Un sensor sin ubicación se reconoce por vacío o por el marcador de migración.
    La ubicación deriva del componente actual; nunca se reasocia el sensor.
    Componentes desconocidos y códigos personalizados requieren criterio de DOM.
    La transacción y la auditoría pertenecen al llamador.
    """
    sensors = connection.execute('''
        SELECT s.id, s.kind, s.location, c.name
        FROM sensors s JOIN components c ON c.id=s.component_id
        JOIN bridges b ON b.id=c.bridge_id
        WHERE b.simulated=1 AND b.code IN ('DEM-01','DEM-02')
          AND s.code=b.code || '-' || upper(s.kind)
    ''').fetchall()
    changed = 0
    for sensor_id, kind, location, component in sensors:
        if (location or '').strip().casefold() not in ('', 'pendiente de precisar'):
            continue
        position = LOCATIONS.get(component, {}).get(kind)
        if position:
            connection.execute('UPDATE sensors SET location=? WHERE id=?', (position, sensor_id))
            changed += 1
    return changed
