import { getStatus } from "./api.js";
import { initializeCharts } from "./charts.js";
import { renderDashboard } from "./dashboard.js";
import { bindNodeControls, bindTrafficControls } from "./simulator.js";
import { setConnectionStatus } from "./ui.js";
import { bindControlPanel } from "./simulator.js";  // ← agrega al bloque de imports

async function refreshDashboard() {
    try {
        const state = await getStatus();
        renderDashboard(state);
        setConnectionStatus(true);
    } catch (error) {
        console.error(error);
        setConnectionStatus(false);
    }
}


window.addEventListener("DOMContentLoaded", async () => {
    initializeCharts();
    bindNodeControls(refreshDashboard);
    bindTrafficControls(refreshDashboard);
    bindControlPanel(refreshDashboard);
    await refreshDashboard();
    window.setInterval(refreshDashboard, 1500);
});
