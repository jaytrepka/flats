// BytyBargain - Interactive Multi-Region Real Estate Aggregator & Bargain Finder

let selectedLocations = new Set(['Praha']);
let currentResults = [];
let currentStats = null;
let currentCriteria = null;
let activeView = 'cards'; // 'cards' | 'table' | 'map'
let progressInterval = null;
let timerInterval = null;
let searchStartTime = 0;

let selectionMap = null;
let resultsMap = null;
let krajeGeoJsonLayer = null;
let cityMarkersMap = {};
let resultsMarkersLayer = null;

// 14 Czech Regions (Kraje) Dataset
const CZECH_KRAJE = [
  { name: "Hlavní město Praha", short: "Praha", avg: 158000 },
  { name: "Středočeský kraj", short: "Středočeský", avg: 82000 },
  { name: "Jihočeský kraj", short: "Jihočeský", avg: 81000 },
  { name: "Plzeňský kraj", short: "Plzeňský", avg: 84000 },
  { name: "Karlovarský kraj", short: "Karlovarský", avg: 62000 },
  { name: "Ústecký kraj", short: "Ústecký", avg: 42000 },
  { name: "Liberecký kraj", short: "Liberecký", avg: 74000 },
  { name: "Královéhradecký kraj", short: "Královéhradecký", avg: 86000 },
  { name: "Pardubický kraj", short: "Pardubický", avg: 79000 },
  { name: "Kraj Vysočina", short: "Vysočina", avg: 72000 },
  { name: "Jihomoravský kraj", short: "Jihomoravský", avg: 128000 },
  { name: "Olomoucký kraj", short: "Olomoucký", avg: 82000 },
  { name: "Zlínský kraj", short: "Zlínský", avg: 76000 },
  { name: "Moravskoslezský kraj", short: "Moravskoslezský", avg: 52000 },
];

// Major Czech cities with coordinates & benchmark prices (Kč/m²)
const CZECH_CITIES = [
  { name: "Praha", lat: 50.0755, lng: 14.4378, avg: 158000, region: "Praha" },
  { name: "Brno", lat: 49.1951, lng: 16.6068, avg: 128000, region: "Jihomoravský" },
  { name: "Ostrava", lat: 49.8209, lng: 18.2625, avg: 52000, region: "Moravskoslezský" },
  { name: "Plzeň", lat: 49.7384, lng: 13.3736, avg: 84000, region: "Plzeňský" },
  { name: "Liberec", lat: 50.7663, lng: 15.0543, avg: 74000, region: "Liberecký" },
  { name: "Olomouc", lat: 49.5938, lng: 17.2509, avg: 82000, region: "Olomoucký" },
  { name: "České Budějovice", lat: 48.9745, lng: 14.4743, avg: 81000, region: "Jihočeský" },
  { name: "Hradec Králové", lat: 50.2104, lng: 15.8252, avg: 86000, region: "Královéhradecký" },
  { name: "Pardubice", lat: 50.0343, lng: 15.7812, avg: 79000, region: "Pardubický" },
  { name: "Ústí nad Labem", lat: 50.6607, lng: 14.0323, avg: 42000, region: "Ústecký" },
  { name: "Zlín", lat: 49.2243, lng: 17.6627, avg: 76000, region: "Zlínský" },
  { name: "Jihlava", lat: 49.3961, lng: 15.5912, avg: 72000, region: "Vysočina" },
  { name: "Karlovy Vary", lat: 50.2319, lng: 12.8719, avg: 62000, region: "Karlovarský" },
  { name: "Kladno", lat: 50.1473, lng: 14.1028, avg: 78000, region: "Středočeský" },
  { name: "Mladá Boleslav", lat: 50.4114, lng: 14.9032, avg: 81000, region: "Středočeský" },
  { name: "Kralupy nad Vltavou", lat: 50.2411, lng: 14.3046, avg: 74000, region: "Středočeský" },
  { name: "Teplice", lat: 50.6404, lng: 13.8245, avg: 41000, region: "Ústecký" },
  { name: "Most", lat: 50.5030, lng: 13.6362, avg: 34000, region: "Ústecký" },
  { name: "Děčín", lat: 50.7822, lng: 14.2148, avg: 39000, region: "Ústecký" },
  { name: "Chomutov", lat: 50.4605, lng: 13.4178, avg: 37000, region: "Ústecký" },
  { name: "Jablonec nad Nisou", lat: 50.7243, lng: 15.1711, avg: 63000, region: "Liberecký" },
  { name: "Česká Lípa", lat: 50.6855, lng: 14.5376, avg: 52000, region: "Liberecký" },
  { name: "Trutnov", lat: 50.5610, lng: 15.9128, avg: 57000, region: "Královéhradecký" },
  { name: "Kolín", lat: 50.0281, lng: 15.2006, avg: 74000, region: "Středočeský" },
  { name: "Příbram", lat: 49.6899, lng: 14.0104, avg: 68000, region: "Středočeský" },
  { name: "Beroun", lat: 49.9638, lng: 14.0720, avg: 86000, region: "Středočeský" },
  { name: "Kutná Hora", lat: 49.9500, lng: 15.2667, avg: 69000, region: "Středočeský" },
  { name: "Mělník", lat: 50.3508, lng: 14.4744, avg: 71000, region: "Středočeský" },
  { name: "Tábor", lat: 49.4144, lng: 14.6578, avg: 68000, region: "Jihočeský" },
  { name: "Písek", lat: 49.3088, lng: 14.1475, avg: 69000, region: "Jihočeský" },
  { name: "Cheb", lat: 50.0796, lng: 12.3739, avg: 52000, region: "Karlovarský" },
  { name: "Třebíč", lat: 49.2149, lng: 15.8817, avg: 62000, region: "Vysočina" },
  { name: "Znojmo", lat: 48.8555, lng: 16.0488, avg: 69000, region: "Jihomoravský" },
  { name: "Břeclav", lat: 48.7590, lng: 16.8820, avg: 72000, region: "Jihomoravský" },
  { name: "Hodonín", lat: 48.8519, lng: 17.1322, avg: 64000, region: "Jihomoravský" },
  { name: "Prostějov", lat: 49.4719, lng: 17.1122, avg: 65000, region: "Olomoucký" },
  { name: "Přerov", lat: 49.4551, lng: 17.4509, avg: 54000, region: "Olomoucký" },
  { name: "Šumperk", lat: 49.9653, lng: 16.9706, avg: 56000, region: "Olomoucký" },
  { name: "Kroměříž", lat: 49.2979, lng: 17.3931, avg: 64000, region: "Zlínský" },
  { name: "Uherské Hradiště", lat: 49.0698, lng: 17.4597, avg: 72000, region: "Zlínský" },
  { name: "Vsetín", lat: 49.3387, lng: 17.9961, avg: 58000, region: "Zlínský" },
  { name: "Opava", lat: 49.9387, lng: 17.9026, avg: 51000, region: "Moravskoslezský" },
  { name: "Frýdek-Místek", lat: 49.6853, lng: 18.3491, avg: 54000, region: "Moravskoslezský" },
  { name: "Karviná", lat: 49.8540, lng: 18.5417, avg: 36000, region: "Moravskoslezský" },
  { name: "Havířov", lat: 49.7797, lng: 18.4369, avg: 38000, region: "Moravskoslezský" },
  { name: "Třinec", lat: 49.6778, lng: 18.6708, avg: 52000, region: "Moravskoslezský" },
];

