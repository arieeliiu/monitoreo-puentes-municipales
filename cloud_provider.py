"""Proveedor simulado reproducible por minuto, independiente del ordenador."""
from datetime import datetime, timezone


def cloud_records(at=None):
    stamp = (at or datetime.now(timezone.utc)).replace(second=0, microsecond=0).isoformat()
    return [dict(external_id=f'nube-{stamp}-{bridge}-{kind}', bridge_code=f'DEM-0{bridge}',
                 sensor_code=f'DEM-0{bridge}-{kind.upper()}', kind=kind, unit=unit, value=value,
                 measured_at=stamp, status='valido', simulated=True)
            for bridge in (1, 2)
            for kind, unit, value in [('vibracion','m/s²',1.0),('inclinacion','°',-0.229)]]
