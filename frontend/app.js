// BytyBargain - Interactive Frontend Application with Live Progress Bar & Status

let currentResults = [];
let currentStats = null;
let currentCriteria = null;
let activeView = 'cards'; // 'cards' | 'table'
let progressInterval = null;
let timerInterval = null;
let searchStartTime = 0;

// Format CZK currency
function formatCZK(amount) {
  if (amount === undefined || amount === null || isNaN(amount)) return '0 Kč';
  return Math.round(amount).toLocaleString('cs-CZ') + ' Kč';
}

function formatNumber(num) {
  if (num === undefined || num === null || isNaN(num)) return '0';
  return Math.round(num).toLocaleString('cs-CZ');
}

// Portal colors & badges
const PORTAL_META = {
  sreality: { name: 'Sreality.cz', color: 'bg-red-100 text-red-700 border-red-200', icon: 'fa-house-chimney' },
  bezrealitky: { name: 'Bezrealitky.cz', color: 'bg-emerald-100 text-emerald-800 border-emerald-200', icon: 'fa-handshake' },
  remax: { name: 'RE/MAX', color: 'bg-blue-100 text-blue-800 border-blue-200', icon: 'fa-building' },
  bazos: { name: 'Bazoš Reality', color: 'bg-amber-100 text-amber-800 border-amber-200', icon: 'fa-tags' },
};

document.addEventListener('DOMContentLoaded', () => {
  initUI();
  // Auto-search default city (Praha) on initial load
  performSearch();
});

function initUI() {
  const form = document.getElementById('searchForm');
  const minDiscountSlider = document.getElementById('minDiscount');
  const discountLabel = document.getElementById('discountLabel');
  const selectAllDispBtn = document.getElementById('selectAllDisp');
  const clearDispBtn = document.getElementById('clearDisp');
  const viewCardsBtn = document.getElementById('viewCardsBtn');
  const viewTableBtn = document.getElementById('viewTableBtn');
  const exportCsvBtn = document.getElementById('exportCsvBtn');
  const sortBySelect = document.getElementById('sortBy');
  const showAllFlatsBtn = document.getElementById('showAllFlatsBtn');
  const resetDiscountBtn = document.getElementById('resetDiscountBtn');

  // Slider label live update
  minDiscountSlider.addEventListener('input', (e) => {
    discountLabel.textContent = `${e.target.value}%`;
  });

  // Quick Location Chips
  document.querySelectorAll('.loc-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.getElementById('locationInput').value = chip.getAttribute('data-loc');
      performSearch();
    });
  });

  // Select all / clear dispositions
  selectAllDispBtn.addEventListener('click', () => {
    document.querySelectorAll('input[name="disposition"]').forEach(cb => cb.checked = true);
  });

  clearDispBtn.addEventListener('click', () => {
    document.querySelectorAll('input[name="disposition"]').forEach(cb => cb.checked = false);
  });

  // View toggle
  viewCardsBtn.addEventListener('click', () => setView('cards'));
  viewTableBtn.addEventListener('click', () => setView('table'));

  // Sort change
  sortBySelect.addEventListener('change', () => {
    if (currentResults.length > 0) {
      sortAndRenderResults();
    }
  });

  // Export CSV
  exportCsvBtn.addEventListener('click', () => {
    if (!currentCriteria) return;
    exportCSV();
  });

  // Empty state action buttons
  showAllFlatsBtn.addEventListener('click', () => {
    document.getElementById('onlyBelowAverage').checked = false;
    document.getElementById('minDiscount').value = '0';
    document.getElementById('discountLabel').textContent = '0%';
    performSearch();
  });

  resetDiscountBtn.addEventListener('click', () => {
    document.getElementById('minDiscount').value = '0';
    document.getElementById('discountLabel').textContent = '0%';
    performSearch();
  });

  // Form submit
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    performSearch();
  });
}