function formatCZK(amount) {
  if (amount === undefined || amount === null || isNaN(amount)) return '0 Kč';
  return Math.round(amount).toLocaleString('cs-CZ') + ' Kč';
}

function formatNumber(num) {
  if (num === undefined || num === null || isNaN(num)) return '0';
  return Math.round(num).toLocaleString('cs-CZ');
}

const PORTAL_META = {
  sreality: { name: 'Sreality.cz', color: 'bg-red-100 text-red-700 border-red-200', icon: 'fa-house-chimney' },
  bezrealitky: { name: 'Bezrealitky.cz', color: 'bg-emerald-100 text-emerald-800 border-emerald-200', icon: 'fa-handshake' },
  remax: { name: 'RE/MAX', color: 'bg-blue-100 text-blue-800 border-blue-200', icon: 'fa-building' },
  bazos: { name: 'Bazoš Reality', color: 'bg-amber-100 text-amber-800 border-amber-200', icon: 'fa-tags' },
};

// -------------------------------------------------------------
// Multi-Location State & Tag Chips Management
// -------------------------------------------------------------

function toggleLocation(locName) {
  if (!locName || !locName.trim()) return;
  const name = locName.trim();

  // Find canonical name if matches region or city
  let canonicalName = name;
  const matchKraj = CZECH_KRAJE.find(k => k.name.toLowerCase() === name.toLowerCase() || k.short.toLowerCase() === name.toLowerCase());
  if (matchKraj) canonicalName = matchKraj.name;

  if (selectedLocations.has(canonicalName)) {
    selectedLocations.delete(canonicalName);
  } else {
    selectedLocations.add(canonicalName);
  }

  renderSelectedLocations();
  updateMapVisuals();
  updateKrajePills();
}

function addLocation(locName) {
  if (!locName || !locName.trim()) return;
  const name = locName.trim();
  selectedLocations.add(name);
  renderSelectedLocations();
  updateMapVisuals();
  updateKrajePills();
}

function removeLocation(locName) {
  selectedLocations.delete(locName);
  renderSelectedLocations();
  updateMapVisuals();
  updateKrajePills();
}

function clearAllLocations() {
  selectedLocations.clear();
  renderSelectedLocations();
  updateMapVisuals();
  updateKrajePills();
}

