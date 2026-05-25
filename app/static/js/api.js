const JSON_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
};


async function requestJson(endpoint, options = {}) {
    const response = await fetch(endpoint, {
        headers: JSON_HEADERS,
        ...options,
    });

    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.error || `Request failed: ${response.status}`);
    }

    return response.json();
}


export function getStatus() {
    return requestJson("/api/status");
}


export function getHealth() {
    return requestJson("/api/health");
}


export function generateUsers(count) {
    return requestJson("/api/traffic/users", {
        method: "POST",
        body: JSON.stringify({ count }),
    });
}


export function createNode() {
    return requestJson("/api/nodes", {
        method: "POST",
        body: JSON.stringify({}),
    });
}


export function deleteNode(nodeId) {
    return requestJson(`/api/nodes/${nodeId}`, {
        method: "DELETE",
    });
}


export function activateNode(nodeId) {
    return requestJson(`/api/nodes/${nodeId}/activate`, {
        method: "POST",
        body: JSON.stringify({}),
    });
}


export function recoverNode(nodeId) {
    return requestJson(`/api/nodes/${nodeId}/recover`, {
        method: "POST",
        body: JSON.stringify({}),
    });
}


export function deactivateNode(nodeId) {
    return requestJson(`/api/nodes/${nodeId}/deactivate`, {
        method: "POST",
        body: JSON.stringify({}),
    });
}


export function assignRequest(nodeId, loadCost = 12) {
    return requestJson(`/api/nodes/${nodeId}/requests`, {
        method: "POST",
        body: JSON.stringify({ load_cost: loadCost }),
    });
}


export function releaseRequest(nodeId) {
    return requestJson(`/api/nodes/${nodeId}/release`, {
        method: "POST",
        body: JSON.stringify({}),
    });
}

export function resetSimulation() {
    return requestJson("/api/reset", { method: "POST" });
}

export function togglePause() {
    return requestJson("/api/traffic/pause", { method: "POST" });
}

export function removeUsers(count) {
    return requestJson("/api/traffic/users", {
        method: "DELETE",
        body: JSON.stringify({ count }),
    });
}

export function updateConfig(params) {
    return requestJson("/api/config", {
        method: "POST",
        body: JSON.stringify(params),
    });
}
