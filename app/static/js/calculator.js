// SRM to approximate RGB color
function srmToColor(srm) {
    srm = Math.max(0, Math.min(srm, 40));
    const r = Math.round(Math.min(255, Math.max(0, 255 * Math.pow(0.975, srm))));
    const g = Math.round(Math.min(255, Math.max(0, 255 * Math.pow(0.88, srm))));
    const b = Math.round(Math.min(255, Math.max(0, 255 * Math.pow(0.7, srm))));
    return `rgb(${r}, ${g}, ${b})`;
}

function updateStats(data) {
    document.getElementById('stat-og').textContent = data.og.toFixed(3);
    document.getElementById('stat-fg').textContent = data.fg.toFixed(3);
    document.getElementById('stat-abv').textContent = data.abv.toFixed(1) + '%';
    document.getElementById('stat-ibu').textContent = Math.round(data.ibu);
    document.getElementById('stat-srm').textContent = Math.round(data.srm);

    const swatch = document.getElementById('srm-swatch');
    if (swatch) swatch.style.backgroundColor = srmToColor(data.srm);

    // Update style range indicators
    if (data.style) {
        const s = data.style;
        setRange('stat-og-range', data.og, s.og_low, s.og_high, v => v.toFixed(3));
        setRange('stat-fg-range', data.fg, s.fg_low, s.fg_high, v => v.toFixed(3));
        setRange('stat-abv-range', data.abv, s.abv_low, s.abv_high, v => v.toFixed(1));
        setRange('stat-ibu-range', data.ibu, s.ibu_low, s.ibu_high, v => Math.round(v));
    }
}

function setRange(elemId, value, low, high, fmt) {
    const el = document.getElementById(elemId);
    if (!el) return;
    const inRange = value >= low && value <= high;
    el.textContent = `${fmt(low)}-${fmt(high)}`;
    el.className = 'small ' + (inRange ? 'text-success' : 'text-danger');
}

async function apiCall(url, method, body) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(url, opts);
    const data = await res.json();
    updateStats(data);
    return data;
}

// Raw fetch that doesn't call updateStats (for profile endpoints)
async function apiRaw(url, method, body) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(url, opts);
    return await res.json();
}

// ============================
// Fermentation Profile Editor
// ============================

let profileChart = null;
let profileWaypoints = [];
let profileRecipeId = null;

function initProfileEditor(recipeId) {
    profileRecipeId = recipeId;

    // Initialize chart
    const ctx = document.getElementById('profile-chart').getContext('2d');
    profileChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Target Temp',
                data: [],
                borderColor: '#dc3545',
                backgroundColor: 'rgba(220, 53, 69, 0.1)',
                borderWidth: 2,
                pointRadius: 6,
                pointBackgroundColor: '#dc3545',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointHoverRadius: 8,
                fill: true,
                tension: 0,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: { display: true, text: 'Day' },
                },
                y: {
                    title: { display: true, text: 'Temperature (°F)' },
                    suggestedMin: 58,
                    suggestedMax: 78,
                },
            },
            plugins: {
                legend: { display: false },
            },
        },
    });

    // Load existing profile
    loadProfile();

    // Add waypoint button
    document.getElementById('add-waypoint-btn').addEventListener('click', () => {
        // Default: add a waypoint 24h after the last one
        const lastHour = profileWaypoints.length > 0
            ? profileWaypoints[profileWaypoints.length - 1].hours + 24
            : 0;
        const lastTemp = profileWaypoints.length > 0
            ? profileWaypoints[profileWaypoints.length - 1].temp_f
            : 66;
        profileWaypoints.push({ hours: lastHour, temp_f: lastTemp });
        saveAndRenderProfile();
    });

    // Preset buttons
    document.querySelectorAll('.profile-preset').forEach(btn => {
        btn.addEventListener('click', () => {
            profileWaypoints = JSON.parse(btn.dataset.profile);
            saveAndRenderProfile();
        });
    });
}

async function loadProfile() {
    const data = await apiRaw(`/api/recipes/${profileRecipeId}/ferm_profile`, 'GET');
    profileWaypoints = data.profile || [];
    if (profileWaypoints.length === 0) {
        profileWaypoints = [{ hours: 0, temp_f: 66 }];
    }
    renderProfile();
}