function getSearchCriteria() {
  const location = document.getElementById('locationInput').value.trim() || 'Praha';
  
  const dispositions = Array.from(
    document.querySelectorAll('input[name="disposition"]:checked')
  ).map(cb => cb.value);

  const minPrice = document.getElementById('minPrice').value ? parseInt(document.getElementById('minPrice').value) : null;
  const maxPrice = document.getElementById('maxPrice').value ? parseInt(document.getElementById('maxPrice').value) : null;
  const minArea = document.getElementById('minArea').value ? parseInt(document.getElementById('minArea').value) : null;
  const maxArea = document.getElementById('maxArea').value ? parseInt(document.getElementById('maxArea').value) : null;

  const portals = Array.from(
    document.querySelectorAll('input[name="portal"]:checked')
  ).map(cb => cb.value);

  const onlyBelowAverage = document.getElementById('onlyBelowAverage').checked;
  const minDiscountPercent = parseFloat(document.getElementById('minDiscount').value) || 0.0;
  const customBenchmark = document.getElementById('customBenchmark').value ? parseFloat(document.getElementById('customBenchmark').value) : null;
  const sortBy = document.getElementById('sortBy').value;

  return {
    location,
    dispositions: dispositions.length > 0 ? dispositions : ['1+kk', '2+kk', '3+kk'],
    min_price: minPrice,
    max_price: maxPrice,
    min_area: minArea,
    max_area: maxArea,
    portals: portals.length > 0 ? portals : ['sreality', 'bezrealitky', 'remax', 'bazos'],
    only_below_average: onlyBelowAverage,
    min_discount_percent: minDiscountPercent,
    custom_benchmark_czk_m2: customBenchmark,
    sort_by: sortBy,
    limit: 150
  };
}

function startLoadingProgress(locationName) {
  const topBarContainer = document.getElementById('topProgressBarContainer');
  const topBar = document.getElementById('topProgressBar');
  const innerBar = document.getElementById('innerProgressBar');
  const liveProgressCard = document.getElementById('liveProgressCard');
  const searchBtn = document.getElementById('searchBtn');
  const searchBtnIcon = document.getElementById('searchBtnIcon');
  const searchBtnText = document.getElementById('searchBtnText');
  const timerSeconds = document.getElementById('timerSeconds');

  // Reset steps
  ['stepSreality', 'stepBezrealitky', 'stepRemax', 'stepBazos'].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.className = 'flex items-center gap-2 p-2 rounded-lg bg-slate-50 text-slate-700 border border-slate-100';
    }
  });

  // UI state: loading
  searchBtn.disabled = true;
  searchBtnIcon.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
  searchBtnText.textContent = `Vyhledávám v lokalitě ${locationName}...`;

  topBarContainer.classList.remove('hidden');
  liveProgressCard.classList.remove('hidden');

  let currentPercent = 10;
  topBar.style.width = '10%';
  innerBar.style.width = '10%';

  searchStartTime = Date.now();
  if (timerInterval) clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    const elapsed = ((Date.now() - searchStartTime) / 1000).toFixed(1);
    timerSeconds.textContent = `${elapsed}s`;
  }, 100);

  if (progressInterval) clearInterval(progressInterval);
  progressInterval = setInterval(() => {
    if (currentPercent < 88) {
      currentPercent += Math.random() * 12;
      topBar.style.width = `${Math.min(88, currentPercent)}%`;
      innerBar.style.width = `${Math.min(88, currentPercent)}%`;
    }

    const elapsedMs = Date.now() - searchStartTime;
    if (elapsedMs > 800) markStepDone('stepSreality', 'stepSrealityIcon');
    if (elapsedMs > 1400) markStepDone('stepBezrealitky', 'stepBezrealitkyIcon');
    if (elapsedMs > 2000) markStepDone('stepRemax', 'stepRemaxIcon');
    if (elapsedMs > 2600) markStepDone('stepBazos', 'stepBazosIcon');
  }, 350);
}

function markStepDone(stepId, iconId) {
  const el = document.getElementById(stepId);
  const icon = document.getElementById(iconId);
  if (el && icon) {
    el.className = 'flex items-center gap-2 p-2 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200';
    icon.className = 'fa-solid fa-check text-emerald-600';
  }
}

function stopLoadingProgress() {
  const topBarContainer = document.getElementById('topProgressBarContainer');
  const topBar = document.getElementById('topProgressBar');
  const innerBar = document.getElementById('innerProgressBar');
  const liveProgressCard = document.getElementById('liveProgressCard');
  const searchBtn = document.getElementById('searchBtn');
  const searchBtnIcon = document.getElementById('searchBtnIcon');
  const searchBtnText = document.getElementById('searchBtnText');

  if (progressInterval) clearInterval(progressInterval);
  if (timerInterval) clearInterval(timerInterval);

  topBar.style.width = '100%';
  innerBar.style.width = '100%';

  ['stepSreality', 'stepBezrealitky', 'stepRemax', 'stepBazos'].forEach(id => {
    markStepDone(id, `${id}Icon`);
  });

  setTimeout(() => {
    topBarContainer.classList.add('hidden');
    liveProgressCard.classList.add('hidden');
    topBar.style.width = '0%';
    innerBar.style.width = '0%';
  }, 450);

  searchBtn.disabled = false;
  searchBtnIcon.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i>';
  searchBtnText.textContent = 'Vyhledat výhodné nabídky';
}

