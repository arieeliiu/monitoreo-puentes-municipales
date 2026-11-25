"""Esquema 2D del puente: ubica cada sensor en su componente estructural.

El esquema es genérico y no está a escala. Los registros no contienen coordenadas, por lo que la
posición se informa por componente: los marcadores se distribuyen dentro de la zona del componente
y nunca se presentan como un punto medido. La ubicación descrita por la DOM se muestra en el detalle.
"""
import unicodedata
from datetime import datetime, timedelta, timezone

from display_time import chile_datetime
from number_format import decimal

SEVERITY_STATE = {'Atención': 'attention', 'Alerta': 'alert', 'Crítico': 'critical'}
STATE_LABELS = {
    'critical': 'Crítico', 'alert': 'Alerta', 'attention': 'Atención', 'ok': 'Sin alerta',
    'valid': 'Lectura válida', 'invalid': 'Dato no válido o no disponible', 'nodata': 'Sin datos',
}
CONDITION_TONE = {'Baja': 'info', 'Media': 'attention', 'Alta': 'alert', 'Crítica': 'critical'}

# Geometría del esquema (viewBox visible 0 62 1000 236). lane: (x inicial, x final, y) de los marcadores.
ZONES = {
    'estribo': dict(paths=('M44 140H120V270H30Z', 'M880 140H956L970 270H880Z'), label=(500, 262, 'middle'),
                    lane=(380, 620, 236), inspection=(925, 205), connector=(120, 880, 236)),
    'viga': dict(paths=('M120 140H880V176H120Z',), label=(134, 163, 'start'), lane=(270, 730, 158), inspection=(850, 158)),
    'tablero': dict(paths=('M30 110H970V140H30Z',), label=(40, 100, 'start'), lane=(200, 800, 86), inspection=(930, 86)),
    'pila': dict(paths=('M486 176H514V270H486Z',), label=(524, 258, 'start'), lane=(500, 500, 208), inspection=(560, 222)),
}
ORDER = ('estribo', 'viga', 'pila', 'tablero')


def zone_key(name):
    # Primera palabra completa, singular o plural: "Viga principal" y "Vigas" sí; "Pilar de iluminación" no.
    plain = unicodedata.normalize('NFKD', str(name or '')).encode('ascii', 'ignore').decode().strip().lower()
    first = plain.split()[0] if plain.split() else ''
    return next((key for key in ZONES if first in (key, key + 's')), None)


def spread(count, start, end, y, spacing=72):
    """Distribuye marcadores dentro de la zona, centrados; no representa posiciones medidas."""
    if not count:
        return []
    step = min(spacing, (end - start) / max(count - 1, 1)) if count > 1 else 0
    center = (start + end) / 2
    return [(round(center + (i - (count - 1) / 2) * step), y) for i in range(count)]


def sensor_state(sensor, alerts_enabled):
    if not sensor['mid']:
        return 'nodata'
    if sensor['status'] != 'valido':
        return 'invalid'
    if alerts_enabled and sensor['alert_severity'] in SEVERITY_STATE:
        return SEVERITY_STATE[sensor['alert_severity']]
    if alerts_enabled and sensor['evaluation'] == 'Evaluada':
        return 'ok'
    return 'valid'


def reading_text(sensor):
    if not sensor['mid']:
        return 'Sin lecturas registradas'
    if sensor['status'] != 'valido':
        return 'Último dato: ' + sensor['status'].replace('_', ' ')
    if sensor['specification'] != 'EV2':
        return 'Último dato: registro histórico, no evaluado con criterios vigentes'
    if sensor['kind'] == 'inclinacion':
        change = f" · cambio absoluto {decimal(sensor['variation'])} °" if sensor['variation'] is not None else ' · referencia no configurada'
        return f"Lectura {decimal(sensor['value'])} °{change}"
    return f"Última lectura {decimal(sensor['value'])} {sensor['unit']}"


def is_stale(value, now):
    try:
        instant = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return instant.tzinfo is not None and instant < now - timedelta(hours=24)
    except (TypeError, ValueError):
        return False


def marker(sensor, component, labels, alerts_enabled, now, position=None):
    state = sensor_state(sensor, alerts_enabled)
    parts = [sensor['code'], labels.get(sensor['kind'], sensor['kind']), 'Componente: ' + component['name'],
             'Ubicación descrita: ' + (sensor['location'] or 'sin descripción'), reading_text(sensor)]
    if sensor['mid']:
        parts.append(chile_datetime(sensor['measured_at']) + (' · sin lecturas en las últimas 24 horas' if is_stale(sensor['measured_at'], now) else ''))
    parts.append('Estado: ' + STATE_LABELS[state])
    result = dict(id=sensor['id'], code=sensor['code'], letter='I' if sensor['kind'] == 'inclinacion' else 'V',
                  state=state, state_label=STATE_LABELS[state], title=' · '.join(parts),
                  href=f"/measurements?sensor_id={sensor['id']}")
    if position:
        result['x'], result['y'] = position
    return result


def inspection_marker(inspection, position):
    tone = CONDITION_TONE.get(inspection['condition'], 'muted') if inspection['standard'] == 'EV2' else 'muted'
    title = (f"Última inspección visual · condición {inspection['condition']}"
             + ('' if inspection['standard'] == 'EV2' else ' (categoría histórica)') + ' · ' + chile_datetime(inspection['inspected_at']))
    return dict(id=inspection['id'], tone=tone, title=title, x=position[0], y=position[1], href=f"/inspections/{inspection['id']}")


def build(components, sensors, inspections, labels, alerts_enabled, now=None):
    now = now or datetime.now(timezone.utc)
    assigned, others = {}, []
    for component in components:
        key = zone_key(component['name'])
        if key and key not in assigned:
            assigned[key] = component
        else:
            others.append(component)
    latest_inspection = {}
    for inspection in inspections:  # ordenadas de la más reciente a la más antigua
        latest_inspection.setdefault(inspection['component_id'], inspection)
    by_component = {}
    for sensor in sensors:
        by_component.setdefault(sensor['component_id'], []).append(sensor)
    zones = []
    for key in ORDER:
        component = assigned.get(key)
        if key == 'pila' and not component:
            continue
        geometry = dict(ZONES[key])
        if key == 'estribo' and 'pila' in assigned:
            geometry['lane'] = (300, 440, 236)
        members = by_component.get(component['id'], []) if component else []
        start, end, y = geometry['lane']
        if key == 'pila':
            positions = [(500, y + i * 30) for i in range(len(members))]
        else:
            positions = spread(len(members), start, end, y)
        zones.append(dict(key=key, component=component, paths=geometry['paths'], label=geometry['label'],
                          connector=geometry.get('connector') if members else None,
                          markers=[marker(s, component, labels, alerts_enabled, now, p) for s, p in zip(members, positions)],
                          inspection=inspection_marker(latest_inspection[component['id']], geometry['inspection'])
                          if component and component['id'] in latest_inspection else None))
    extra = [dict(component=c, markers=[marker(s, c, labels, alerts_enabled, now) for s in by_component.get(c['id'], [])],
                  inspection=latest_inspection.get(c['id'])) for c in others]
    states = [m['state'] for z in zones for m in z['markers']] + [m['state'] for o in extra for m in o['markers']]
    legend = [(state, STATE_LABELS[state]) for state in ('critical', 'alert', 'attention', 'ok', 'valid', 'invalid', 'nodata')
              if alerts_enabled or state not in ('critical', 'alert', 'attention', 'ok')]
    return dict(zones=zones, others=extra, legend=legend, sensor_count=len(states),
                summary={state: states.count(state) for state in STATE_LABELS if states.count(state)})
