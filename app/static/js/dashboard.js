import { updateCharts } from "./charts.js";
import { formatPercent, formatUptime, setText, statusClass, statusLabel } from "./ui.js";


export function renderDashboard(state) {
    renderMetrics(state.metrics);
    renderSimulationState(state.simulation);
    renderAutoscaling(state.simulation.autoscaling);
    renderNodes(state.nodes);
    renderTraffic(state);
    renderEvents(state.events);
    updateCharts(state.charts);
}


function renderMetrics(metrics) {
    setText("totalRequests", metrics.total_requests);
    setText("processedRequests", metrics.processed_requests);
    setText("activeRequests", metrics.active_requests);
    setText("totalLoad", metrics.used_capacity);
    setText("activeNodes", metrics.active_nodes);
    setText("failedNodes", metrics.failed_nodes);
    setText("availability", formatPercent(metrics.availability));
    setText("averageLoad", formatPercent(metrics.average_load));
    setText("virtualUsers", metrics.virtual_users || 0);
}


function renderSimulationState(simulation) {
    const element = document.getElementById("simulationState");

    if (!element) {
        return;
    }

    element.textContent = simulation.running ? "Ejecutandose" : "En espera";
    element.classList.toggle("status-ok", simulation.running);
    element.classList.toggle("status-idle", !simulation.running);
}


function renderAutoscaling(autoscaling) {
    if (!autoscaling) {
        return;
    }

    const statusElement = document.getElementById("autoscalingStatus");

    if (statusElement) {
        statusElement.textContent = autoscaling.enabled ? "Activo" : "Inactivo";
        statusElement.classList.toggle("status-ok", autoscaling.enabled);
        statusElement.classList.toggle("status-idle", !autoscaling.enabled);
    }

    setText("scaleUpRule", `> ${autoscaling.scale_up_threshold}%`);
    setText("scaleDownRule", `< ${autoscaling.scale_down_threshold}%`);
    setText("minNodes", `${autoscaling.min_nodes} nodos`);
    setText("maxNodes", `${autoscaling.max_nodes} nodos`);
}


function renderTraffic(state) {
    const activeRequestsElement = document.getElementById("topologyActiveRequests");
    const usersElement = document.getElementById("topologyUsers");
    const loadElement = document.getElementById("topologyLoad");
    const lastTargetElement = document.getElementById("lastBalancerTarget");
    const requestsContainer = document.getElementById("requestsContainer");
    const loadBalancer = state.simulation.load_balancer || {};

    if (activeRequestsElement) {
        activeRequestsElement.textContent = state.metrics.active_requests;
    }

    if (usersElement) {
        usersElement.textContent = state.metrics.virtual_users || 0;
    }

    if (loadElement) {
        loadElement.textContent = `${state.metrics.used_capacity}/${state.metrics.total_capacity}`;
    }

    if (lastTargetElement) {
        lastTargetElement.textContent = loadBalancer.last_target_node_id
            ? `Node-${loadBalancer.last_target_node_id}`
            : "N/A";
    }

    setText("balancerStrategy", loadBalancer.strategy === "round_robin" ? "Round robin" : "Menor carga");
    setText("availableNodes", `${loadBalancer.available_nodes || 0} nodos`);

    if (!requestsContainer) {
        return;
    }

    const requests = state.requests.slice(0, 8);

    if (!requests.length) {
        requestsContainer.innerHTML = `
            <article class="request-item request-empty">
                <span>Sin solicitudes activas</span>
            </article>
        `;
        return;
    }

    requestsContainer.innerHTML = requests.map((request) => `
        <article class="request-item">
            <strong>REQ-${request.id}</strong>
            <span>User-${String(request.user_id).padStart(3, "0")}</span>
            <span class="request-node">Node-${request.node_id}</span>
            <span>${request.load_cost} u.</span>
        </article>
    `).join("");
}


function renderNodes(nodes) {
    const container = document.getElementById("nodesContainer");

    if (!container) {
        return;
    }

    container.innerHTML = nodes.map((node) => `
        <article class="node-card ${node.status === "FAILED" ? "node-card-failed" : ""}">
            <div class="node-card-header">
                <h3>${node.name}</h3>
                <span class="status-pill ${statusClass(node.status)}">${statusLabel(node.status)}</span>
            </div>
            <p class="node-serving">${node.failed ? "Fuera del balanceador" : `Atendiendo ${node.active_requests} solicitudes`}</p>
            <div class="load-track" aria-hidden="true">
                <div class="load-bar ${node.status === "OVERLOADED" ? "load-bar-warning" : ""}" style="width: ${node.usage_percentage}%"></div>
            </div>
            <div class="node-meta">
                <span>Carga ${formatPercent(node.usage_percentage)}</span>
                <span>${node.current_load}/${node.max_capacity}</span>
            </div>
            <dl class="node-stats">
                <div>
                    <dt>Activas</dt>
                    <dd>${node.active_requests}</dd>
                </div>
                <div>
                    <dt>Procesadas</dt>
                    <dd>${node.processed_requests}</dd>
                </div>
                <div>
                    <dt>Uptime</dt>
                    <dd>${formatUptime(node.uptime_seconds)}</dd>
                </div>
            </dl>
            <div class="node-actions">
                <button type="button" data-action="assign-request" data-node-id="${node.id}" ${node.active ? "" : "disabled"}>+ Solicitud</button>
                <button type="button" data-action="release-request" data-node-id="${node.id}" ${node.active_requests > 0 ? "" : "disabled"}>- Solicitud</button>
                <button type="button" data-action="${node.failed ? "recover-node" : "deactivate-node"}" data-node-id="${node.id}" ${node.active || node.failed ? "" : "disabled"}>
                    ${node.failed ? "Recuperar" : "Simular falla"}
                </button>
                <button type="button" data-action="delete-node" data-node-id="${node.id}">Eliminar</button>
            </div>
        </article>
    `).join("");
}


function renderEvents(events) {
    const container = document.getElementById("eventsContainer");

    if (!container) {
        return;
    }

    container.innerHTML = events.map((event) => `
        <article class="event-item event-${String(event.severity || "info").toLowerCase()}">
            <strong>${event.type}</strong>
            <p>${event.description}</p>
        </article>
    `).join("");
}
