function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

const SEARCH_MODE_FIELDS = {
  full: ["title", "content", "tags", "source_name", "file_name", "id", "person_names", "locations"],
  title: ["title"],
  tags: ["tags"],
  source: ["source_name"],
  file: ["file_name", "id"],
  person: ["person_names", "title", "content"],
  location: ["locations", "title", "content"],
  filenumber: ["extracted_file_numbers", "id"],
};

const SEARCH_MODE_PLACEHOLDERS = {
  full: "Search names, places, or terms (fuzzy)",
  title: "Search document titles",
  tags: "Search tags",
  source: "Search sources",
  file: "Search filename or ID",
  person: "Search by person name (e.g., Maxwell, Epstein)",
  location: "Search by location (e.g., Little St. James, New York)",
  filenumber: "Lookup file number (e.g., EFTA00004051, FBI123456)",
};

async function loadJson(path) {
  const res = await fetch(path);
  if (!res.ok) {
    throw new Error(`Failed to load ${path}`);
  }
  return res.json();
}

function uniqueSorted(values) {
  return Array.from(new Set(values)).sort();
}

function formatDate(dateStr) {
  if (!dateStr) return "Unknown";
  if (dateStr.length >= 10) return dateStr;
  return dateStr;
}

function buildSnippet(content, query) {
  const text = content || "";
  if (!query) return text.slice(0, 220);
  const lower = text.toLowerCase();
  const q = query.toLowerCase();
  const idx = lower.indexOf(q);
  if (idx === -1) return text.slice(0, 220);
  const start = Math.max(0, idx - 90);
  const end = Math.min(text.length, idx + 130);
  return text.slice(start, end);
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function highlightSnippet(snippet, query) {
  if (!query) return escapeHtml(snippet);
  const escaped = escapeHtml(snippet);
  const escapedQuery = escapeRegExp(escapeHtml(query));
  const regex = new RegExp(`(${escapedQuery})`, "ig");
  return escaped.replace(regex, "<mark>$1</mark>");
}

function applyFilters(docs, filters) {
  const {
    sources,
    years,
    tags,
    type,
    category,
    quality,
    dateFrom,
    dateTo,
    fileSizeMin,
    fileSizeMax,
    pageCountMin,
    pageCountMax,
    hasPhotos,
    ocrQualityMin
  } = filters;

  return docs.filter((doc) => {
    // Multi-select source filter
    if (sources && sources.length > 0 && !sources.includes(doc.source_name)) {
      return false;
    }

    // Multi-select year filter
    if (years && years.length > 0) {
      const docYear = (doc.release_date || "").slice(0, 4);
      if (!years.includes(docYear)) return false;
    }

    // Multi-select tag filter
    if (tags && tags.length > 0) {
      const docTags = doc.tags || [];
      const hasAnyTag = tags.some(tag => docTags.includes(tag));
      if (!hasAnyTag) return false;
    }

    // Single-select filters (backward compatibility)
    if (type && doc.pdf_type !== type) return false;
    if (category && doc.document_category !== category) return false;

    // Quality filter
    if (quality) {
      const score = doc.text_quality_score || 0;
      if (quality === "high" && score < 70) return false;
      if (quality === "medium" && (score < 30 || score >= 70)) return false;
      if (quality === "low" && score >= 30) return false;
    }

    // Date range filter
    if (dateFrom || dateTo) {
      const docDate = doc.release_date || "";
      if (dateFrom && docDate < dateFrom) return false;
      if (dateTo && docDate > dateTo) return false;
    }

    // File size filter (in bytes)
    if (fileSizeMin !== undefined || fileSizeMax !== undefined) {
      const fileSize = doc.file_size_bytes || 0;
      if (fileSizeMin !== undefined && fileSize < fileSizeMin) return false;
      if (fileSizeMax !== undefined && fileSize > fileSizeMax) return false;
    }

    // Page count filter
    if (pageCountMin !== undefined || pageCountMax !== undefined) {
      const pages = doc.pages || 0;
      if (pageCountMin !== undefined && pages < pageCountMin) return false;
      if (pageCountMax !== undefined && pages > pageCountMax) return false;
    }

    // Has photos filter
    if (hasPhotos === "yes") {
      if (doc.pdf_type !== "image" && doc.pdf_type !== "hybrid") return false;
    } else if (hasPhotos === "no") {
      if (doc.pdf_type !== "text") return false;
    }

    // OCR quality slider
    if (ocrQualityMin !== undefined && ocrQualityMin > 0) {
      const ocrConf = doc.ocr_confidence || 0;
      if (ocrConf < ocrQualityMin) return false;
    }

    return true;
  });
}

function sortResults(results, sortBy) {
  if (sortBy === "date") {
    return results.sort((a, b) => (b.release_date || "").localeCompare(a.release_date || ""));
  }
  if (sortBy === "quality") {
    return results.sort((a, b) => (b.text_quality_score || 0) - (a.text_quality_score || 0));
  }
  return results.sort((a, b) => (b.score || 0) - (a.score || 0));
}

function getStateFromUrl() {
  const params = new URLSearchParams(window.location.search);
  
  // Helper to parse comma-separated values
  const parseArray = (key) => {
    const val = params.get(key);
    return val ? val.split(',').filter(Boolean) : [];
  };

  return {
    q: params.get("q") || "",
    sources: parseArray("sources"),
    years: parseArray("years"),
    tags: parseArray("tags"),
    type: params.get("type") || "",
    category: params.get("category") || "",
    quality: params.get("quality") || "",
    dateFrom: params.get("dateFrom") || "",
    dateTo: params.get("dateTo") || "",
    fileSizeMin: params.get("fileSizeMin") ? parseInt(params.get("fileSizeMin")) : undefined,
    fileSizeMax: params.get("fileSizeMax") ? parseInt(params.get("fileSizeMax")) : undefined,
    pageCountMin: params.get("pageCountMin") ? parseInt(params.get("pageCountMin")) : undefined,
    pageCountMax: params.get("pageCountMax") ? parseInt(params.get("pageCountMax")) : undefined,
    hasPhotos: params.get("hasPhotos") || "",
    ocrQualityMin: params.get("ocrQualityMin") ? parseInt(params.get("ocrQualityMin")) : undefined,
    sort: params.get("sort") || "relevance",
    mode: params.get("mode") || "full",
  };
}

function updateUrl(state) {
  const params = new URLSearchParams();
  
  // Helper to add array params
  const addArray = (key, arr) => {
    if (arr && arr.length > 0) {
      params.set(key, arr.join(','));
    }
  };

  if (state.q) params.set("q", state.q);
  
  // Multi-select filters
  addArray("sources", state.sources);
  addArray("years", state.years);
  addArray("tags", state.tags);
  
  // Single-select filters
  if (state.type) params.set("type", state.type);
  if (state.category) params.set("category", state.category);
  if (state.quality) params.set("quality", state.quality);
  
  // Date range
  if (state.dateFrom) params.set("dateFrom", state.dateFrom);
  if (state.dateTo) params.set("dateTo", state.dateTo);
  
  // File size range
  if (state.fileSizeMin !== undefined) params.set("fileSizeMin", state.fileSizeMin);
  if (state.fileSizeMax !== undefined) params.set("fileSizeMax", state.fileSizeMax);
  
  // Page count range
  if (state.pageCountMin !== undefined) params.set("pageCountMin", state.pageCountMin);
  if (state.pageCountMax !== undefined) params.set("pageCountMax", state.pageCountMax);
  
  // Has photos
  if (state.hasPhotos) params.set("hasPhotos", state.hasPhotos);
  
  // OCR quality
  if (state.ocrQualityMin !== undefined && state.ocrQualityMin > 0) {
    params.set("ocrQualityMin", state.ocrQualityMin);
  }
  
  if (state.sort && state.sort !== "relevance") params.set("sort", state.sort);
  if (state.mode && state.mode !== "full") params.set("mode", state.mode);
  
  const query = params.toString();
  const newUrl = query ? `${window.location.pathname}?${query}` : window.location.pathname;
  window.history.replaceState({}, "", newUrl);
}

function findRelatedDocuments(doc, allMeta, limit = 5) {
  const related = [];
  const docCaseNumbers = new Set(doc.case_numbers || []);
  const docDate = doc.release_date ? new Date(doc.release_date) : null;
  
  for (const other of Object.values(allMeta)) {
    if (other.id === doc.id) continue;
    
    let relevance = 0;
    
    // Same case numbers (high relevance)
    const otherCaseNumbers = new Set(other.case_numbers || []);
    const commonCases = [...docCaseNumbers].filter(c => otherCaseNumbers.has(c));
    if (commonCases.length > 0) {
      relevance += 10 * commonCases.length;
    }
    
    // Similar date range (within 30 days)
    if (docDate && other.release_date) {
      const otherDate = new Date(other.release_date);
      const daysDiff = Math.abs((docDate - otherDate) / (1000 * 60 * 60 * 24));
      if (daysDiff <= 30) {
        relevance += Math.max(0, 5 - daysDiff / 10);
      }
    }
    
    // Same person names
    const docPersons = new Set(doc.person_names || []);
    const otherPersons = new Set(other.person_names || []);
    const commonPersons = [...docPersons].filter(p => otherPersons.has(p));
    if (commonPersons.length > 0) {
      relevance += 3 * commonPersons.length;
    }
    
    // Same locations
    const docLocations = new Set(doc.locations || []);
    const otherLocations = new Set(other.locations || []);
    const commonLocations = [...docLocations].filter(l => otherLocations.has(l));
    if (commonLocations.length > 0) {
      relevance += 2 * commonLocations.length;
    }
    
    if (relevance > 0) {
      related.push({ doc: other, relevance });
    }
  }
  
  return related
    .sort((a, b) => b.relevance - a.relevance)
    .slice(0, limit)
    .map(r => r.doc);
}

function renderResults(target, results, metaById, query) {
  target.innerHTML = "";
  results.forEach((result) => {
    const meta = metaById[result.id];
    if (!meta) return;
    const tags = (meta.tags || []).map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("");
    const snippet = buildSnippet(result.content, query);
    const snippetHtml = highlightSnippet(snippet, query);
    
    // Build metadata badges
    const metaBadges = [];
    
    // PDF type badge
    if (meta.pdf_type) {
      const typeIcons = {
        text: '📄',
        image: '🖼️',
        hybrid: '🔀'
      };
      const icon = typeIcons[meta.pdf_type] || '';
      metaBadges.push(`<span class="meta-badge type-${meta.pdf_type}">${icon} ${meta.pdf_type}</span>`);
    }
    
    // Quality badge
    if (meta.text_quality_score != null) {
      const score = meta.text_quality_score;
      let qualityClass = 'quality-low';
      let qualityLabel = 'Low quality';
      let qualityIcon = '❌';
      
      if (score >= 70) {
        qualityClass = 'quality-high';
        qualityLabel = 'High quality';
        qualityIcon = '⭐';
      } else if (score >= 30) {
        qualityClass = 'quality-medium';
        qualityLabel = 'Medium quality';
        qualityIcon = '⚠️';
      }
      
      metaBadges.push(`<span class="meta-badge ${qualityClass}" title="${score}/100">${qualityIcon} ${qualityLabel}</span>`);
    }
    
    // Category badge
    if (meta.document_category) {
      const categoryLabels = {
        'evidence-list': 'Evidence List',
        'correspondence': 'Correspondence',
        'legal-filing': 'Legal Filing',
        'memorandum': 'Memorandum',
        'report': 'Report',
        'flight-log': 'Flight Log',
        // Phase 1 categories
        'email': '📧 Email',
        'deposition': '📝 Deposition',
        'subpoena': '⚖️ Subpoena',
        'case-photo': '📷 Case Photo',
        'evidence-photo': '📷 Evidence Photo',
        'handwritten-note': '✍️ Handwritten Note'
      };
      const label = categoryLabels[meta.document_category] || meta.document_category;
      metaBadges.push(`<span class="meta-badge">${label}</span>`);
    }
    
    // OCR indicator + confidence (Phase 1)
    if (meta.ocr_applied) {
      if (meta.ocr_confidence != null) {
        const conf = Math.round(meta.ocr_confidence);
        const confClass = conf >= 70 ? 'ocr-high' : conf >= 50 ? 'ocr-medium' : 'ocr-low';
        metaBadges.push(`<span class="meta-badge ${confClass}" title="OCR applied with ${conf}% confidence">🔍 OCR ${conf}%</span>`);
      } else {
        metaBadges.push(`<span class="meta-badge" title="OCR applied">🔍 OCR</span>`);
      }
    }
    
    const metadataHtml = metaBadges.length > 0 ? `<div class="doc-metadata">${metaBadges.join('')}</div>` : '';
    
    // File numbers
    const fileNumbers = (meta.extracted_file_numbers || []).slice(0, 5)
      .map(num => `<span class="file-number">${escapeHtml(num)}</span>`)
      .join('');
    const fileNumbersHtml = fileNumbers ? `<div class="file-numbers">${fileNumbers}</div>` : '';
    
    // Phase 1: Person names
    const personNames = (meta.person_names || []).slice(0, 3)
      .map(name => `<span class="person-name">👤 ${escapeHtml(name)}</span>`)
      .join('');
    const personNamesHtml = personNames ? `<div class="person-names">${personNames}</div>` : '';
    
    // Phase 1: Locations
    const locations = (meta.locations || []).slice(0, 3)
      .map(loc => `<span class="location">📍 ${escapeHtml(loc)}</span>`)
      .join('');
    const locationsHtml = locations ? `<div class="locations">${locations}</div>` : '';
    
    // Phase 1: Case numbers
    const caseNumbers = (meta.case_numbers || []).slice(0, 3)
      .map(num => `<span class="case-number">⚖️ ${escapeHtml(num)}</span>`)
      .join('');
    const caseNumbersHtml = caseNumbers ? `<div class="case-numbers">${caseNumbers}</div>` : '';
    
    // Find related documents
    const relatedDocs = findRelatedDocuments(meta, metaById, 3);
    const relatedHtml = relatedDocs.length > 0 ? `
      <div class="related-docs">
        <strong>Related:</strong>
        ${relatedDocs.map(related => 
          `<a href="documents/${related.id}.html" class="related-link">${escapeHtml(related.title.slice(0, 60))}${related.title.length > 60 ? '...' : ''}</a>`
        ).join(' · ')}
      </div>
    ` : '';
    
    const card = document.createElement("div");
    card.className = "result-card";
    card.innerHTML = `
      <h3>${escapeHtml(meta.title)}</h3>
      <div class="result-meta">
        <span>${formatDate(meta.release_date)}</span>
        <span>${escapeHtml(meta.source_name)}</span>
      </div>
      ${metadataHtml}
      ${fileNumbersHtml}
      ${personNamesHtml}
      ${locationsHtml}
      ${caseNumbersHtml}
      <div class="result-tags">${tags}</div>
      <p class="result-snippet">${snippetHtml}</p>
      ${relatedHtml}
      <div class="result-actions">
        <a class="button" href="${meta.source_url || meta.file_path}">Original</a>
        <a class="button outline" href="data/derived/text/${meta.id}.txt">Text</a>
        <a class="button ghost" href="documents/${meta.id}.html">Details</a>
      </div>
    `;
    target.appendChild(card);
  });
}

async function init() {
  const loadingState = document.getElementById("loadingState");
  const emptyState = document.getElementById("emptyState");
  const noResultsState = document.getElementById("noResultsState");
  const resultCount = document.getElementById("resultCount");
  const loadStatus = document.getElementById("loadStatus");
  const resultsEl = document.getElementById("results");

  loadingState.hidden = false;
  const [manifest, catalog] = await Promise.all([
    loadJson("data/derived/index/manifest.json"),
    loadJson("data/meta/catalog.json"),
  ]);

  const hasCatalog = catalog.length > 0;
  if (!hasCatalog) {
    emptyState.hidden = false;
    noResultsState.hidden = true;
  }

  const metaById = {};
  catalog.forEach((doc) => {
    metaById[doc.id] = doc;
  });

  const sources = uniqueSorted(catalog.map((doc) => doc.source_name));
  const years = uniqueSorted(
    catalog
      .map((doc) => (doc.release_date ? doc.release_date.slice(0, 4) : ""))
      .filter((year) => year && /\d{4}/.test(year))
  );
  const tags = uniqueSorted(catalog.flatMap((doc) => doc.tags || []));
  const categories = uniqueSorted(
    catalog
      .map((doc) => doc.document_category)
      .filter(cat => cat)
  );

  // Multi-select filter elements
  const filterSources = document.getElementById("filterSources");
  const filterYears = document.getElementById("filterYears");
  const filterTags = document.getElementById("filterTags");
  
  // Single-select filter elements
  const filterType = document.getElementById("filterType");
  const filterCategory = document.getElementById("filterCategory");
  const filterQuality = document.getElementById("filterQuality");
  
  // New Phase 2 filter elements
  const filterDateFrom = document.getElementById("filterDateFrom");
  const filterDateTo = document.getElementById("filterDateTo");
  const filterFileSizePreset = document.getElementById("filterFileSizePreset");
  const filterPageCountPreset = document.getElementById("filterPageCountPreset");
  const filterHasPhotos = document.getElementById("filterHasPhotos");
  const filterOcrQuality = document.getElementById("filterOcrQuality");
  const ocrQualityValue = document.getElementById("ocrQualityValue");
  
  // Other elements
  const sortBy = document.getElementById("sortBy");
  const searchInput = document.getElementById("searchInput");
  const searchMode = document.getElementById("searchMode");
  const clearFilters = document.getElementById("clearFilters");

  // Populate multi-select dropdowns
  filterSources.innerHTML = sources
    .map((s) => `<option value="${escapeHtml(s)}">${escapeHtml(s)}</option>`)
    .join("");
  
  filterYears.innerHTML = years
    .map((y) => `<option value="${y}">${y}</option>`)
    .join("");
  
  filterTags.innerHTML = tags
    .map((t) => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`)
    .join("");
  
  // Populate category filter
  if (categories.length > 0) {
    const categoryLabels = {
      'evidence-list': 'Evidence List',
      'correspondence': 'Correspondence',
      'legal-filing': 'Legal Filing',
      'memorandum': 'Memorandum',
      'report': 'Report',
      'flight-log': 'Flight Log',
      'email': 'Email',
      'deposition': 'Deposition',
      'subpoena': 'Subpoena',
      'case-photo': 'Case Photo',
      'evidence-photo': 'Evidence Photo',
      'handwritten-note': 'Handwritten Note'
    };
    filterCategory.innerHTML += categories
      .map((cat) => `<option value="${cat}">${categoryLabels[cat] || cat}</option>`)
      .join("");
  }

  // Restore state from URL
  const state = getStateFromUrl();
  searchInput.value = state.q;
  
  // Set multi-select values
  if (state.sources && state.sources.length > 0) {
    Array.from(filterSources.options).forEach(opt => {
      opt.selected = state.sources.includes(opt.value);
    });
  }
  
  if (state.years && state.years.length > 0) {
    Array.from(filterYears.options).forEach(opt => {
      opt.selected = state.years.includes(opt.value);
    });
  }
  
  if (state.tags && state.tags.length > 0) {
    Array.from(filterTags.options).forEach(opt => {
      opt.selected = state.tags.includes(opt.value);
    });
  }
  
  // Set single-select values
  filterType.value = state.type || "";
  filterCategory.value = state.category || "";
  filterQuality.value = state.quality || "";
  
  // Set new Phase 2 filter values
  filterDateFrom.value = state.dateFrom || "";
  filterDateTo.value = state.dateTo || "";
  filterHasPhotos.value = state.hasPhotos || "";
  
  if (state.ocrQualityMin !== undefined) {
    filterOcrQuality.value = state.ocrQualityMin;
    ocrQualityValue.textContent = state.ocrQualityMin;
  }
  
  sortBy.value = state.sort;
  searchMode.value = state.mode;

  searchInput.placeholder = SEARCH_MODE_PLACEHOLDERS[searchMode.value] || SEARCH_MODE_PLACEHOLDERS.full;

  // Build search suggestions
  const allPersonNames = new Set();
  const allLocations = new Set();
  catalog.forEach((doc) => {
    (doc.person_names || []).forEach(name => allPersonNames.add(name));
    (doc.locations || []).forEach(loc => allLocations.add(loc));
  });

  function updateSearchSuggestions() {
    const mode = searchMode.value;
    let suggestions = [];
    
    if (mode === "person") {
      suggestions = Array.from(allPersonNames).sort();
    } else if (mode === "location") {
      suggestions = Array.from(allLocations).sort();
    } else if (mode === "tags") {
      suggestions = tags;
    } else if (mode === "full") {
      // Mix of common terms
      suggestions = [
        ...Array.from(allPersonNames).slice(0, 20),
        ...Array.from(allLocations).slice(0, 20),
        ...tags.slice(0, 20)
      ].sort();
    }
    
    // Create or update datalist
    let datalist = document.getElementById("searchSuggestions");
    if (!datalist) {
      datalist = document.createElement("datalist");
      datalist.id = "searchSuggestions";
      document.body.appendChild(datalist);
      searchInput.setAttribute("list", "searchSuggestions");
    }
    
    datalist.innerHTML = suggestions
      .map(s => `<option value="${escapeHtml(s)}">`)
      .join("");
  }

  updateSearchSuggestions();

  const shardLookup = manifest.shards || [];

  const loadedShards = new Map();
  let indexDocs = [];
  let lunrIndex = null;

  function rebuildIndex() {
    lunrIndex = lunr(function () {
      this.ref("id");
      this.field("title");
      this.field("content");
      this.field("source_name");
      this.field("tags");
      this.field("file_name");
      this.field("id");
      this.field("person_names");
      this.field("locations");
      this.field("extracted_file_numbers");
      indexDocs.forEach((doc) => this.add(doc));
    });
  }

  async function loadShard(path) {
    if (loadedShards.has(path)) return;
    const docs = await loadJson(path);
    loadedShards.set(path, docs);
    indexDocs = Array.from(loadedShards.values()).flat();
    rebuildIndex();
    if (loadingState.hidden === false) {
      loadingState.hidden = true;
    }
  }

  async function loadShardsForState(currentState) {
    const { sources, years } = currentState;
    
    const desired = shardLookup.filter((shard) => {
      // If sources specified, match any of them
      if (sources && sources.length > 0) {
        if (!sources.includes(shard.source_name)) return false;
      }
      // If years specified, match any of them
      if (years && years.length > 0) {
        if (!years.includes(shard.year)) return false;
      }
      return true;
    });
    
    if (!desired.length) {
      // If no shards match, load all
      await loadAllShardsProgressively();
      return;
    }
    
    for (const shard of desired) {
      await loadShard(shard.path);
      loadStatus.textContent = `Loaded ${loadedShards.size} of ${shardLookup.length} shards`;
      performSearch();
    }
  }

  async function loadAllShardsProgressively() {
    for (const shard of shardLookup) {
      await loadShard(shard.path);
      loadStatus.textContent = `Loaded ${loadedShards.size} of ${shardLookup.length} shards`;
      performSearch();
    }
  }

  // Helper to get selected values from multi-select
  function getSelectedValues(selectElement) {
    if (!selectElement) return [];
    return Array.from(selectElement.selectedOptions).map(opt => opt.value);
  }

  // Helper to convert file size preset to bytes
  function fileSizePresetToBytes(preset) {
    const presets = {
      'small': { min: 0, max: 100 * 1024 }, // < 100 KB (text docs)
      'medium': { min: 100 * 1024, max: 1024 * 1024 }, // 100 KB - 1 MB
      'large': { min: 1024 * 1024, max: 10 * 1024 * 1024 }, // 1 MB - 10 MB (photos)
      'xlarge': { min: 10 * 1024 * 1024, max: undefined } // > 10 MB
    };
    return presets[preset] || { min: undefined, max: undefined };
  }

  // Helper to convert page count preset to range
  function pageCountPresetToRange(preset) {
    const presets = {
      'single': { min: 1, max: 1 },
      'few': { min: 2, max: 5 },
      'many': { min: 6, max: 50 },
      'large': { min: 51, max: undefined }
    };
    return presets[preset] || { min: undefined, max: undefined };
  }

  function performSearch() {
    if (!indexDocs.length) {
      resultsEl.innerHTML = "";
      resultCount.textContent = "0 results";
      if (!hasCatalog) {
        noResultsState.hidden = true;
      } else {
        noResultsState.hidden = loadingState.hidden === false;
      }
      return;
    }
    const query = searchInput.value.trim();
    
    const fileSizeRange = filterFileSizePreset ? fileSizePresetToBytes(filterFileSizePreset.value) : { min: undefined, max: undefined };
    const pageCountRange = filterPageCountPreset ? pageCountPresetToRange(filterPageCountPreset.value) : { min: undefined, max: undefined };
    
    const filters = {
      sources: getSelectedValues(filterSources),
      years: getSelectedValues(filterYears),
      tags: getSelectedValues(filterTags),
      type: filterType ? filterType.value : "",
      category: filterCategory ? filterCategory.value : "",
      quality: filterQuality ? filterQuality.value : "",
      dateFrom: filterDateFrom ? filterDateFrom.value : "",
      dateTo: filterDateTo ? filterDateTo.value : "",
      fileSizeMin: fileSizeRange.min,
      fileSizeMax: fileSizeRange.max,
      pageCountMin: pageCountRange.min,
      pageCountMax: pageCountRange.max,
      hasPhotos: filterHasPhotos ? filterHasPhotos.value : "",
      ocrQualityMin: filterOcrQuality ? parseInt(filterOcrQuality.value) : undefined,
    };

    let docs = indexDocs;
    if (query && lunrIndex) {
      const mode = searchMode.value;
      const fields = SEARCH_MODE_FIELDS[mode] || SEARCH_MODE_FIELDS.full;
      
      // File number lookup: exact matching
      if (mode === "filenumber") {
        const queryUpper = query.toUpperCase();
        docs = indexDocs
          .filter((doc) => {
            const fileNumbers = doc.extracted_file_numbers || [];
            return fileNumbers.some(num => num.toUpperCase().includes(queryUpper));
          })
          .map((doc) => ({ ...doc, score: 1.0 }));
      } else {
        // Normalize query terms for case-insensitive search
        const terms = query
          .split(/\s+/)
          .filter(Boolean)
          .map((term) => term.toLowerCase());
        
        // Fuzzy search: add wildcards and edit distance for full/person/location modes
        const useFuzzy = ["full", "person", "location"].includes(mode);
        
        const hits = lunrIndex.query((q) => {
          terms.forEach((term) => {
            // Standard term search
            q.term(term, { fields, boost: 10 });
            
            if (useFuzzy) {
              // Fuzzy search with edit distance 1 (handles typos)
              q.term(term, { fields, editDistance: 1, boost: 5 });
              
              // Wildcard search (handles partial matches, OCR errors)
              if (term.length > 3) {
                q.term(term + "*", { fields, boost: 3 });
                q.term("*" + term, { fields, boost: 2 });
              }
            }
          });
        });
        
        const hitMap = new Map(hits.map((h) => [h.ref, h.score]));
        docs = indexDocs
          .filter((doc) => hitMap.has(doc.id))
          .map((doc) => ({ ...doc, score: hitMap.get(doc.id) }));
      }
    }

    docs = applyFilters(docs, filters);
    const sorted = sortResults(docs, sortBy.value);
    renderResults(resultsEl, sorted, metaById, query);
    resultCount.textContent = `${sorted.length.toLocaleString()} result${sorted.length === 1 ? '' : 's'}`;
    noResultsState.hidden = sorted.length > 0;
  }

  function syncAndSearch() {
    const fileSizeRange = filterFileSizePreset ? fileSizePresetToBytes(filterFileSizePreset.value) : { min: undefined, max: undefined };
    const pageCountRange = filterPageCountPreset ? pageCountPresetToRange(filterPageCountPreset.value) : { min: undefined, max: undefined };
    
    const nextState = {
      q: searchInput.value.trim(),
      sources: getSelectedValues(filterSources),
      years: getSelectedValues(filterYears),
      tags: getSelectedValues(filterTags),
      type: filterType ? filterType.value : "",
      category: filterCategory ? filterCategory.value : "",
      quality: filterQuality ? filterQuality.value : "",
      dateFrom: filterDateFrom ? filterDateFrom.value : "",
      dateTo: filterDateTo ? filterDateTo.value : "",
      fileSizeMin: fileSizeRange.min,
      fileSizeMax: fileSizeRange.max,
      pageCountMin: pageCountRange.min,
      pageCountMax: pageCountRange.max,
      hasPhotos: filterHasPhotos ? filterHasPhotos.value : "",
      ocrQualityMin: filterOcrQuality ? parseInt(filterOcrQuality.value) : undefined,
      sort: sortBy.value,
      mode: searchMode.value,
    };
    updateUrl(nextState);
    performSearch();
  }

  // Update OCR quality display
  if (filterOcrQuality && ocrQualityValue) {
    filterOcrQuality.addEventListener("input", () => {
      ocrQualityValue.textContent = filterOcrQuality.value;
      syncAndSearch();
    });
  }

  // Attach change listeners to all filter elements
  const filterElements = [
    filterSources, filterYears, filterTags,
    filterType, filterCategory, filterQuality,
    filterDateFrom, filterDateTo,
    filterFileSizePreset, filterPageCountPreset,
    filterHasPhotos,
    sortBy, searchMode
  ].filter(el => el); // Filter out any null elements

  filterElements.forEach((el) =>
    el.addEventListener("change", () => {
      if (el === searchMode) {
        searchInput.placeholder =
          SEARCH_MODE_PLACEHOLDERS[searchMode.value] || SEARCH_MODE_PLACEHOLDERS.full;
        updateSearchSuggestions();
      }
      syncAndSearch();
      
      // Load shards based on selected sources/years
      const selectedSources = getSelectedValues(filterSources);
      const selectedYears = getSelectedValues(filterYears);
      
      if (selectedSources.length === 0 && selectedYears.length === 0) {
        loadAllShardsProgressively();
      }
      // Note: Multi-select shard loading would need updated logic
      // For now, load all shards when any filter is selected
    })
  );
  
  searchInput.addEventListener("input", syncAndSearch);
  
  clearFilters.addEventListener("click", () => {
    searchInput.value = "";
    
    // Clear multi-select
    if (filterSources) Array.from(filterSources.options).forEach(opt => opt.selected = false);
    if (filterYears) Array.from(filterYears.options).forEach(opt => opt.selected = false);
    if (filterTags) Array.from(filterTags.options).forEach(opt => opt.selected = false);
    
    // Clear single-select
    if (filterType) filterType.value = "";
    if (filterCategory) filterCategory.value = "";
    if (filterQuality) filterQuality.value = "";
    
    // Clear Phase 2 filters
    if (filterDateFrom) filterDateFrom.value = "";
    if (filterDateTo) filterDateTo.value = "";
    if (filterFileSizePreset) filterFileSizePreset.value = "";
    if (filterPageCountPreset) filterPageCountPreset.value = "";
    if (filterHasPhotos) filterHasPhotos.value = "";
    if (filterOcrQuality) {
      filterOcrQuality.value = "0";
      if (ocrQualityValue) ocrQualityValue.textContent = "0";
    }
    
    sortBy.value = "relevance";
    searchMode.value = "full";
    searchInput.placeholder = SEARCH_MODE_PLACEHOLDERS.full;
    syncAndSearch();
    loadAllShardsProgressively();
  });

  const filtersPanel = document.getElementById("filtersPanel");
  const openFilters = document.getElementById("openFilters");
  const closeFilters = document.getElementById("closeFilters");
  const backdrop = document.getElementById("filtersBackdrop");
  openFilters.addEventListener("click", () => {
    filtersPanel.classList.add("open");
    backdrop.hidden = false;
  });
  closeFilters.addEventListener("click", () => {
    filtersPanel.classList.remove("open");
    backdrop.hidden = true;
  });
  backdrop.addEventListener("click", () => {
    filtersPanel.classList.remove("open");
    backdrop.hidden = true;
  });

  // Initial shard loading based on URL state
  const initialSources = getSelectedValues(filterSources);
  const initialYears = getSelectedValues(filterYears);
  
  if (initialSources.length > 0 || initialYears.length > 0) {
    await loadShardsForState({ sources: initialSources, years: initialYears });
  } else {
    await loadAllShardsProgressively();
  }

  syncAndSearch();
}

function encodePath(path) {
  return String(path)
    .split("/")
    .map((part) => encodeURIComponent(part))
    .join("/");
}

function getMetaContent(name) {
  const meta = document.querySelector(`meta[name="${name}"]`);
  return meta ? meta.getAttribute("content") || "" : "";
}

async function initViewer() {
  const frame = document.getElementById("viewer-frame");
  if (!frame) return;

  const titleEl = document.getElementById("viewer-title");
  const originalLink = document.getElementById("viewer-original");
  const githubLink = document.getElementById("viewer-github");
  const textLink = document.getElementById("viewer-text");

  const params = new URLSearchParams(window.location.search);
  const id = params.get("id") || "";
  if (!id) {
    if (titleEl) titleEl.textContent = "Missing document id";
    return;
  }

  const catalogResp = await fetch("data/meta/catalog.json");
  const catalog = await catalogResp.json();
  const entry = (catalog || []).find((item) => item.id === id);
  if (!entry) {
    if (titleEl) titleEl.textContent = `Unknown document: ${id}`;
    return;
  }

  if (titleEl) titleEl.textContent = entry.title || id;
  if (originalLink) originalLink.href = entry.source_url || "#";
  if (textLink) textLink.href = `data/derived/text/${encodeURIComponent(id)}.txt`;

  const buildSha = getMetaContent("build-sha");
  const repoSlug = getMetaContent("repo-slug") || "kleinpanic/The-Stein-Files";
  const filePath = entry.file_path || "";

  let pdfUrl = "";
  if (filePath && (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")) {
    // Local dev: raw files may be present if EPPIE_MIRROR_MODE=1 during build.
    pdfUrl = encodePath(filePath);
  } else if (filePath && buildSha) {
    pdfUrl = `https://raw.githubusercontent.com/${repoSlug}/${buildSha}/${encodePath(filePath)}`;
  }

  if (githubLink && filePath && buildSha) {
    githubLink.href = `https://github.com/${repoSlug}/blob/${buildSha}/${encodePath(filePath)}`;
  }

  if (!pdfUrl) {
    if (titleEl) titleEl.textContent = `${entry.title || id} (no PDF link)`;
    return;
  }

  frame.src = pdfUrl;
}

if (document.getElementById("searchInput") && document.getElementById("loadingState")) {
  init().catch((err) => {
    console.error(err);
  });
}

initViewer().catch((err) => {
  console.error(err);
});
