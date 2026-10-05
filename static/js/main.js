/**
 * Crime Data Analytics & Visualization System
 * Robust Dynamic Cascading: State -> District -> Area
 */

/**
 * Resolve an input argument which may be a DOM element or a string value/ID
 */
function resolveElement(arg, fallbackId, form, nameSelector) {
    if (arg && arg.nodeType === 1) {
        return arg;
    }
    if (typeof arg === 'string' && arg.trim() !== '') {
        const byId = document.getElementById(arg);
        if (byId) return byId;
    }
    if (form && nameSelector) {
        const byName = form.querySelector(nameSelector);
        if (byName) return byName;
    }
    if (fallbackId) {
        const byFallback = document.getElementById(fallbackId);
        if (byFallback) return byFallback;
    }
    if (nameSelector) {
        return document.querySelector(nameSelector);
    }
    return null;
}

/**
 * Triggered when State selection changes.
 * Cascades: refreshes District dropdown, resets & refreshes Area dropdown.
 */
function onStateChange(triggerArg, districtArg, areaArg) {
    let stateVal = '';
    let form = null;

    if (triggerArg && triggerArg.nodeType === 1) {
        stateVal = triggerArg.value || '';
        form = triggerArg.form || triggerArg.closest('form');
    } else if (typeof triggerArg === 'string') {
        stateVal = triggerArg;
    }

    const stateSelect = form ? (form.querySelector('select[name="state"]') || document.getElementById('filterState')) : document.getElementById('filterState');
    if (!stateVal && stateSelect) {
        stateVal = stateSelect.value || '';
    }
    stateVal = (stateVal || '').trim();

    const districtSelect = resolveElement(districtArg, 'filterDistrict', form, 'select[name="district"]');
    const areaSelect = resolveElement(areaArg, 'filterArea', form, 'select[name="area"]');

    if (!districtSelect) return;

    // 1. Immediately reset District to Loading
    districtSelect.innerHTML = '<option value="">Loading districts...</option>';
    districtSelect.disabled = true;

    // 2. Immediately reset Area to Loading or Default
    if (areaSelect) {
        areaSelect.innerHTML = '<option value="">Loading areas...</option>';
        areaSelect.disabled = true;
    }

    const stateParam = (stateVal && stateVal.toLowerCase() !== 'all') ? encodeURIComponent(stateVal) : 'all';

    // 3. Fetch districts for selected state
    fetch(`/api/districts?state=${stateParam}`)
        .then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.json();
        })
        .then(districts => {
            districtSelect.innerHTML = '<option value="">All Districts</option>';
            if (Array.isArray(districts) && districts.length > 0) {
                districts.forEach(dist => {
                    const opt = document.createElement('option');
                    opt.value = dist;
                    opt.textContent = dist;
                    districtSelect.appendChild(opt);
                });
            } else {
                const opt = document.createElement('option');
                opt.value = '';
                opt.textContent = 'No districts available';
                districtSelect.appendChild(opt);
            }
            districtSelect.disabled = false;
        })
        .catch(err => {
            console.error("Error fetching districts:", err);
            districtSelect.innerHTML = '<option value="">All Districts</option>';
            districtSelect.disabled = false;
        });

    // 4. Fetch areas for selected state (with district = all)
    if (areaSelect) {
        fetch(`/api/areas?state=${stateParam}&district=all`)
            .then(res => {
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                return res.json();
            })
            .then(areas => {
                areaSelect.innerHTML = '<option value="">All Areas</option>';
                if (Array.isArray(areas) && areas.length > 0) {
                    areas.forEach(ar => {
                        const opt = document.createElement('option');
                        opt.value = ar;
                        opt.textContent = ar;
                        areaSelect.appendChild(opt);
                    });
                } else {
                    const opt = document.createElement('option');
                    opt.value = '';
                    opt.textContent = 'No areas available';
                    areaSelect.appendChild(opt);
                }
                areaSelect.disabled = false;
            })
            .catch(err => {
                console.error("Error fetching areas:", err);
                areaSelect.innerHTML = '<option value="">All Areas</option>';
                areaSelect.disabled = false;
            });
    }
}