function renderSelectedLocations() {
  const container = document.getElementById('selectedLocationsContainer');
  if (!container) return;

  container.innerHTML = '';

  if (selectedLocations.size === 0) {
    container.innerHTML = `
      <span class="text-xs text-slate-500 italic py-1">
        <i class="fa-solid fa-circle-info mr-1 text-slate-400"></i> Nebyla vybrána žádná lokalita (vyberte na mapě nebo zadejte do pole níže)
      </span>
    `;
    return;
  }

  selectedLocations.forEach(loc => {
    const isRegion = CZECH_KRAJE.some(k => k.name.toLowerCase() === loc.toLowerCase());
    const chip = document.createElement('span');
    chip.className = `inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold shadow-2xs border transition animate-fade-in ${
      isRegion
        ? 'bg-indigo-600 text-white border-indigo-700'
        : 'bg-white text-indigo-950 border-indigo-200'
    }`;

    chip.innerHTML = `
      <i class="fa-solid ${isRegion ? 'fa-map' : 'fa-location-dot'} text-[10px] opacity-80"></i>
      <span>${escapeHtml(loc)}</span>
      <button type="button" class="ml-1 hover:text-red-400 font-black cursor-pointer text-xs" title="Odebrat">✕</button>
    `;

    chip.querySelector('button').addEventListener('click', (e) => {
      e.stopPropagation();
      removeLocation(loc);
    });

    container.appendChild(chip);
  });
}

function updateKrajePills() {
  const container = document.getElementById('krajePillsContainer');
  if (!container) return;

  container.innerHTML = '';

  CZECH_KRAJE.forEach(kraj => {
    const isSelected = selectedLocations.has(kraj.name) || selectedLocations.has(kraj.short);
    const kczk = Math.round(kraj.avg / 1000);
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = `px-2.5 py-1 rounded-lg text-xs font-semibold border transition cursor-pointer flex items-center gap-1.5 ${
      isSelected
        ? 'bg-indigo-500 text-white border-indigo-300 shadow-xs'
        : 'bg-white/10 hover:bg-white/20 text-slate-200 border-white/10'
    }`;

    btn.innerHTML = `
      <span class="w-1.5 h-1.5 rounded-full ${isSelected ? 'bg-emerald-400' : 'bg-slate-400'}"></span>
      <span>${kraj.short}</span>
      <span class="text-[10px] opacity-75">${kczk}k</span>
    `;

    btn.addEventListener('click', () => {
      toggleLocation(kraj.name);
    });

    container.appendChild(btn);
  });
}

// -------------------------------------------------------------
// Interactive Map (GeoJSON Kraje + Clickable City Markers)
// -------------------------------------------------------------

function initSelectionMap() {
  const mapEl = document.getElementById('selectionMap');
  if (!mapEl || typeof L === 'undefined') return;

  selectionMap = L.map('selectionMap', {
    scrollWheelZoom: true,
    zoomControl: true,
  }).setView([49.8175, 15.4730], 7);

  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    maxZoom: 18,
  }).addTo(selectionMap);

  // Render 14 Czech Kraje GeoJSON layer
  if (window.CZECH_KRAJE_GEOJSON) {
    krajeGeoJsonLayer = L.geoJSON(window.CZECH_KRAJE_GEOJSON, {
      style: getKrajStyle,
      onEachFeature: (feature, layer) => {
        const name = feature.properties.name;
        const avg = formatNumber(feature.properties.avg_price_m2);

        layer.bindTooltip(`<strong>${name}</strong><br/>Průměr: ${avg} Kč/m²`, {
          className: 'region-tooltip',
          sticky: true,
          direction: 'top',
        });

        layer.on({
          mouseover: (e) => {
            const isSel = isRegionSelected(name);
            e.target.setStyle({
              weight: 3,
              color: '#3730a3',
              fillOpacity: isSel ? 0.6 : 0.25,
            });
          },
          mouseout: (e) => {
            krajeGeoJsonLayer.resetStyle(e.target);
            e.target.setStyle(getKrajStyle(feature));
          },
          click: () => {
            toggleLocation(name);
          },
        });
      }
    }).addTo(selectionMap);
  }

  // Add City Badges
  CZECH_CITIES.forEach(city => {
    const kczk = Math.round(city.avg / 1000);
    const isSel = selectedLocations.has(city.name);

    const customHtml = `
      <div class="custom-city-marker ${isSel ? 'is-selected' : ''}" id="cityMarker_${city.name}" title="${city.name} (${formatNumber(city.avg)} Kč/m²)">
        <span>${city.name}</span>
        <span class="price-sub">${kczk}k</span>
      </div>
    `;

    const cityIcon = L.divIcon({
      html: customHtml,
      className: '',
      iconSize: [85, 24],
      iconAnchor: [42, 12]
    });

    const marker = L.marker([city.lat, city.lng], { icon: cityIcon }).addTo(selectionMap);

    marker.on('click', (e) => {
      L.DomEvent.stopPropagation(e);
      toggleLocation(city.name);
    });

    cityMarkersMap[city.name] = marker;
  });

  // Map Click Handler: clicking outside cities/kraje toggles nearest location
  selectionMap.on('click', (e) => {
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;

    let closestCity = CZECH_CITIES[0];
    let minDist = 999999;
    CZECH_CITIES.forEach(c => {
      const d = Math.hypot(c.lat - lat, c.lng - lng);
      if (d < minDist) {
        minDist = d;
        closestCity = c;
      }
    });

    toggleLocation(closestCity.name);
  });

  updateMapVisuals();
}

