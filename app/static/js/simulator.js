import {
    activateNode,
    assignRequest,
    createNode,
    deactivateNode,
    deleteNode,
    generateUsers,
    recoverNode,
    releaseRequest,
    resetSimulation,   // ← nuevo
    togglePause,       // ← nuevo
    removeUsers,       // ← nuevo
    updateConfig,      // ← nuevo
} from "./api.js";


export function bindNodeControls(refreshDashboard) {
    const createButton = document.getElementById("createNodeButton");
    const nodesContainer = document.getElementById("nodesContainer");

    createButton?.addEventListener("click", async () => {
        await createNode();
        await refreshDashboard();
    });

    nodesContainer?.addEventListener("click", async (event) => {
        const button = event.target.closest("button[data-action]");

        if (!button) {
            return;
        }

        await runNodeAction(button.dataset.action, button.dataset.nodeId, refreshDashboard);
    });
}


export function bindTrafficControls(refreshDashboard) {
    const controls = document.getElementById("trafficControls");

    controls?.addEventListener("click", async (event) => {
        const button = event.target.closest("button[data-users]");

        if (!button) {
            return;
        }

        setTrafficButtonsDisabled(controls, true);

        try {
            await generateUsers(Number(button.dataset.users));
        } finally {
            setTrafficButtonsDisabled(controls, false);
            await refreshDashboard();
        }
    });
}


async function runNodeAction(action, nodeId, refreshDashboard) {
    const operations = {
        "assign-request": () => assignRequest(nodeId),
        "release-request": () => releaseRequest(nodeId),
        "activate-node": () => activateNode(nodeId),
        "deactivate-node": () => deactivateNode(nodeId),
        "recover-node": () => recoverNode(nodeId),
        "delete-node": () => deleteNode(nodeId),
    };

    if (!operations[action]) {
        return;
    }

    try {
        await operations[action]();
    } catch (error) {
        console.error(error);
    } finally {
        await refreshDashboard();
    }
}


function setTrafficButtonsDisabled(container, isDisabled) {
    container.querySelectorAll("button[data-users]").forEach((control) => {
        control.disabled = isDisabled;
    });
}

export function bindControlPanel(refreshDashboard) {
    // Reiniciar
    document.getElementById("resetButton")?.addEventListener("click", async () => {
        if (!confirm("¿Reiniciar la simulación? Se perderán todos los datos actuales.")) return;
        await resetSimulation();
        await refreshDashboard();
    });

    // Pausar / reanudar
    document.getElementById("pauseButton")?.addEventListener("click", async () => {
        await togglePause();
        await refreshDashboard();
    });

    // Eliminar usuarios
    document.getElementById("removeUsersButton")?.addEventListener("click", async () => {
        const input = document.getElementById("removeUsersCount");
        const count = parseInt(input?.value || "1", 10);
        if (isNaN(count) || count < 1) return;
        await removeUsers(count);
        await refreshDashboard();
    });

    // Actualizar configuración
    document.getElementById("applyConfigButton")?.addEventListener("click", async () => {
        const get = (id) => {
            const el = document.getElementById(id);
            return el ? el.value : null;
        };
        const params = {};
        const up = get("cfgScaleUp");
        const down = get("cfgScaleDown");
        const min = get("cfgMinNodes");
        const max = get("cfgMaxNodes");
        const strategy = get("cfgStrategy");
        if (up) params.scale_up_threshold = parseInt(up);
        if (down) params.scale_down_threshold = parseInt(down);
        if (min) params.min_nodes = parseInt(min);
        if (max) params.max_nodes = parseInt(max);
        if (strategy) params.strategy = strategy;
        await updateConfig(params);
        await refreshDashboard();
    });
}