async function performSearch() {
  const criteria = getSearchCriteria();
  currentCriteria = criteria;

  const emptyState = document.getElementById('emptyState');
  const resultsGrid = document.getElementById('resultsGrid');
  const resultsTableContainer = document.getElementById('resultsTableContainer');
  const statsSection = document.getElementById('statsSection');

  startLoadingProgress(criteria.location);
  emptyState.classList.add('hidden');
  resultsGrid.innerHTML = '';
  document.getElementById('resultsTableBody').innerHTML = '';

  try {
    const response = await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(criteria)
    });

    if (!response.ok) {
      throw new Error(`Server vrátil chybu HTTP ${response.status}`);
    }

    const data = await response.json();
    currentResults = data.listings || [];
    currentStats = data.stats || null;

    renderStats(currentStats);
    sortAndRenderResults();

    statsSection.classList.remove('hidden');

    // Scroll smoothly to results if user initiated search
    if (Date.now() - searchStartTime > 600) {
      statsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  } catch (error) {
    console.error('Search error:', error);
    emptyState.classList.remove('hidden');
    document.getElementById('emptyTitle').textContent = 'Chyba při vyhledávání nabídek';
    document.getElementById('emptyDescription').textContent = `Nepodařilo se načíst data ze serveru (${error.message}). Zkuste to prosím za okamžik znovu.`;
  } finally {
    stopLoadingProgress();
  }
}

function renderStats(stats) {
  if (!stats) return;

  document.getElementById('statLocalityName').textContent = stats.locality_name;
  document.getElementById('statAvgM2').textContent = formatNumber(stats.average_price_per_m2);
  document.getElementById('statMedianM2').textContent = formatNumber(stats.median_price_per_m2);
  document.getElementById('statTotalScanned').textContent = formatNumber(stats.total_scanned);
  document.getElementById('statBargainsCount').textContent = formatNumber(stats.total_bargains);
  document.getElementById('statMaxSavings').textContent = formatNumber(stats.max_savings_czk);

  const sourceBadge = document.getElementById('benchmarkSourceBadge');
  if (sourceBadge) {
    sourceBadge.textContent = stats.benchmark_source;
  }
}

function sortAndRenderResults() {
  const sortBy = document.getElementById('sortBy').value;
  const emptyState = document.getElementById('emptyState');
  const resultsGrid = document.getElementById('resultsGrid');
  const resultsTableContainer = document.getElementById('resultsTableContainer');

  if (!currentResults || currentResults.length === 0) {
    emptyState.classList.remove('hidden');
    resultsGrid.classList.add('hidden');
    resultsTableContainer.classList.add('hidden');

    if (currentStats && currentStats.total_scanned > 0) {
      document.getElementById('emptyTitle').textContent = `Nalezeno ${currentStats.total_scanned} inzerátů, ale žádný pod průměrem`;
      document.getElementById('emptyDescription').textContent = 
        `V lokalitě ${currentStats.locality_name} bylo zanalyzováno ${currentStats.total_scanned} bytů (tržní průměr ${formatNumber(currentStats.average_price_per_m2)} Kč/m²), ale žádný nesplnil požadovanou slevu.`;
    } else {
      document.getElementById('emptyTitle').textContent = 'Nebyly nalezeny žádné inzeráty';
      document.getElementById('emptyDescription').textContent = 'Zkuste zadat větší město, upravit cenové limity nebo povolit více dispozic.';
    }
    return;
  }

  emptyState.classList.add('hidden');

  // Client-side sort
  currentResults.sort((a, b) => {
    if (sortBy === 'discount_desc') return b.discount_percentage - a.discount_percentage;
    if (sortBy === 'savings_desc') return b.difference_czk - a.difference_czk;
    if (sortBy === 'price_m2_asc') return a.price_per_m2 - b.price_per_m2;
    if (sortBy === 'price_asc') return a.price_czk - b.price_czk;
    if (sortBy === 'price_desc') return b.price_czk - a.price_czk;
    return 0;
  });

  renderCardsView(currentResults);
  renderTableView(currentResults);

  setView(activeView);
}