function isRegionSelected(regionName) {
  if (!regionName) return false;
  return Array.from(selectedLocations).some(loc => 
    loc.toLowerCase() === regionName.toLowerCase() ||
    regionName.toLowerCase().includes(loc.toLowerCase()) ||
    loc.toLowerCase().includes(regionName.toLowerCase())
  );
}

function getKrajStyle(feature) {
  const name = feature?.properties?.name || '';
  const isSelected = isRegionSelected(name);

  if (isSelected) {
    return {
      fillColor: '#4f46e5',
      fillOpacity: 0.45,
      weight: 2.5,
      color: '#312e81',
      dashArray: '',
    };
  }

  return {
    fillColor: '#6366f1',
    fillOpacity: 0.08,
    weight: 1.5,
    color: '#818cf8',
    dashArray: '3',
  };
}

function updateMapVisuals() {
  if (krajeGeoJsonLayer) {
    krajeGeoJsonLayer.eachLayer(layer => {
      if (layer.feature) {
        layer.setStyle(getKrajStyle(layer.feature));
      }
    });
  }

  // Update city markers style
  CZECH_CITIES.forEach(city => {
    const isSel = selectedLocations.has(city.name);
    const kczk = Math.round(city.avg / 1000);
    const marker = cityMarkersMap[city.name];

    if (marker) {
      const newHtml = `
        <div class="custom-city-marker ${isSel ? 'is-selected' : ''}" title="${city.name} (${formatNumber(city.avg)} Kč/m²)">
          ${isSel ? '<i class="fa-solid fa-check text-[10px] text-emerald-300"></i>' : ''}
          <span>${city.name}</span>
          <span class="price-sub">${kczk}k</span>
        </div>
      `;

      const newIcon = L.divIcon({
        html: newHtml,
        className: '',
        iconSize: [85, 24],
        iconAnchor: [42, 12]
      });

      marker.setIcon(newIcon);
    }
  });
}

// -------------------------------------------------------------
// Results Map View
// -------------------------------------------------------------

function initResultsMap() {
  const mapEl = document.getElementById('resultsMap');
  if (!mapEl || typeof L === 'undefined') return;

  if (!resultsMap) {
    resultsMap = L.map('resultsMap').setView([49.8175, 15.4730], 8);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
      maxZoom: 18,
    }).addTo(resultsMap);
    resultsMarkersLayer = L.layerGroup().addTo(resultsMap);
  }

  renderResultsOnMap();
}

function renderResultsOnMap() {
  if (!resultsMap || !resultsMarkersLayer) return;

  resultsMarkersLayer.clearLayers();

  const validEstates = currentResults.filter(f => f.latitude && f.longitude);

  if (validEstates.length === 0) {
    const firstLoc = Array.from(selectedLocations)[0] || 'Praha';
    const matchedCity = CZECH_CITIES.find(c => c.name.toLowerCase() === firstLoc.toLowerCase());
    if (matchedCity) {
      resultsMap.setView([matchedCity.lat, matchedCity.lng], 10);
    }
    return;
  }

  const latLngs = [];

  validEstates.forEach(flat => {
    const lat = flat.latitude;
    const lng = flat.longitude;
    latLngs.push([lat, lng]);

    let bgColor = '#16a34a';
    let iconClass = 'fa-tag';
    if (flat.discount_percentage >= 20.0) {
      bgColor = '#dc2626';
      iconClass = 'fa-fire';
    } else if (flat.discount_percentage >= 10.0) {
      bgColor = '#ea580c';
      iconClass = 'fa-bolt';
    }

    const markerHtml = `
      <div class="custom-estate-marker" style="background-color: ${bgColor}; width: 34px; height: 34px; border: 2px solid white;">
        <i class="fa-solid ${iconClass}"></i>
      </div>
    `;

    const icon = L.divIcon({
      html: markerHtml,
      className: '',
      iconSize: [34, 34],
      iconAnchor: [17, 17],
      popupAnchor: [0, -18]
    });

    const popupHtml = `
      <div class="w-64 overflow-hidden rounded-xl font-sans text-xs">
        ${flat.image_url ? `<img src="${flat.image_url}" class="w-full h-28 object-cover" />` : ''}
        <div class="p-3 space-y-2">
          <div class="flex items-center justify-between">
            <span class="font-bold text-slate-900">${flat.disposition} • ${flat.area_m2} m²</span>
            <span class="font-bold text-white px-2 py-0.5 rounded text-[10px]" style="background-color: ${bgColor}">
              -${flat.discount_percentage}%
            </span>
          </div>
          <h4 class="font-bold text-slate-800 text-xs line-clamp-1">${escapeHtml(flat.title)}</h4>
          <div class="bg-slate-50 p-2 rounded border border-slate-200 text-[11px] space-y-1">
            <div class="flex justify-between">
              <span class="text-slate-600">Cena:</span>
              <strong class="text-slate-900">${formatCZK(flat.price_czk)}</strong>
            </div>
            <div class="flex justify-between text-emerald-700 font-bold">
              <span>Úspora:</span>
              <span>+${formatCZK(flat.difference_czk)}</span>
            </div>
          </div>
          <a href="${flat.url}" target="_blank" class="block text-center py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs transition">
            Zobrazit inzerát ↗
          </a>
        </div>
      </div>
    `;

    const marker = L.marker([lat, lng], { icon }).bindPopup(popupHtml);
    resultsMarkersLayer.addLayer(marker);
  });

  if (latLngs.length > 0) {
    resultsMap.fitBounds(L.latLngBounds(latLngs), { padding: [40, 40], maxZoom: 14 });
  }
}

