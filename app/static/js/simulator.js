import {
    activateNode,
    assignRequest,
    createNode,
    deactivateNode,
    deleteNode,
    generateUsers,
    recoverNode,
    releaseRequest,
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
