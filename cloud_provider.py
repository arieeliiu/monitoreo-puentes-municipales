"""Proveedor de referencia reproducible por minuto."""
from datetime import datetime, timezone
from reference_data import BRIDGE_REFERENCES


def cloud_records(at=None):
    stamp = (at or datetime.now(timezone.utc)).replace(second=0, microsecond=0).isoformat()
    return [dict(external_id=f'nube-{stamp}-{bridge}-{kind}', bridge_code=code,
                 sensor_code=f'{code}-{kind.upper()}', kind=kind, unit=unit, value=value,
                 measured_at=stamp, status='valido')
            for bridge,(code,_,_) in enumerate(BRIDGE_REFERENCES,1)
            for kind, unit, value in [('vibracion','m/s²',1.0),('inclinacion','°',-0.229)]]