function renderCardsView(listings) {
  const container = document.getElementById('resultsGrid');
  container.innerHTML = '';

  listings.forEach(flat => {
    const portal = PORTAL_META[flat.portal] || { name: flat.portal, color: 'bg-slate-100 text-slate-700', icon: 'fa-globe' };
    
    // Tier badges
    let tierBadgeHtml = '';
    if (flat.discount_percentage >= 20.0) {
      tierBadgeHtml = `<span class="px-2.5 py-1 rounded-lg text-xs font-black bg-red-600 text-white shadow-xs badge-super-bargain flex items-center gap-1">
        <i class="fa-solid fa-fire"></i> -${flat.discount_percentage}% SLEVA
      </span>`;
    } else if (flat.discount_percentage >= 10.0) {
      tierBadgeHtml = `<span class="px-2.5 py-1 rounded-lg text-xs font-bold bg-amber-500 text-white shadow-xs flex items-center gap-1">
        <i class="fa-solid fa-bolt"></i> -${flat.discount_percentage}% VÝHODNÉ
      </span>`;
    } else if (flat.discount_percentage > 0.0) {
      tierBadgeHtml = `<span class="px-2.5 py-1 rounded-lg text-xs font-bold bg-emerald-600 text-white shadow-xs flex items-center gap-1">
        <i class="fa-solid fa-tag"></i> -${flat.discount_percentage}% POD PRŮMĚREM
      </span>`;
    } else {
      tierBadgeHtml = `<span class="px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-600 text-white shadow-xs">
        +${Math.abs(flat.discount_percentage)}% nad průměrem
      </span>`;
    }

    const fallbackImg = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="250" viewBox="0 0 400 250" fill="%23f1f5f9"><rect width="400" height="250"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" font-size="16" fill="%2394a3b8">Fotografie nedostupná</text></svg>`;
    const imgSrc = flat.image_url || fallbackImg;

    const savingsText = flat.difference_czk > 0
      ? `Ušetříte ${formatCZK(flat.difference_czk)}`
      : `Příplatek ${formatCZK(Math.abs(flat.difference_czk))}`;

    const card = document.createElement('div');
    card.className = 'flat-card bg-white rounded-2xl border border-slate-200/80 shadow-2xs overflow-hidden flex flex-col justify-between';

    card.innerHTML = `
      <div>
        <!-- Image & Badges Header -->
        <div class="relative h-48 sm:h-52 bg-slate-100 overflow-hidden">
          <img
            src="${imgSrc}"
            alt="${escapeHtml(flat.title)}"
            class="flat-img w-full h-full object-cover"
            loading="lazy"
            onerror="this.src='${fallbackImg}'"
          />
          <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/20"></div>

          <!-- Top Overlay Badges -->
          <div class="absolute top-3 left-3 right-3 flex items-center justify-between">
            ${tierBadgeHtml}
            <span class="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-black/60 backdrop-blur-xs text-white border border-white/20">
              ${flat.disposition} • ${flat.area_m2} m²
            </span>
          </div>

          <!-- Bottom Overlay: Location -->
          <div class="absolute bottom-2.5 left-3 right-3 text-white">
            <p class="text-xs font-medium truncate flex items-center gap-1.5 drop-shadow-xs">
              <i class="fa-solid fa-location-dot text-indigo-400"></i> ${escapeHtml(flat.locality || flat.city)}
            </p>
          </div>
        </div>

        <!-- Card Body -->
        <div class="p-4 sm:p-5 space-y-4">
          
          <!-- Title -->
          <h3 class="font-bold text-sm sm:text-base text-slate-900 line-clamp-2 leading-snug hover:text-indigo-600 transition" title="${escapeHtml(flat.title)}">
            ${escapeHtml(flat.title)}
          </h3>

          <!-- Pricing Metrics Box -->
          <div class="bg-slate-50 p-3 rounded-xl border border-slate-200/70 space-y-2 text-xs">
            <div class="flex items-center justify-between">
              <span class="text-slate-600 font-medium">Nabídková cena:</span>
              <span class="text-base font-extrabold text-slate-900">${formatCZK(flat.price_czk)}</span>
            </div>

            <div class="flex items-center justify-between text-slate-600">
              <span>Cena za m²:</span>
              <span class="font-bold text-slate-800">${formatNumber(flat.price_per_m2)} Kč/m²</span>
            </div>

            <div class="flex items-center justify-between text-slate-600 pt-1.5 border-t border-slate-200/60">
              <span title="Očekávaná tržní hodnota dle průměru lokality">Očekávaná hodnota:</span>
              <span class="font-medium text-slate-600 line-through">${formatCZK(flat.expected_price_czk)}</span>
            </div>

            <div class="flex items-center justify-between font-semibold ${flat.difference_czk > 0 ? 'text-emerald-700' : 'text-slate-600'}">
              <span>${flat.difference_czk > 0 ? 'Úspora oproti průměru:' : 'Rozdíl oproti průměru:'}</span>
              <span class="font-extrabold">${savingsText}</span>
            </div>
          </div>

        </div>
      </div>

      <!-- Card Footer -->
      <div class="px-4 pb-4 sm:px-5 sm:pb-5 pt-0 flex items-center justify-between gap-2 border-t border-slate-100">
        <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-semibold border ${portal.color}">
          <i class="fa-solid ${portal.icon}"></i> ${portal.name}
        </span>

        <a
          href="${flat.url}"
          target="_blank"
          rel="noopener noreferrer"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-600 text-indigo-700 hover:text-white font-bold text-xs transition active:scale-95 shadow-2xs"
        >
          <span>Zobrazit inzerát</span>
          <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
        </a>
      </div>
    `;

    container.appendChild(card);
  });
}