function renderProfile() {
    // Sort waypoints
    profileWaypoints.sort((a, b) => a.hours - b.hours);

    // Update chart
    // Generate interpolated points for a smooth line, plus mark actual waypoints
    const labels = [];
    const data = [];

    if (profileWaypoints.length > 0) {
        const maxHours = Math.max(profileWaypoints[profileWaypoints.length - 1].hours + 24, 48);
        for (let h = 0; h <= maxHours; h += 2) {
            labels.push(`Day ${(h / 24).toFixed(1)}`);
            data.push(interpolateTemp(h));
        }
    }

    profileChart.data.labels = labels;
    profileChart.data.datasets[0].data = data;

    // Mark actual waypoint positions with larger points
    const pointRadii = labels.map((_, i) => {
        const hour = i * 2;
        return profileWaypoints.some(w => Math.abs(w.hours - hour) < 1) ? 6 : 0;
    });
    profileChart.data.datasets[0].pointRadius = pointRadii;
    profileChart.update('none');

    // Update waypoint table
    const tbody = document.getElementById('waypoints-list');
    tbody.innerHTML = profileWaypoints.map((w, i) => {
        const day = (w.hours / 24).toFixed(1);
        let desc = '';
        if (i === 0) desc = 'Start';
        else if (i > 0 && w.temp_f === profileWaypoints[i - 1].temp_f) desc = 'Hold';
        else if (i > 0 && w.temp_f > profileWaypoints[i - 1].temp_f) desc = 'Ramp up';
        else if (i > 0 && w.temp_f < profileWaypoints[i - 1].temp_f) desc = 'Ramp down';

        return `<tr>
            <td class="text-muted small">${day}</td>
            <td><input type="number" class="form-control form-control-sm wp-hours" data-index="${i}" value="${w.hours}" step="6" min="0"></td>
            <td><input type="number" class="form-control form-control-sm wp-temp" data-index="${i}" value="${w.temp_f}" step="0.5" min="50" max="85"></td>
            <td class="text-muted small">${desc}</td>
            <td>${profileWaypoints.length > 1 ? `<button class="btn btn-sm btn-outline-danger wp-delete" data-index="${i}">&times;</button>` : ''}</td>
        </tr>`;
    }).join('');

    // Wire up waypoint inputs
    wireUpWaypoints();
}

function wireUpWaypoints() {
    let timer;

    document.querySelectorAll('.wp-hours').forEach(input => {
        input.addEventListener('input', () => {
            clearTimeout(timer);
            timer = setTimeout(() => {
                const idx = parseInt(input.dataset.index);
                profileWaypoints[idx].hours = parseFloat(input.value) || 0;
                saveAndRenderProfile();
            }, 500);
        });
    });

    document.querySelectorAll('.wp-temp').forEach(input => {
        input.addEventListener('input', () => {
            clearTimeout(timer);
            timer = setTimeout(() => {
                const idx = parseInt(input.dataset.index);
                profileWaypoints[idx].temp_f = parseFloat(input.value) || 66;
                saveAndRenderProfile();
            }, 500);
        });
    });

    document.querySelectorAll('.wp-delete').forEach(btn => {
        btn.addEventListener('click', () => {
            const idx = parseInt(btn.dataset.index);
            profileWaypoints.splice(idx, 1);
            saveAndRenderProfile();
        });
    });
}

async function saveAndRenderProfile() {
    profileWaypoints.sort((a, b) => a.hours - b.hours);
    await apiRaw(`/api/recipes/${profileRecipeId}/ferm_profile`, 'PUT', {
        profile: profileWaypoints,
    });
    renderProfile();
}

function interpolateTemp(hours) {
    if (!profileWaypoints.length) return 66;

    if (hours <= profileWaypoints[0].hours) return profileWaypoints[0].temp_f;
    if (hours >= profileWaypoints[profileWaypoints.length - 1].hours)
        return profileWaypoints[profileWaypoints.length - 1].temp_f;

    for (let i = 0; i < profileWaypoints.length - 1; i++) {
        const w1 = profileWaypoints[i];
        const w2 = profileWaypoints[i + 1];
        if (hours >= w1.hours && hours <= w2.hours) {
            const span = w2.hours - w1.hours;
            if (span === 0) return w2.temp_f;
            const frac = (hours - w1.hours) / span;
            return w1.temp_f + frac * (w2.temp_f - w1.temp_f);
        }
    }
    return profileWaypoints[profileWaypoints.length - 1].temp_f;
}


// ============================
// Builder Init
// ============================

