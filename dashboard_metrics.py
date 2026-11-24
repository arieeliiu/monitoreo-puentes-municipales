"""Indicadores y series del panel. Solo lectura: agrega registros existentes, sin escribir ni inventar datos.

Las agregaciones se hacen en SQL sobre ventanas acotadas (compatible SQLite/PostgreSQL) para no traer
lecturas individuales a memoria. Los instantes persistidos son texto ISO 8601 en UTC; los históricos sin
zona horaria registrada se excluyen de las ventanas temporales, igual que en los filtros por fecha.
"""
from datetime import datetime, timedelta, timezone

from display_time import CHILE, day_start_utc

SEVERITIES = ('Atención', 'Alerta', 'Crítico')
SEVERITY_RANK = "CASE {c} WHEN 'Crítico' THEN 3 WHEN 'Alerta' THEN 2 WHEN 'Atención' THEN 1 ELSE 0 END"
SERIES_RANGES = {'1': (1, 15, '10 minutos'), '7': (7, 13, 'hora'), '30': (30, 13, 'hora')}


def zoned(column):
    """Solo instantes con zona UTC explícita (contrato persistido)."""
    return f"(substr({column},length({column})-5)='+00:00' OR substr({column},length({column}),1)='Z')"


def iso(instant):
    return instant.astimezone(timezone.utc).isoformat(timespec='seconds')


def today_chile(now=None):
    return (now or datetime.now(timezone.utc)).astimezone(CHILE).date()


def bucket_instant(text):
    """Convierte un prefijo ISO UTC agrupado (hora o decena de minutos) en instante."""
    padded = {13: ':00:00', 15: '0:00'}.get(len(text))
    if padded is None:
        return None
    try:
        return datetime.fromisoformat(text + padded + '+00:00')
    except ValueError:
        return None


def alert_summary(rows):
    data = rows("SELECT status,severity,standard,count(*) AS n FROM alerts WHERE status!='Resuelta' GROUP BY status,severity,standard")
    summary = dict(total=0, active=0, attending=0, legacy=0, severity={s: 0 for s in SEVERITIES})
    for row in data:
        summary['total'] += row['n']
        summary['active' if row['status'] == 'Activa' else 'attending'] += row['n']
        if row['standard'] == 'EV2' and row['severity'] in SEVERITIES:
            summary['severity'][row['severity']] += row['n']
        else:
            summary['legacy'] += row['n']
    summary['bar'] = proportion_bar([(summary['severity'][s], cls) for s, cls in
                                     (('Crítico', 'bar-critical'), ('Alerta', 'bar-alert'), ('Atención', 'bar-attention'))]
                                    + [(summary['legacy'], 'bar-legacy')])
    return summary


def sensor_summary(one, now):
    total = one('SELECT count(*) AS n FROM sensors')['n']
    since = iso(now - timedelta(hours=24))
    reporting = one("SELECT count(DISTINCT sensor_id) AS n FROM measurements WHERE status='valido' AND measured_at>=? AND "
                    + zoned('measured_at'), (since,))['n']
    return dict(total=total, reporting=reporting)


def maintenance_summary(rows, one, user, today):
    scoped = user['role'] == 'Mantención'
    scope, args = (' AND assignee_id=?', (user['id'],)) if scoped else ('', ())
    counts = {row['status']: row['n'] for row in rows('SELECT status,count(*) AS n FROM tasks WHERE 1=1' + scope + ' GROUP BY status', args)}
    overdue = one("SELECT count(*) AS n FROM tasks WHERE status!='Completada' AND planned_date<?" + scope, (today.isoformat(), *args))['n']
    upcoming = one("SELECT count(*) AS n FROM tasks WHERE status!='Completada' AND planned_date>=? AND planned_date<=?" + scope,
                   (today.isoformat(), (today + timedelta(days=7)).isoformat(), *args))['n']
    pending, progress, done = (counts.get(s, 0) for s in ('Pendiente', 'En ejecución', 'Completada'))
    return dict(scoped=scoped, pending=pending, progress=progress, done=done, total=pending + progress + done,
                open=pending + progress, overdue=overdue, upcoming=upcoming,
                bar=proportion_bar([(done, 'seg-done'), (progress, 'seg-progress'), (pending, 'seg-pending')]))