// -------------------------------------------------------------
// UI Initialization & Event Handlers
// -------------------------------------------------------------

function syncDispositionPill(labelEl) {
  const checkbox = labelEl.querySelector('input[name="disposition"]');
  const box = labelEl.querySelector('.pill-box');
  if (!checkbox || !box) return;

  if (checkbox.checked) {
    box.className = 'pill-box text-center py-2 px-2 rounded-xl border border-indigo-600 bg-indigo-50 text-indigo-700 font-bold text-xs transition shadow-2xs hover:border-indigo-500';
  } else {
    box.className = 'pill-box text-center py-2 px-2 rounded-xl border border-slate-200 bg-slate-50 text-slate-700 font-semibold text-xs transition shadow-2xs hover:border-slate-300';
  }
}

function syncAllDispositionPills() {
  document.querySelectorAll('.disp-pill').forEach(syncDispositionPill);
}

document.addEventListener('DOMContentLoaded', () => {
  initUI();
  initSelectionMap();
  // Auto-search default location (Praha) on initial load
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
  const viewMapBtn = document.getElementById('viewMapBtn');
  const exportCsvBtn = document.getElementById('exportCsvBtn');
  const sortBySelect = document.getElementById('sortBy');
  const showAllFlatsBtn = document.getElementById('showAllFlatsBtn');
  const resetDiscountBtn = document.getElementById('resetDiscountBtn');
  const toggleMapBtn = document.getElementById('toggleMapBtn');
  const locationInput = document.getElementById('locationInput');
  const addLocationBtn = document.getElementById('addLocationBtn');
  const clearAllLocationsBtn = document.getElementById('clearAllLocationsBtn');

  // Multi-location Tags & Kraje Pills
  renderSelectedLocations();
  updateKrajePills();

  // Add Location Input Handler (Enter key or Add button)
  const handleAddLocation = () => {
    if (locationInput && locationInput.value.trim()) {
      const parts = locationInput.value.split(',');
      parts.forEach(p => addLocation(p.trim()));
      locationInput.value = '';
    }
  };

  if (addLocationBtn) addLocationBtn.addEventListener('click', handleAddLocation);
  if (locationInput) {
    locationInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleAddLocation();
      }
    });
  }

  if (clearAllLocationsBtn) {
    clearAllLocationsBtn.addEventListener('click', () => {
      clearAllLocations();
    });
  }

  // Quick City Chips (+ Praha, + Brno, etc.)
  document.querySelectorAll('.loc-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const loc = chip.getAttribute('data-loc');
      addLocation(loc);
    });
  });

  // Slider label live update
  const updateSliderLabel = (val) => {
    if (discountLabel) {
      discountLabel.textContent = `${val}%`;
    }
  };

  if (minDiscountSlider) {
    minDiscountSlider.addEventListener('input', (e) => updateSliderLabel(e.target.value));
    minDiscountSlider.addEventListener('change', (e) => updateSliderLabel(e.target.value));
  }

  // Disposition Pills Click Handling
  document.querySelectorAll('.disp-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      setTimeout(() => syncDispositionPill(pill), 10);
    });
  });

  if (selectAllDispBtn) {
    selectAllDispBtn.addEventListener('click', (e) => {
      e.preventDefault();
      document.querySelectorAll('input[name="disposition"]').forEach(cb => {
        cb.checked = true;
      });
      syncAllDispositionPills();
    });
  }

  if (clearDispBtn) {
    clearDispBtn.addEventListener('click', (e) => {
      e.preventDefault();
      document.querySelectorAll('input[name="disposition"]').forEach(cb => {
        cb.checked = false;
      });
      syncAllDispositionPills();
    });
  }

  // Toggle Map
  if (toggleMapBtn) {
    toggleMapBtn.addEventListener('click', () => {
      const mapWrapper = document.getElementById('interactiveMapWrapper');
      const toggleText = document.getElementById('toggleMapBtnText');
      if (mapWrapper.classList.contains('hidden')) {
        mapWrapper.classList.remove('hidden');
        toggleText.textContent = '▲ Skrýt mapu ČR';
        setTimeout(() => {
          if (selectionMap) selectionMap.invalidateSize();
        }, 150);
      } else {
        mapWrapper.classList.add('hidden');
        toggleText.textContent = '🗺️ Otevřít mapu ČR k výběru';
      }
    });
  }

  // View toggle
  if (viewCardsBtn) viewCardsBtn.addEventListener('click', () => setView('cards'));
  if (viewTableBtn) viewTableBtn.addEventListener('click', () => setView('table'));
  if (viewMapBtn) viewMapBtn.addEventListener('click', () => setView('map'));

  // Sort change
  if (sortBySelect) {
    sortBySelect.addEventListener('change', () => {
      if (currentResults.length > 0) {
        sortAndRenderResults();
      }
    });
  }

  // Export CSV
  if (exportCsvBtn) {
    exportCsvBtn.addEventListener('click', () => {
      if (!currentCriteria) return;
      exportCSV();
    });
  }

  // Empty state buttons
  if (showAllFlatsBtn) {
    showAllFlatsBtn.addEventListener('click', () => {
      const belowAvgCb = document.getElementById('onlyBelowAverage');
      if (belowAvgCb) belowAvgCb.checked = false;
      if (minDiscountSlider) minDiscountSlider.value = '0';
      updateSliderLabel(0);
      performSearch();
    });
  }

  if (resetDiscountBtn) {
    resetDiscountBtn.addEventListener('click', () => {
      if (minDiscountSlider) minDiscountSlider.value = '0';
      updateSliderLabel(0);
      performSearch();
    });
  }

  // Main Search Form submit (ONLY TRIGGERS WHEN USER CLICKS BUTTON)
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      // If user typed in the location input without pressing Enter, add it
      if (locationInput && locationInput.value.trim()) {
        addLocation(locationInput.value.trim());
        locationInput.value = '';
      }
      performSearch();
    });
  }

  syncAllDispositionPills();
}

