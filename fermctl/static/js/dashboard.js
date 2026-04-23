// FermCtl Dashboard — real-time temperature monitoring

let chart = null;
let activeRunId = null;
let pollInterval = null;

// Initialize Chart.js temperature chart
function initChart() {
    const ctx = document.getElementById('temp-chart').getContext('2d');
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Actual',
                    data: [],
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: true,
                    tension: 0.3,
                },
                {
                    label: 'Target',
                    data: [],
                    borderColor: '#dc3545',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    fill: false,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { intersect: false, mode: 'index' },
            scales: {
                x: {
                    display: true,
                    title: { display: true, text: 'Time' },
                    ticks: { maxTicksLimit: 12 },
                },
                y: {
                    display: true,
                    title: { display: true, text: 'Temperature (°F)' },
                    suggestedMin: 58,
                    suggestedMax: 78,
                },
            },
            plugins: {
                legend: { position: 'top' },
            },
        },
    });
}

// Poll status every 15 seconds
function startPolling() {
    updateStatus();
    pollInterval = setInterval(updateStatus, 15000);
}

async function updateStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();

        // Update stat cards
        document.getElementById('current-temp').textContent =
            data.current_temp !== null ? data.current_temp.toFixed(1) : '--';
        document.getElementById('target-temp').textContent =
            data.target_temp !== null ? data.target_temp.toFixed(1) : '--';
        document.getElementById('elapsed').textContent =
            data.elapsed_hours > 0 ? data.elapsed_hours.toFixed(1) : '--';

        // Relay indicators
        setIndicator('heat-indicator', data.heat_on);
        setIndicator('cool-indicator', data.cool_on);

        // Status badge
        const badge = document.getElementById('status-badge');
        if (data.active) {
            badge.textContent = `Run #${data.run_id} active`;
            badge.className = 'badge bg-success';
        } else {
            badge.textContent = 'Idle';
            badge.className = 'text-muted small';
        }

        // Override status
        const overrideStatus = document.getElementById('override-status');
        if (data.override_temp !== null) {
            overrideStatus.textContent = `Override active: ${data.override_temp}°F`;
            overrideStatus.className = 'small text-warning mt-2';
        } else {
            overrideStatus.textContent = 'Following profile';
            overrideStatus.className = 'small text-muted mt-2';
        }

        // Button states
        document.getElementById('start-btn').disabled = data.active;
        document.getElementById('stop-btn').disabled = !data.active;

        activeRunId = data.run_id;

        // Update chart with latest readings
        if (data.active && data.run_id) {
            await updateChart(data.run_id);
        }
    } catch (e) {
        document.getElementById('status-badge').textContent = 'Connection error';
        document.getElementById('status-badge').className = 'badge bg-danger';
    }

    // Update run history
    loadRunHistory();
}

function setIndicator(elemId, on) {
    const el = document.getElementById(elemId);
    el.className = 'indicator ' + (on ? 'on' : 'off');
}

async function updateChart(runId) {
    try {
        const res = await fetch(`/api/readings?run_id=${runId}`);
        const readings = await res.json();

        if (!readings.length) return;

        // Downsample if too many points
        const maxPoints = 500;
        let data = readings;
        if (readings.length > maxPoints) {
            const step = Math.ceil(readings.length / maxPoints);
            data = readings.filter((_, i) => i % step === 0);
        }

        chart.data.labels = data.map(r => {
            const d = new Date(r.timestamp);
            return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        });
        chart.data.datasets[0].data = data.map(r => r.temp_f);
        chart.data.datasets[1].data = data.map(r => r.target_f);
        chart.update('none');
    } catch (e) {
        console.error('Failed to load readings:', e);
    }
}

function loadReadings(range) {
    // For now just reload all — range filtering can use `since` param
    if (activeRunId) updateChart(activeRunId);
}

async function startRun() {
    const name = document.getElementById('run-name').value || 'Manual run';
    const temp = parseFloat(document.getElementById('run-temp').value) || 66;

    const profile = [{ hours: 0, temp_f: temp }];

    await fetch('/api/runs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recipe_name: name, profile }),
    });

    updateStatus();
}

async function stopRun() {
    if (!activeRunId) return;
    if (!confirm('Stop the active fermentation run?')) return;

    await fetch(`/api/runs/${activeRunId}/stop`, { method: 'POST' });
    updateStatus();
}

async function setOverride() {
    const temp = parseFloat(document.getElementById('override-temp').value);
    if (isNaN(temp)) return alert('Enter a temperature');

    await fetch('/api/override', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ temp_f: temp }),
    });
    updateStatus();
}

async function clearOverride() {
    await fetch('/api/override', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ temp_f: null }),
    });
    updateStatus();
}

async function loadRunHistory() {
    try {
        const res = await fetch('/api/runs');
        const runs = await res.json();
        const el = document.getElementById('run-history');

        if (!runs.length) {
            el.innerHTML = '<div class="list-group-item text-muted small">No runs yet</div>';
            return;
        }

        el.innerHTML = runs.slice(0, 5).map(r => {
            const started = new Date(r.started_at).toLocaleDateString();
            const status = r.active ? '<span class="badge bg-success">Active</span>' : '<span class="badge bg-secondary">Done</span>';
            return `<div class="list-group-item d-flex justify-content-between align-items-center py-2">
                <div>
                    <div class="small fw-bold">${r.recipe_name || 'Run #' + r.id}</div>
                    <div class="small text-muted">${started}</div>
                </div>
                ${status}
            </div>`;
        }).join('');
    } catch (e) {
        // Ignore
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    startPolling();
});