function initBuilder(recipeId) {
    const base = `/api/recipes/${recipeId}`;

    // Debounced settings update
    let settingsTimer;
    function updateSettings() {
        clearTimeout(settingsTimer);
        settingsTimer = setTimeout(async () => {
            const data = await apiCall(`${base}/update`, 'POST', {
                style_id: document.getElementById('style-select').value || null,
                yeast_id: document.getElementById('yeast-select').value || null,
                batch_size: parseFloat(document.getElementById('batch-size').value),
                boil_time: parseInt(document.getElementById('boil-time').value),
                efficiency: parseFloat(document.getElementById('efficiency').value),
            });
            // Keep scale current label in sync
            document.getElementById('scale-current').textContent =
                parseFloat(document.getElementById('batch-size').value) + ' gal';
        }, 400);
    }

    document.getElementById('style-select').addEventListener('change', updateSettings);
    document.getElementById('yeast-select').addEventListener('change', updateSettings);
    document.getElementById('batch-size').addEventListener('input', updateSettings);
    document.getElementById('boil-time').addEventListener('input', updateSettings);
    document.getElementById('efficiency').addEventListener('input', updateSettings);

    // Add fermentable
    document.getElementById('add-fermentable-btn').addEventListener('click', async () => {
        const select = document.getElementById('add-fermentable-select');
        const data = await apiCall(`${base}/fermentable`, 'POST', {
            fermentable_id: select.value,
            amount_oz: 16,
            use: 'boil',
        });
        rebuildFermentables(data.fermentables, base);
    });

    // Add hop
    document.getElementById('add-hop-btn').addEventListener('click', async () => {
        const select = document.getElementById('add-hop-select');
        const data = await apiCall(`${base}/hop`, 'POST', {
            hop_id: select.value,
            amount_oz: 0.5,
            boil_time_min: 60,
            use: 'boil',
        });
        rebuildHops(data.hops, base);
    });

    // Adjunct form toggle + submit
    const adjForm = document.getElementById('adjunct-form');
    const adjStageSel = document.getElementById('adj-stage');
    const adjTimeLabel = document.getElementById('adj-time-label');
    const adjTimeInput = document.getElementById('adj-time');

    function updateAdjTimeLabel() {
        const stage = adjStageSel.value;
        if (stage === 'boil') adjTimeLabel.textContent = 'Min remaining';
        else if (stage === 'mash' || stage === 'flameout') adjTimeLabel.textContent = 'Minutes';
        else adjTimeLabel.textContent = 'Day';
    }
    adjStageSel.addEventListener('change', updateAdjTimeLabel);

    function resetAdjForm() {
        document.getElementById('adj-name').value = '';
        document.getElementById('adj-amount').value = '';
        adjStageSel.value = 'boil';
        adjTimeInput.value = '';
        updateAdjTimeLabel();
    }

    document.getElementById('add-adjunct-btn').addEventListener('click', () => {
        adjForm.style.display = adjForm.style.display === 'none' ? 'block' : 'none';
        if (adjForm.style.display === 'block') document.getElementById('adj-name').focus();
    });

    document.getElementById('adj-cancel').addEventListener('click', () => {
        adjForm.style.display = 'none';
        resetAdjForm();
    });

    document.getElementById('adj-save').addEventListener('click', async () => {
        const name = document.getElementById('adj-name').value.trim();
        if (!name) return;
        const payload = {
            name,
            amount: document.getElementById('adj-amount').value.trim(),
            stage: adjStageSel.value,
            time_value: adjTimeInput.value === '' ? null : parseInt(adjTimeInput.value),
        };
        const data = await apiCall(`${base}/adjunct`, 'POST', payload);
        rebuildAdjuncts(data.adjuncts, base);
        resetAdjForm();
        adjForm.style.display = 'none';
    });

    // Batch scaling
    document.getElementById('scale-btn').addEventListener('click', async () => {
        const newSize = parseFloat(document.getElementById('scale-target').value);
        const currentSize = parseFloat(document.getElementById('batch-size').value);
        if (!newSize || newSize <= 0) return;
        if (newSize === currentSize) return;

        if (!confirm(`Scale recipe from ${currentSize} gal to ${newSize} gal? All ingredient amounts will be adjusted.`)) return;

        const data = await apiCall(`${base}/scale`, 'POST', { new_batch_size: newSize });
        rebuildFermentables(data.fermentables, base);
        rebuildHops(data.hops, base);
        // Update batch size input and scale label
        document.getElementById('batch-size').value = newSize;
        document.getElementById('scale-current').textContent = newSize + ' gal';
        document.getElementById('scale-target').value = newSize;
    });

    // Scale presets
    document.querySelectorAll('.scale-preset').forEach(btn => {
        btn.addEventListener('click', () => {
            document.getElementById('scale-target').value = btn.dataset.size;
        });
    });

    // Wire up existing rows
    wireUpFermentables(base);
    wireUpHops(base);
    wireUpAdjuncts(base);

    // Initial stats load
    apiCall(`${base}/calculate`, 'GET');

    // Initialize profile editor
    initProfileEditor(recipeId);
}