// -------------------------------------------------------------
// Search Execution
// -------------------------------------------------------------

function getSearchCriteria() {
  const locList = Array.from(selectedLocations);
  const primaryLocation = locList.length > 0 ? locList[0] : 'Praha';
  
  const dispositions = Array.from(
    document.querySelectorAll('input[name="disposition"]:checked')
  ).map(cb => cb.value);

  const minPrice = document.getElementById('minPrice')?.value ? parseInt(document.getElementById('minPrice').value) : null;
  const maxPrice = document.getElementById('maxPrice')?.value ? parseInt(document.getElementById('maxPrice').value) : null;
  const minArea = document.getElementById('minArea')?.value ? parseInt(document.getElementById('minArea').value) : null;
  const maxArea = document.getElementById('maxArea')?.value ? parseInt(document.getElementById('maxArea').value) : null;

  const portals = Array.from(
    document.querySelectorAll('input[name="portal"]:checked')
  ).map(cb => cb.value);

  const onlyBelowAverage = document.getElementById('onlyBelowAverage')?.checked ?? true;
  const minDiscountPercent = parseFloat(document.getElementById('minDiscount')?.value) || 0.0;
  const customBenchmark = document.getElementById('customBenchmark')?.value ? parseFloat(document.getElementById('customBenchmark').value) : null;
  const sortBy = document.getElementById('sortBy')?.value || 'discount_desc';

  return {
    location: primaryLocation,
    locations: locList.length > 0 ? locList : ['Praha'],
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
    limit: 200
  };
}

