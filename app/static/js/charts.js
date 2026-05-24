let loadChart = null;
let trafficChart = null;
let nodesChart = null;


export function initializeCharts() {
    const canvas = document.getElementById("loadChart");

    if (!canvas || !window.Chart) {
        return;
    }

    loadChart = new Chart(canvas, {
        type: "line",
        data: {
            labels: ["Inicio"],
            datasets: [
                {
                    label: "Carga promedio",
                    data: [0],
                    borderColor: "#2364aa",
                    backgroundColor: "rgba(35, 100, 170, 0.14)",
                    borderWidth: 3,
                    pointRadius: 3,
                    tension: 0.35,
                    fill: true,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false,
                },
            },
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    ticks: {
                        callback: (value) => `${value}%`,
                    },
                },
            },
        },
    });

    const trafficCanvas = document.getElementById("trafficChart");

    if (!trafficCanvas) {
        return;
    }

    trafficChart = new Chart(trafficCanvas, {
        type: "bar",
        data: {
            labels: ["Inicio"],
            datasets: [
                {
                    label: "Solicitudes activas",
                    data: [0],
                    backgroundColor: "rgba(35, 100, 170, 0.78)",
                    borderRadius: 5,
                },
                {
                    label: "Capacidad usada",
                    data: [0],
                    backgroundColor: "rgba(31, 143, 95, 0.72)",
                    borderRadius: 5,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        boxWidth: 12,
                        usePointStyle: true,
                    },
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                },
            },
        },
    });

    const nodesCanvas = document.getElementById("nodesChart");

    if (!nodesCanvas) {
        return;
    }

    nodesChart = new Chart(nodesCanvas, {
        type: "line",
        data: {
            labels: ["Inicio"],
            datasets: [
                {
                    label: "Nodos activos",
                    data: [0],
                    borderColor: "#7c5c2e",
                    backgroundColor: "rgba(124, 92, 46, 0.12)",
                    borderWidth: 3,
                    pointRadius: 3,
                    tension: 0.28,
                    fill: true,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false,
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0,
                    },
                },
            },
        },
    });
}


export function updateCharts(charts) {
    if (!charts) {
        return;
    }

    if (loadChart) {
        loadChart.data.labels = charts.labels.length ? charts.labels : ["Inicio"];
        loadChart.data.datasets[0].data = charts.average_load.length
            ? charts.average_load
            : [0];
        loadChart.update();
    }

    if (trafficChart) {
        trafficChart.data.labels = charts.labels.length ? charts.labels : ["Inicio"];
        trafficChart.data.datasets[0].data = charts.active_requests.length
            ? charts.active_requests
            : [0];
        trafficChart.data.datasets[1].data = charts.used_capacity.length
            ? charts.used_capacity
            : [0];
        trafficChart.update();
    }

    if (nodesChart) {
        nodesChart.data.labels = charts.labels.length ? charts.labels : ["Inicio"];
        nodesChart.data.datasets[0].data = charts.active_nodes.length
            ? charts.active_nodes
            : [0];
        nodesChart.update();
    }
}
