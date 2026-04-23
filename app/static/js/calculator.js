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

function initBuilder(recipeId) {
    const base = `/api/recipes/${recipeId}`;

    // Debounced settings update
    let settingsTimer;
    function updateSettings() {
        clearTimeout(settingsTimer);
        settingsTimer = setTimeout(() => {
            apiCall(`${base}/update`, 'POST', {
                style_id: document.getElementById('style-select').value || null,
                yeast_id: document.getElementById('yeast-select').value || null,
                batch_size: parseFloat(document.getElementById('batch-size').value),
                boil_time: parseInt(document.getElementById('boil-time').value),
                efficiency: parseFloat(document.getElementById('efficiency').value),
            });
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

    // Add adjunct
    document.getElementById('add-adjunct-btn').addEventListener('click', async () => {
        const name = prompt('Adjunct name:');
        if (!name) return;
        const amount = prompt('Amount (e.g. "1 oz"):') || '';
        const addTime = prompt('When to add (e.g. "boil 15 min", "secondary 5 days"):') || '';
        const data = await apiCall(`${base}/adjunct`, 'POST', { name, amount, add_time: addTime });
        rebuildAdjuncts(data.adjuncts, base);
    });

    // Wire up existing rows
    wireUpFermentables(base);
    wireUpHops(base);
    wireUpAdjuncts(base);

    // Initial stats load
    apiCall(`${base}/calculate`, 'GET');
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
            <td>${a.name}</td>
            <td>${a.amount}</td>
            <td>${a.add_time}</td>
            <td><button class="btn btn-sm btn-outline-danger adj-delete">&times;</button></td>
        </tr>
    `).join('');
    wireUpAdjuncts(base);
}