function startLoadingProgress(locationsText) {
  const topBarContainer = document.getElementById('topProgressBarContainer');
  const topBar = document.getElementById('topProgressBar');
  const innerBar = document.getElementById('innerProgressBar');
  const liveProgressCard = document.getElementById('liveProgressCard');
  const searchBtn = document.getElementById('searchBtn');
  const searchBtnIcon = document.getElementById('searchBtnIcon');
  const searchBtnText = document.getElementById('searchBtnText');
  const timerSeconds = document.getElementById('timerSeconds');

  ['stepSreality', 'stepBezrealitky', 'stepRemax', 'stepBazos'].forEach(id => {
    const el = document.getElementById(id);
    const icon = document.getElementById(`${id}Icon`);
    if (el) el.className = 'flex items-center gap-2 p-2 rounded-lg bg-slate-50 text-slate-700 border border-slate-100';
    if (icon) icon.className = 'fa-solid fa-spinner fa-spin text-indigo-600';
  });

  if (searchBtn) searchBtn.disabled = true;
  if (searchBtnIcon) searchBtnIcon.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
  if (searchBtnText) searchBtnText.textContent = `Vyhledávám (${locationsText})...`;

  if (topBarContainer) topBarContainer.classList.remove('hidden');
  if (liveProgressCard) liveProgressCard.classList.remove('hidden');

  let currentPercent = 15;
  if (topBar) topBar.style.width = '15%';
  if (innerBar) innerBar.style.width = '15%';

  searchStartTime = Date.now();
  if (timerInterval) clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    const elapsed = ((Date.now() - searchStartTime) / 1000).toFixed(1);
    if (timerSeconds) timerSeconds.textContent = `${elapsed}s`;
  }, 100);

  if (progressInterval) clearInterval(progressInterval);
  progressInterval = setInterval(() => {
    if (currentPercent < 88) {
      currentPercent += Math.random() * 10;
      if (topBar) topBar.style.width = `${Math.min(88, currentPercent)}%`;
      if (innerBar) innerBar.style.width = `${Math.min(88, currentPercent)}%`;
    }

    const elapsedMs = Date.now() - searchStartTime;
    if (elapsedMs > 600) markStepDone('stepSreality', 'stepSrealityIcon');
    if (elapsedMs > 1200) markStepDone('stepBezrealitky', 'stepBezrealitkyIcon');
    if (elapsedMs > 1800) markStepDone('stepRemax', 'stepRemaxIcon');
    if (elapsedMs > 2400) markStepDone('stepBazos', 'stepBazosIcon');
  }, 300);
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

  if (topBar) topBar.style.width = '100%';
  if (innerBar) innerBar.style.width = '100%';

  ['stepSreality', 'stepBezrealitky', 'stepRemax', 'stepBazos'].forEach(id => {
    markStepDone(id, `${id}Icon`);
  });

  setTimeout(() => {
    if (topBarContainer) topBarContainer.classList.add('hidden');
    if (liveProgressCard) liveProgressCard.classList.add('hidden');
    if (topBar) topBar.style.width = '0%';
    if (innerBar) innerBar.style.width = '0%';
  }, 400);

  if (searchBtn) searchBtn.disabled = false;
  if (searchBtnIcon) searchBtnIcon.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i>';
  if (searchBtnText) searchBtnText.textContent = 'Vyhledat výhodné nabídky';
}

async function performSearch() {
  const criteria = getSearchCriteria();
  currentCriteria = criteria;

  const emptyState = document.getElementById('emptyState');
  const resultsGrid = document.getElementById('resultsGrid');
  const resultsTableContainer = document.getElementById('resultsTableContainer');
  const resultsMapContainer = document.getElementById('resultsMapContainer');
  const statsSection = document.getElementById('statsSection');

  const locSummary = criteria.locations.slice(0, 3).join(', ') + (criteria.locations.length > 3 ? ` (+${criteria.locations.length-3})` : '');
  startLoadingProgress(locSummary);

  if (emptyState) emptyState.classList.add('hidden');
  if (resultsGrid) resultsGrid.innerHTML = '';
  const tbody = document.getElementById('resultsTableBody');
  if (tbody) tbody.innerHTML = '';

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

    if (statsSection) statsSection.classList.remove('hidden');

    if (Date.now() - searchStartTime > 600 && statsSection) {
      statsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  } catch (error) {
    console.error('Search error:', error);
    if (emptyState) emptyState.classList.remove('hidden');
    const emptyTitle = document.getElementById('emptyTitle');
    const emptyDesc = document.getElementById('emptyDescription');
    if (emptyTitle) emptyTitle.textContent = 'Chyba při vyhledávání nabídek';
    if (emptyDesc) emptyDesc.textContent = `Nepodařilo se načíst data ze serveru (${error.message}). Zkuste to prosím za okamžik znovu.`;
  } finally {
    stopLoadingProgress();
  }
}

function renderStats(stats) {
  if (!stats) return;

  const statLoc = document.getElementById('statLocalityName');
  const statAvg = document.getElementById('statAvgM2');
  const statMed = document.getElementById('statMedianM2');
  const statTot = document.getElementById('statTotalScanned');
  const statBar = document.getElementById('statBargainsCount');
  const statMax = document.getElementById('statMaxSavings');
  const sourceBadge = document.getElementById('benchmarkSourceBadge');

  if (statLoc) statLoc.textContent = stats.locality_name;
  if (statAvg) statAvg.textContent = formatNumber(stats.average_price_per_m2);
  if (statMed) statMed.textContent = formatNumber(stats.median_price_per_m2);
  if (statTot) statTot.textContent = formatNumber(stats.total_scanned);
  if (statBar) statBar.textContent = formatNumber(stats.total_bargains);
  if (statMax) statMax.textContent = formatNumber(stats.max_savings_czk);
  if (sourceBadge) sourceBadge.textContent = stats.benchmark_source;
}

