# Despliegue En Render

## Configuracion Recomendada

- Runtime: Python.
- Build command: `pip install -r requirements.txt`.
- Start command: `gunicorn app:app --workers 1 --threads 4 --timeout 120`.
- Plan: Free es suficiente para la demostracion.

## Variables

```text
FLASK_DEBUG=false
SECRET_KEY=change-this-in-render
INITIAL_NODE_COUNT=3
MIN_NODE_COUNT=2
MAX_NODE_COUNT=8
NODE_CAPACITY=100
METRICS_HISTORY_LIMIT=36
SCALE_UP_THRESHOLD=80
SCALE_DOWN_THRESHOLD=20
SCALE_UP_CYCLES=2
SCALE_DOWN_CYCLES=4
```

## Nota Sobre SQLite

En el plan gratuito de Render, el disco del servicio puede reiniciarse. Para una exposicion universitaria esto no afecta la demostracion porque el simulador reconstruye nodos iniciales al arrancar. Si se requiere conservar historico entre reinicios, se debe agregar un Persistent Disk y apuntar `DATABASE_PATH` hacia esa ruta.
