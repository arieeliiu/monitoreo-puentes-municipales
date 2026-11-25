"""Episodios de alertas: agrupación derivada de alertas abiertas por sensor.

Cada lectura que cumple una regla conserva su propio registro de alerta, asociado al puente y a la
medición que la originó (CA-04.4 y CA-04.5). Un episodio solo reúne, para presentación, avisos y
seguimiento, las alertas abiertas (Activa o En atención) originadas en mediciones de un mismo sensor.

- Se calcula por consulta: no agrega columnas ni requiere migración en SQLite ni en PostgreSQL.
- Cuando todas las alertas del sensor quedan Resueltas, la siguiente superación abre un episodio nuevo.
- Las alertas de inspección visual no se agrupan: cada hallazgo es independiente.
- Las consultas acotan por puente y estado para aprovechar el índice existente alerts(bridge_id,status).
"""
from dashboard_metrics import SEVERITIES

# Rango de severidad: solo la escala vigente EV2 tiene nivel; los históricos valen 0.
RANK = ("CASE WHEN {a}.standard='EV2' THEN CASE {a}.severity WHEN 'Crítico' THEN 3 "
        "WHEN 'Alerta' THEN 2 WHEN 'Atención' THEN 1 ELSE 0 END ELSE 0 END")
OPEN = "{a}.status!='Resuelta'"


def rank(alias):
    return RANK.format(a=alias)


def _top_alert(sensor_ref):
    """Alerta abierta de mayor severidad (y más reciente) del sensor; representa el episodio."""
    return (f"(SELECT t.id FROM alerts t JOIN measurements tm ON tm.id=t.measurement_id "
            f"WHERE tm.sensor_id={sensor_ref} AND {OPEN.format(a='t')} "
            f"ORDER BY {rank('t')} DESC,t.id DESC LIMIT 1)")


def _episodes_sql(where=''):
    grouped = ("SELECT m.sensor_id,count(*) AS n,min(a.id) AS first_id,max(a.id) AS last_id,"
               "min(a.created_at) AS first_at,max(a.created_at) AS last_at,"
               f"sum(CASE WHEN a.status='Activa' THEN 1 ELSE 0 END) AS active "
               f"FROM alerts a JOIN measurements m ON m.id=a.measurement_id WHERE {OPEN.format(a='a')}"
               + where + " GROUP BY m.sensor_id")
    return ("SELECT e.*,s.code AS sensor_code,s.kind,c.name AS component,b.id AS bridge_id,b.code AS bridge_code,"
            "b.name,t.id AS top_id,t.severity,t.standard,r.label "
            f"FROM ({grouped}) e JOIN sensors s ON s.id=e.sensor_id JOIN components c ON c.id=s.component_id "
            f"JOIN bridges b ON b.id=c.bridge_id JOIN alerts t ON t.id={_top_alert('e.sensor_id')} "
            "JOIN rules r ON r.id=t.rule_id")


def _episode(row):
    episode = dict(row)
    episode['status'] = 'Activa' if row['active'] else 'En atención'
    episode['repeated'] = row['n'] > 1
    return episode


def open_episodes(rows):
    """Episodios abiertos de sensores. Su número está acotado por la cantidad de sensores."""
    return [_episode(r) for r in rows(_episodes_sql())]


def episode_for(one, alert):
    """Episodio abierto al que pertenece una alerta de medición; None si no corresponde."""
    if not alert['measurement_id'] or alert['status'] == 'Resuelta':
        return None
    origin = one('SELECT sensor_id FROM measurements WHERE id=?', (alert['measurement_id'],))
    if not origin:
        return None
    row = one(_episodes_sql(' AND a.bridge_id=? AND m.sensor_id=?'), (alert['bridge_id'], origin['sensor_id']))
    return _episode(row) if row else None


def episode_scope(bridge_id, sensor_id, until_id):
    """Filtro SQL de las alertas abiertas del episodio hasta el último registro mostrado al usuario.

    Acotar por until_id evita aplicar un seguimiento a alertas que llegaron después de cargar la página.
    """
    return (f"a.bridge_id=? AND {OPEN.format(a='a')} AND a.id<=? "
            "AND a.measurement_id IN (SELECT id FROM measurements WHERE sensor_id=?)",
            (bridge_id, until_id, sensor_id))


def dashboard_queue(rows, limit=10):
    """Cola priorizada del panel: un elemento por episodio de sensor más los hallazgos visuales abiertos."""
    items = []
    for e in open_episodes(rows):
        items.append(dict(id=e['top_id'], name=e['name'], label=e['label'], severity=e['severity'], standard=e['standard'],
                          status=e['status'], created_at=e['last_at'], first_at=e['first_at'], count=e['n'],
                          sensor_id=e['sensor_id'], sensor_code=e['sensor_code'], origin='Medición'))
    visual = rows("SELECT a.id,a.severity,a.standard,a.status,a.created_at,b.name,b.code AS bridge_code,r.label FROM alerts a "
                  "JOIN bridges b ON b.id=a.bridge_id JOIN rules r ON r.id=a.rule_id "
                  f"WHERE a.inspection_id IS NOT NULL AND {OPEN.format(a='a')} "
                  f"ORDER BY {rank('a')} DESC,a.created_at DESC,a.id DESC LIMIT ?", (limit,))
    for a in visual:
        items.append(dict(a, count=1, first_at=a['created_at'], sensor_id=None, sensor_code=None, origin='Inspección'))
    total = len(items) - len(visual) + rows("SELECT count(*) AS n FROM alerts a WHERE a.inspection_id IS NOT NULL AND "
                                            + OPEN.format(a='a'))[0]['n']
    weight = {s: n + 1 for n, s in enumerate(SEVERITIES)}
    items.sort(key=lambda i: (weight.get(i['severity'], 0) if i['standard'] == 'EV2' else 0, i['created_at'] or '', i['id']),
               reverse=True)
    return items[:limit], total