function renderTableView(listings) {
  const tbody = document.getElementById('resultsTableBody');
  tbody.innerHTML = '';

  listings.forEach((flat) => {
    const portal = PORTAL_META[flat.portal] || { name: flat.portal, color: 'bg-slate-100 text-slate-700' };
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-slate-50/80 transition';

    tr.innerHTML = `
      <td class="px-4 py-3">
        <div class="flex items-center gap-3">
          <img
            src="${flat.image_url || ''}"
            alt=""
            class="w-10 h-10 rounded-lg object-cover bg-slate-100 shrink-0"
            onerror="this.style.display='none'"
          />
          <div>
            <a href="${flat.url}" target="_blank" class="font-bold text-slate-900 hover:text-indigo-600 line-clamp-1">
              ${escapeHtml(flat.title)}
            </a>
            <span class="text-[11px] text-slate-600 truncate block">${escapeHtml(flat.locality || flat.city)}</span>
          </div>
        </div>
      </td>
      <td class="px-4 py-3 font-semibold text-slate-800">${flat.disposition}</td>
      <td class="px-4 py-3 font-semibold text-slate-800">${flat.area_m2} m²</td>
      <td class="px-4 py-3 font-extrabold text-slate-900">${formatCZK(flat.price_czk)}</td>
      <td class="px-4 py-3 font-bold text-slate-700">${formatNumber(flat.price_per_m2)} Kč</td>
      <td class="px-4 py-3 text-slate-600 line-through">${formatCZK(flat.expected_price_czk)}</td>
      <td class="px-4 py-3 font-black ${flat.difference_czk > 0 ? 'text-emerald-600' : 'text-slate-600'}">
        ${flat.difference_czk > 0 ? '+' : ''}${formatCZK(flat.difference_czk)} (${flat.discount_percentage}%)
      </td>
      <td class="px-4 py-3">
        <span class="inline-block px-2 py-0.5 rounded text-[10px] font-semibold ${portal.color}">
          ${portal.name}
        </span>
      </td>
      <td class="px-4 py-3 text-right">
        <a
          href="${flat.url}"
          target="_blank"
          class="px-2.5 py-1 rounded bg-indigo-50 hover:bg-indigo-600 text-indigo-700 hover:text-white font-semibold text-xs transition inline-flex items-center gap-1"
        >
          <span>Přejít</span>
          <i class="fa-solid fa-arrow-up-right-from-square text-[9px]"></i>
        </a>
      </td>
    `;

    tbody.appendChild(tr);
  });
}

function setView(view) {
  activeView = view;
  const cardsBtn = document.getElementById('viewCardsBtn');
  const tableBtn = document.getElementById('viewTableBtn');
  const resultsGrid = document.getElementById('resultsGrid');
  const resultsTableContainer = document.getElementById('resultsTableContainer');

  if (view === 'cards') {
    cardsBtn.className = 'px-3 py-1 rounded-md bg-white text-slate-900 font-semibold shadow-2xs';
    tableBtn.className = 'px-3 py-1 rounded-md text-slate-600 font-medium hover:text-slate-900';
    resultsGrid.classList.remove('hidden');
    resultsTableContainer.classList.add('hidden');
  } else {
    tableBtn.className = 'px-3 py-1 rounded-md bg-white text-slate-900 font-semibold shadow-2xs';
    cardsBtn.className = 'px-3 py-1 rounded-md text-slate-600 font-medium hover:text-slate-900';
    resultsTableContainer.classList.remove('hidden');
    resultsGrid.classList.add('hidden');
  }
}

async function exportCSV() {
  if (!currentCriteria) return;
  
  try {
    const response = await fetch('/api/export/csv', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(currentCriteria)
    });

    if (!response.ok) throw new Error('Export failed');

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vyhodne_byty_${currentCriteria.location || 'cr'}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  } catch (e) {
    alert('Chyba při exportu CSV: ' + e.message);
  }
}

function escapeHtml(text) {
  if (!text) return '';
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