function sortAndRenderResults() {
  const sortBy = document.getElementById('sortBy')?.value || 'discount_desc';
  const emptyState = document.getElementById('emptyState');
  const resultsGrid = document.getElementById('resultsGrid');
  const resultsTableContainer = document.getElementById('resultsTableContainer');
  const resultsMapContainer = document.getElementById('resultsMapContainer');

  if (!currentResults || currentResults.length === 0) {
    if (emptyState) emptyState.classList.remove('hidden');
    if (resultsGrid) resultsGrid.classList.add('hidden');
    if (resultsTableContainer) resultsTableContainer.classList.add('hidden');
    if (resultsMapContainer) resultsMapContainer.classList.add('hidden');

    const emptyTitle = document.getElementById('emptyTitle');
    const emptyDesc = document.getElementById('emptyDescription');

    if (currentStats && currentStats.total_scanned > 0) {
      if (emptyTitle) emptyTitle.textContent = `Nalezeno ${currentStats.total_scanned} inzerátů, ale žádný pod průměrem`;
      if (emptyDesc) emptyDesc.textContent = 
        `V zadaných lokalitách bylo zanalyzováno ${currentStats.total_scanned} bytů (tržní průměr ${formatNumber(currentStats.average_price_per_m2)} Kč/m²), ale žádný nesplnil požadovanou slevu.`;
    } else {
      if (emptyTitle) emptyTitle.textContent = 'Nebyly nalezeny žádné inzeráty';
      if (emptyDesc) emptyDesc.textContent = 'Zkuste vybrat větší kraj, upravit cenové limity nebo povolit více dispozic.';
    }
    return;
  }

  if (emptyState) emptyState.classList.add('hidden');

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
  renderResultsOnMap();

  setView(activeView);
}

function renderCardsView(listings) {
  const container = document.getElementById('resultsGrid');
  if (!container) return;
  container.innerHTML = '';

  listings.forEach(flat => {
    const portal = PORTAL_META[flat.portal] || { name: flat.portal, color: 'bg-slate-100 text-slate-700', icon: 'fa-globe' };
    
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
        <div class="relative h-48 sm:h-52 bg-slate-100 overflow-hidden">
          <img
            src="${imgSrc}"
            alt="${escapeHtml(flat.title)}"
            class="flat-img w-full h-full object-cover"
            loading="lazy"
            onerror="this.src='${fallbackImg}'"
          />
          <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/20"></div>

          <div class="absolute top-3 left-3 right-3 flex items-center justify-between">
            ${tierBadgeHtml}
            <span class="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-black/60 backdrop-blur-xs text-white border border-white/20">
              ${flat.disposition} • ${flat.area_m2} m²
            </span>
          </div>

          <div class="absolute bottom-2.5 left-3 right-3 text-white">
            <p class="text-xs font-medium truncate flex items-center gap-1.5 drop-shadow-xs">
              <i class="fa-solid fa-location-dot text-indigo-400"></i> ${escapeHtml(flat.locality || flat.city)}
            </p>
          </div>
        </div>

        <div class="p-4 sm:p-5 space-y-4">
          <h3 class="font-bold text-sm sm:text-base text-slate-900 line-clamp-2 leading-snug hover:text-indigo-600 transition" title="${escapeHtml(flat.title)}">
            ${escapeHtml(flat.title)}
          </h3>

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
  if (!tbody) return;
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
  const viewMapBtn = document.getElementById('viewMapBtn');
  const resultsGrid = document.getElementById('resultsGrid');
  const resultsTableContainer = document.getElementById('resultsTableContainer');
  const resultsMapContainer = document.getElementById('resultsMapContainer');

  [cardsBtn, tableBtn, viewMapBtn].forEach(btn => {
    if (btn) btn.className = 'px-3 py-1 rounded-md text-slate-600 font-medium hover:text-slate-900 cursor-pointer';
  });

  if (resultsGrid) resultsGrid.classList.add('hidden');
  if (resultsTableContainer) resultsTableContainer.classList.add('hidden');
  if (resultsMapContainer) resultsMapContainer.classList.add('hidden');

  if (view === 'cards') {
    if (cardsBtn) cardsBtn.className = 'px-3 py-1 rounded-md bg-white text-slate-900 font-semibold shadow-2xs cursor-pointer';
    if (resultsGrid) resultsGrid.classList.remove('hidden');
  } else if (view === 'table') {
    if (tableBtn) tableBtn.className = 'px-3 py-1 rounded-md bg-white text-slate-900 font-semibold shadow-2xs cursor-pointer';
    if (resultsTableContainer) resultsTableContainer.classList.remove('hidden');
  } else if (view === 'map') {
    if (viewMapBtn) viewMapBtn.className = 'px-3 py-1 rounded-md bg-white text-slate-900 font-semibold shadow-2xs cursor-pointer';
    if (resultsMapContainer) resultsMapContainer.classList.remove('hidden');
    initResultsMap();
    setTimeout(() => {
      if (resultsMap) resultsMap.invalidateSize();
    }, 150);
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
    a.download = `vyhodne_byty_${currentCriteria.locations.join('_') || 'cr'}.csv`;
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
