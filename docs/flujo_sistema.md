# Flujo Del Sistema

1. El usuario abre el dashboard.
2. Flask sirve `index.html` y archivos estaticos.
3. JavaScript consulta `/api/status` cada 1.5 segundos.
4. El backend avanza un ciclo de simulacion si hay trafico activo.
5. Los usuarios virtuales generan solicitudes.
6. El balanceador selecciona el nodo saludable con menor carga.
7. Los nodos aumentan o liberan carga segun solicitudes activas.
8. El autoescalado evalua carga sostenida.
9. Si un nodo falla, se drenan solicitudes y se redistribuyen.
10. Se guardan eventos y metricas en SQLite.
11. El frontend actualiza tarjetas, graficas, nodos y eventos.

## Demostracion Sugerida

- Generar 20 usuarios para mostrar distribucion.
- Generar 50 usuarios para forzar alta carga.
- Observar creacion automatica de nodos.
- Simular falla de un nodo con solicitudes activas.
- Mostrar failover y recuperacion.
- Explicar el log de eventos como auditoria del control plane.
