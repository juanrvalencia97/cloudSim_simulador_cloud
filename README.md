# CloudSim

CloudSim es un simulador web academico de infraestructura cloud. Representa usuarios virtuales, balanceo de carga, nodos de computo, autoescalado, tolerancia basica a fallos, monitoreo en tiempo real y persistencia historica en SQLite.

## Stack

- Backend: Python, Flask y Gunicorn.
- Frontend: HTML, CSS, JavaScript modular y Chart.js.
- Persistencia: SQLite para eventos y muestras de metricas.
- Arquitectura: monolito Flask modular con API REST JSON.

## Ejecucion local

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Si tu entorno creo carpeta `bin`:

```powershell
.\.venv\bin\python.exe -m pip install -r requirements.txt
.\.venv\bin\python.exe app.py
```

Abre:

```text
http://127.0.0.1:5000
```

## Variables de configuracion

Las variables pueden definirse en Render o en el entorno local:

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

## Despliegue en Render

1. Sube el proyecto a GitHub.
2. En Render, crea un nuevo Web Service conectado al repositorio.
3. Usa Python como runtime.
4. Build command:

```bash
pip install -r requirements.txt
```

5. Start command:

```bash
gunicorn app:app --workers 1 --threads 4 --timeout 120
```

6. Configura las variables de entorno anteriores. Usa un solo worker porque el simulador mantiene el estado operativo en memoria.

El archivo `render.yaml` ya contiene una configuracion lista para despliegue.

## Como demostrarlo

1. Abre el dashboard y presenta la arquitectura: usuarios, frontend, backend Flask, balanceador, nodos, autoescalado, fallos y SQLite.
2. Genera 20 o 50 usuarios virtuales.
3. Muestra como el balanceador distribuye solicitudes hacia el nodo con menor carga.
4. Observa metricas y graficas: carga promedio, solicitudes activas, nodos activos y capacidad usada.
5. Espera ciclos de alta carga para mostrar autoescalado.
6. Pulsa `Simular falla` sobre un nodo activo y explica el failover.
7. Muestra que el nodo caido deja de recibir solicitudes y que la carga se redistribuye.
8. Pulsa `Recuperar` para devolver el nodo al pool.
9. Cierra con el panel de eventos cloud como evidencia del comportamiento del sistema.

## Nota academica

CloudSim no crea servidores reales. Los nodos virtuales son objetos de simulacion mantenidos en memoria, mientras SQLite conserva eventos y metricas. Esto permite explicar conceptos de sistemas distribuidos y cloud computing sin introducir Kubernetes, colas, WebSockets o microservicios reales.