/**
 * Triggered when District selection changes.
 * Cascades: refreshes Area dropdown for selected State + District.
 */
function onDistrictChange(triggerArg, areaArg) {
    let districtVal = '';
    let form = null;

    if (triggerArg && triggerArg.nodeType === 1) {
        districtVal = triggerArg.value || '';
        form = triggerArg.form || triggerArg.closest('form');
    } else if (typeof triggerArg === 'string') {
        districtVal = triggerArg;
    }

    const districtSelect = form ? (form.querySelector('select[name="district"]') || document.getElementById('filterDistrict')) : document.getElementById('filterDistrict');
    if (!districtVal && districtSelect) {
        districtVal = districtSelect.value || '';
    }
    districtVal = (districtVal || '').trim();

    // Determine current state value from form or document
    const stateSelect = form ? (form.querySelector('select[name="state"]') || document.getElementById('filterState')) : document.getElementById('filterState');
    let stateVal = stateSelect ? (stateSelect.value || '').trim() : '';
    if (stateVal.toLowerCase() === 'all') stateVal = '';

    const areaSelect = resolveElement(areaArg, 'filterArea', form, 'select[name="area"]');
    if (!areaSelect) return;

    // Reset Area to Loading
    areaSelect.innerHTML = '<option value="">Loading areas...</option>';
    areaSelect.disabled = true;

    const stateParam = stateVal ? encodeURIComponent(stateVal) : 'all';
    const districtParam = (districtVal && districtVal.toLowerCase() !== 'all') ? encodeURIComponent(districtVal) : 'all';

    // Fetch areas for State + District
    fetch(`/api/areas?state=${stateParam}&district=${districtParam}`)
        .then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.json();
        })
        .then(areas => {
            areaSelect.innerHTML = '<option value="">All Areas</option>';
            if (Array.isArray(areas) && areas.length > 0) {
                areas.forEach(ar => {
                    const opt = document.createElement('option');
                    opt.value = ar;
                    opt.textContent = ar;
                    areaSelect.appendChild(opt);
                });
            } else {
                const opt = document.createElement('option');
                opt.value = '';
                opt.textContent = 'No areas available';
                areaSelect.appendChild(opt);
            }
            areaSelect.disabled = false;
        })
        .catch(err => {
            console.error("Error fetching areas for district:", err);
            areaSelect.innerHTML = '<option value="">All Areas</option>';
            areaSelect.disabled = false;
        });
}

/**
 * Form Submission Validation & Cleanup
 * Clears stale or mismatched district/area values before submitting GET filter forms.
 */
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('form').forEach(function(form) {
        const stateSel = form.querySelector('select[name="state"]');
        const districtSel = form.querySelector('select[name="district"]');
        const areaSel = form.querySelector('select[name="area"]');

        // Only attach to filter forms having geographic selects
        if (stateSel && districtSel) {
            // Auto attach event listeners if inline onchange wasn't set
            if (!stateSel.getAttribute('onchange')) {
                stateSel.addEventListener('change', function() { onStateChange(this); });
            }
            if (!districtSel.getAttribute('onchange')) {
                districtSel.addEventListener('change', function() { onDistrictChange(this); });
            }

            form.addEventListener('submit', function() {
                // If user selected "All Districts" or an invalid option, don't send stale district
                if (districtSel && districtSel.options && districtSel.value) {
                    const validDistricts = Array.from(districtSel.options).map(o => o.value);
                    if (!validDistricts.includes(districtSel.value)) {
                        districtSel.value = '';
                    }
                }
                // If user selected an invalid area not in current options, clear it
                if (areaSel && areaSel.options && areaSel.value) {
                    const validAreas = Array.from(areaSel.options).map(o => o.value);
                    if (!validAreas.includes(areaSel.value)) {
                        areaSel.value = '';
                    }
                }
            });
        }
    });
});
