# Arquitectura De CloudSim

CloudSim usa un monolito Flask modular. La aplicacion es centralizada para facilitar ejecucion y despliegue, pero sus modulos representan conceptos de infraestructura cloud.

## Flujo General

```text
Usuarios simulados
  -> Frontend Web
  -> API Flask
  -> Motor de simulacion
      -> Balanceador de carga
      -> Gestor de nodos virtuales
      -> Autoescalado
      -> Tolerancia a fallos
      -> Monitor de metricas
      -> SQLite
```

## Responsabilidades

- `app.py`: punto de entrada local y objeto WSGI para Render.
- `config.py`: parametros de simulacion y variables de entorno.
- `routes`: endpoints HTML y JSON.
- `services`: reglas de simulacion, nodos, balanceo, autoescalado y fallos.
- `models`: modelo de nodo y esquema SQLite.
- `repositories`: acceso a SQLite para eventos y metricas.
- `static/js`: consumo de API, render del dashboard y graficas Chart.js.
- `static/css`: diseno visual responsive del panel cloud.

## Conceptos Cloud Representados

- Usuarios concurrentes: usuarios virtuales.
- Instancias cloud: nodos virtuales.
- Load Balancer: seleccion de nodo por menor carga.
- Elasticidad: creacion y retiro automatico de nodos.
- Alta disponibilidad: exclusion de nodos fallidos y redistribucion.
- Observabilidad: metricas, graficas y eventos.
- Almacenamiento centralizado: SQLite.

## Decision De Diseno

El estado operativo vive en memoria porque es una simulacion interactiva. SQLite guarda trazabilidad historica de eventos y metricas. En Render se usa un solo worker para evitar duplicar el estado de simulacion.
