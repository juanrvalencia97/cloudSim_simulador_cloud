export function setText(id, value) {
    const element = document.getElementById(id);

    if (element) {
        element.textContent = value;
    }
}


export function setConnectionStatus(isOnline) {
    const element = document.getElementById("connectionStatus");

    if (!element) {
        return;
    }

    element.textContent = isOnline ? "API conectada" : "Sin conexion";
    element.classList.toggle("status-ok", isOnline);
    element.classList.toggle("status-error", !isOnline);
    element.classList.remove("status-idle");
}


export function statusLabel(status) {
    const labels = {
        STANDBY: "En espera",
        ACTIVE: "Activo",
        INACTIVE: "Inactivo",
        FAILED: "Caido",
        OVERLOADED: "Alta carga",
    };

    return labels[status] || status;
}


export function formatPercent(value) {
    return `${Math.round(Number(value) || 0)}%`;
}


export function formatUptime(seconds) {
    const value = Number(seconds) || 0;
    const minutes = Math.floor(value / 60);
    const remainingSeconds = value % 60;

    if (minutes <= 0) {
        return `${remainingSeconds}s`;
    }

    return `${minutes}m ${remainingSeconds}s`;
}


export function statusClass(status) {
    const classes = {
        ACTIVE: "status-ok",
        OVERLOADED: "status-warning",
        INACTIVE: "status-idle",
        FAILED: "status-error",
    };

    return classes[status] || "status-idle";
}