function wireUpFermentables(base) {
    document.querySelectorAll('#fermentables-list tr').forEach(row => {
        const id = row.dataset.id;
        let timer;
        const amountInput = row.querySelector('.ferm-amount');
        const useSelect = row.querySelector('.ferm-use');
        const deleteBtn = row.querySelector('.ferm-delete');

        if (amountInput) {
            amountInput.addEventListener('input', () => {
                clearTimeout(timer);
                timer = setTimeout(() => {
                    apiCall(`${base}/fermentable/${id}`, 'PUT', {
                        amount_oz: parseFloat(amountInput.value),
                        use: useSelect.value,
                    });
                }, 400);
            });
        }
        if (useSelect) {
            useSelect.addEventListener('change', () => {
                apiCall(`${base}/fermentable/${id}`, 'PUT', {
                    amount_oz: parseFloat(amountInput.value),
                    use: useSelect.value,
                });
            });
        }
        if (deleteBtn) {
            deleteBtn.addEventListener('click', async () => {
                const data = await apiCall(`${base}/fermentable/${id}`, 'DELETE');
                rebuildFermentables(data.fermentables, base);
            });
        }
    });
}

function wireUpHops(base) {
    document.querySelectorAll('#hops-list tr').forEach(row => {
        const id = row.dataset.id;
        let timer;
        const amountInput = row.querySelector('.hop-amount');
        const timeInput = row.querySelector('.hop-time');
        const useSelect = row.querySelector('.hop-use');
        const deleteBtn = row.querySelector('.hop-delete');

        function updateHop() {
            clearTimeout(timer);
            timer = setTimeout(() => {
                apiCall(`${base}/hop/${id}`, 'PUT', {
                    amount_oz: parseFloat(amountInput.value),
                    boil_time_min: parseInt(timeInput.value),
                    use: useSelect.value,
                });
            }, 400);
        }

        if (amountInput) amountInput.addEventListener('input', updateHop);
        if (timeInput) timeInput.addEventListener('input', updateHop);
        if (useSelect) useSelect.addEventListener('change', updateHop);
        if (deleteBtn) {
            deleteBtn.addEventListener('click', async () => {
                const data = await apiCall(`${base}/hop/${id}`, 'DELETE');
                rebuildHops(data.hops, base);
            });
        }
    });
}

function wireUpAdjuncts(base) {
    document.querySelectorAll('#adjuncts-list tr').forEach(row => {
        const id = row.dataset.id;
        const deleteBtn = row.querySelector('.adj-delete');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', async () => {
                const data = await apiCall(`${base}/adjunct/${id}`, 'DELETE');
                rebuildAdjuncts(data.adjuncts, base);
            });
        }
    });
}

function rebuildFermentables(fermentables, base) {
    const tbody = document.getElementById('fermentables-list');
    tbody.innerHTML = fermentables.map(f => `
        <tr data-id="${f.id}">
            <td>${f.name}</td>
            <td><input type="number" class="form-control form-control-sm ferm-amount" value="${f.amount_oz}" step="0.5" min="0.1"></td>
            <td>
                <select class="form-select form-select-sm ferm-use">
                    <option value="boil" ${f.use === 'boil' ? 'selected' : ''}>Boil</option>
                    <option value="steep" ${f.use === 'steep' ? 'selected' : ''}>Steep</option>
                    <option value="late" ${f.use === 'late' ? 'selected' : ''}>Late</option>
                </select>
            </td>
            <td><button class="btn btn-sm btn-outline-danger ferm-delete">&times;</button></td>
        </tr>
    `).join('');
    wireUpFermentables(base);
}

function rebuildHops(hops, base) {
    const tbody = document.getElementById('hops-list');
    tbody.innerHTML = hops.map(h => `
        <tr data-id="${h.id}">
            <td>${h.name}</td>
            <td><input type="number" class="form-control form-control-sm hop-amount" value="${h.amount_oz}" step="0.25" min="0.1"></td>
            <td><input type="number" class="form-control form-control-sm hop-time" value="${h.boil_time_min}" step="5" min="0" max="120"></td>
            <td>
                <select class="form-select form-select-sm hop-use">
                    <option value="boil" ${h.use === 'boil' ? 'selected' : ''}>Boil</option>
                    <option value="flameout" ${h.use === 'flameout' ? 'selected' : ''}>Flameout</option>
                    <option value="dryhop" ${h.use === 'dryhop' ? 'selected' : ''}>Dry Hop</option>
                </select>
            </td>
            <td><button class="btn btn-sm btn-outline-danger hop-delete">&times;</button></td>
        </tr>
    `).join('');
    wireUpHops(base);
}

function rebuildAdjuncts(adjuncts, base) {
    const tbody = document.getElementById('adjuncts-list');
    tbody.innerHTML = adjuncts.map(a => `
        <tr data-id="${a.id}">
            <td>${escapeHtml(a.name || '')}</td>
            <td>${escapeHtml(a.amount || '')}</td>
            <td>${escapeHtml(a.display_when || '')}</td>
            <td><button class="btn btn-sm btn-outline-danger adj-delete">&times;</button></td>
        </tr>
    `).join('');
    wireUpAdjuncts(base);
}

function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