def inspection_summary(one, now):
    since = iso(now - timedelta(days=30))
    recent = one('SELECT count(*) AS n FROM inspections WHERE inspected_at>=? AND ' + zoned('inspected_at'), (since,))['n']
    last = one('SELECT inspected_at FROM inspections ORDER BY inspected_at DESC,id DESC LIMIT 1')
    return dict(recent=recent, last=last['inspected_at'] if last else None)


def proportion_bar(parts):
    """Segmentos enteros sobre 0–100 para una barra SVG con preserveAspectRatio=none."""
    total = sum(n for n, _ in parts)
    segments, x = [], 0
    if not total:
        return segments
    for index, (n, cls) in enumerate(parts):
        if not n:
            continue
        width = 100 - x if index == len(parts) - 1 or all(not m for m, _ in parts[index + 1:]) else round(n * 100 / total)
        segments.append(dict(x=x, width=max(width, 1), cls=cls, n=n))
        x += width
    return segments


def nice_ceiling(value, ticks=4):
    """Máximo del eje como múltiplo entero de un paso 1/2/5·10^k, para marcas sin decimales."""
    target = max(value / ticks, 1)
    magnitude = 10 ** (len(str(int(target))) - 1)
    for factor in (1, 2, 5, 10):
        if factor * magnitude >= target:
            return factor * magnitude * ticks
    return 10 * magnitude * ticks


def alerts_by_day(rows, now, days=30):
    """Alertas generadas por día de Chile, apiladas por severidad (geometría SVG en enteros)."""
    last_day = today_chile(now)
    first_day = last_day - timedelta(days=days - 1)
    data = rows('SELECT substr(created_at,1,13) AS hour,severity,standard,count(*) AS n FROM alerts WHERE created_at>=? AND '
                + zoned('created_at') + ' GROUP BY substr(created_at,1,13),severity,standard', (iso(day_start_utc(first_day)),))
    buckets = {first_day + timedelta(days=n): dict(Atención=0, Alerta=0, Crítico=0, Histórica=0) for n in range(days)}
    for row in data:
        instant = bucket_instant(row['hour'])
        if instant is None:
            continue
        day = instant.astimezone(CHILE).date()
        if day in buckets:
            key = row['severity'] if row['standard'] == 'EV2' and row['severity'] in SEVERITIES else 'Histórica'
            buckets[day][key] += row['n']
    total = sum(sum(b.values()) for b in buckets.values())
    peak = max((sum(b.values()) for b in buckets.values()), default=0)
    top = nice_ceiling(peak)
    width, height, left, right, top_pad, bottom = 720, 200, 40, 8, 10, 24
    plot_w, plot_h = width - left - right, height - top_pad - bottom
    slot = plot_w / days
    bar_w = max(int(slot * 0.62), 3)
    bars = []
    for index, (day, counts) in enumerate(sorted(buckets.items())):
        x = round(left + index * slot + (slot - bar_w) / 2)
        y = height - bottom
        segments = []
        for key, cls in (('Histórica', 'bar-legacy'), ('Atención', 'bar-attention'), ('Alerta', 'bar-alert'), ('Crítico', 'bar-critical')):
            if counts[key]:
                h = max(round(counts[key] * plot_h / top), 1)
                y -= h
                segments.append(dict(cls=cls, y=y, h=h))
        detail = ', '.join(f'{k} {v}' for k, v in counts.items() if v)
        bars.append(dict(x=x, w=bar_w, slot_x=round(left + index * slot), slot_w=max(round(slot), 1), segments=segments,
                         total=sum(counts.values()), title=day.strftime('%d/%m/%Y') + ' · ' + (f'{sum(counts.values())} alertas ({detail})' if detail else 'sin alertas'),
                         label=day.strftime('%d/%m') if index % 5 == 0 or index == days - 1 else ''))
    ticks = [dict(value=f'{top * n // 4:,}'.replace(',', '.'), y=round(height - bottom - plot_h * n / 4)) for n in range(5)]
    return dict(bars=bars, ticks=ticks, total=total, width=width, height=height, left=left, right=width - right,
                baseline=height - bottom, label_y=height - 6, days=days,
                first=first_day.strftime('%d/%m/%Y'), last=last_day.strftime('%d/%m/%Y'))


