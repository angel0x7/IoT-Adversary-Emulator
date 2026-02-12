function updateSecurityStatus(data) {
    if (!data) return;

    let logs = data.logs || [];
    let severity = data.severity || "OK";

    // Score
    let score = 100;
    const maxDelta = Math.max(data.delta_temperature || 0, data.delta_humidity || 0, data.delta_pressure || 0);
    score -= maxDelta * 5;
    if (score < 0) score = 0;
    document.getElementById("securityScore").innerText = score.toFixed(0) + "%";

    // Status box
    const statusBox = document.getElementById("globalStatus");
    statusBox.className = "status"; // reset classes
    if (severity === "CRITICAL") {
        statusBox.classList.add("critical");
        statusBox.innerText = "CRITICAL";
    } else if (severity === "WARNING") {
        statusBox.classList.add("warning");
        statusBox.innerText = "WARNING";
    } else {
        statusBox.classList.add("ok");
        statusBox.innerText = "OK";
    }

    // Logs
    const logsContainer = document.getElementById("logs");
    logsContainer.innerHTML = "";
    logs.forEach(log => {
        const p = document.createElement("p");
        p.innerText = log;
        logsContainer.appendChild(p);
    });
}

async function fetchData() {
    const response = await fetch('/api/data'); // Assure-toi que ton Flask fournit /api/data
    const data = await response.json();

    // Mettre à jour les graphes
    updateCharts(data);

    // Mettre à jour l'état de sécurité
    updateSecurityStatus(data.logs);
}

// Lancer fetchData toutes les 5 secondes
setInterval(fetchData, 5000);