def measurement_series(rows, labels, kinds, *, days_key='7', bridge_id=None, sensor_id=None, with_thresholds=False, now=None):
    """Máximo por intervalo de lecturas válidas EV2; en inclinación, del cambio absoluto evaluado."""
    days, width, bucket_name = SERIES_RANGES[days_key]
    now = now or datetime.now(timezone.utc)
    since = iso(now - timedelta(days=days))
    filters, args = [], []
    if bridge_id is not None:
        filters.append('c.bridge_id=?'); args.append(bridge_id)
    if sensor_id is not None:
        filters.append('s.id=?'); args.append(sensor_id)
    scope = ''.join(' AND ' + f for f in filters)
    sensors = rows('SELECT s.id,s.code,s.kind,s.unit,s.reference_value,c.name AS component,c.bridge_id,b.code AS bridge_code,b.name AS bridge '
                   'FROM sensors s JOIN components c ON c.id=s.component_id JOIN bridges b ON b.id=c.bridge_id WHERE 1=1' + scope + ' ORDER BY b.code,s.kind DESC,s.code', tuple(args))
    if not sensors:
        return []
    source = ' FROM measurements m JOIN sensors s ON s.id=m.sensor_id JOIN components c ON c.id=s.component_id WHERE m.measured_at>=? AND ' + zoned('m.measured_at') + scope
    bucket = f'substr(m.measured_at,1,{width})'
    points = rows("SELECT m.sensor_id," + bucket + " AS bucket,max(CASE WHEN s.kind='inclinacion' THEN m.variation ELSE m.value END) AS peak,count(*) AS n"
                  + source + " AND m.status='valido' AND m.specification='EV2' GROUP BY m.sensor_id," + bucket + ' ORDER BY m.sensor_id,bucket', (since, *args))
    counts = rows('SELECT m.sensor_id,m.status,count(*) AS n' + source + ' GROUP BY m.sensor_id,m.status', (since, *args))
    thresholds = {}
    if with_thresholds:
        for rule in rows("SELECT bridge_id,kind,severity,min(threshold) AS threshold FROM rules WHERE active=1 AND standard='EV2' AND threshold IS NOT NULL AND kind IN ('vibracion','inclinacion') GROUP BY bridge_id,kind,severity"):
            if rule['severity'] in SEVERITIES:
                thresholds.setdefault((rule['bridge_id'], rule['kind']), []).append(dict(severity=rule['severity'], value=rule['threshold']))
    by_sensor = {}
    for row in points:
        instant = bucket_instant(row['bucket'])
        if instant is None or row['peak'] is None:
            continue
        local = instant.astimezone(CHILE)
        by_sensor.setdefault(row['sensor_id'], []).append([int(instant.timestamp() * 1000), round(float(row['peak']), 4), local.strftime('%d/%m/%Y %H:%M'), row['n']])
    status = {}
    for row in counts:
        status.setdefault(row['sensor_id'], {})[row['status']] = row['n']
    result = []
    for s in sensors:
        inclination = s['kind'] == 'inclinacion'
        levels = sorted(thresholds.get((s['bridge_id'], s['kind']), []), key=lambda t: SEVERITIES.index(t['severity']))
        result.append(dict(id=s['id'], code=s['code'], kind=s['kind'], label=labels.get(s['kind'], s['kind']),
                           unit=kinds.get(s['kind'], s['unit']), component=s['component'], bridge=s['bridge'], bridge_code=s['bridge_code'],
                           metric=('Cambio absoluto respecto de la referencia' if inclination else labels.get(s['kind'], s['kind'])) + f' · máximo por {bucket_name}',
                           reference_missing=inclination and s['reference_value'] is None,
                           thresholds=levels, points=by_sensor.get(s['id'], []), counts=status.get(s['id'], {})))
    return result
