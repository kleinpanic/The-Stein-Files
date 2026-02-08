// Stats page data visualization

async function loadStats() {
  const resp = await fetch('data/meta/catalog.json');
  const catalog = await resp.json();

  // PDF Type breakdown
  const byType = {};
  const byQuality = { high: 0, medium: 0, low: 0 };
  const byCategory = {};
  const bySource = {};
  let ocrApplied = 0;
  let needsOCR = 0;

  catalog.forEach(doc => {
    // Type
    const type = doc.pdf_type || 'unknown';
    if (!byType[type]) byType[type] = { count: 0, totalQuality: 0, high: 0, medium: 0, low: 0 };
    byType[type].count++;
    
    // Quality
    const quality = doc.text_quality_score || 0;
    byType[type].totalQuality += quality;
    
    if (quality >= 70) {
      byQuality.high++;
      byType[type].high++;
    } else if (quality >= 30) {
      byQuality.medium++;
      byType[type].medium++;
    } else {
      byQuality.low++;
      byType[type].low++;
    }

    // Category
    const cat = doc.document_category || 'uncategorized';
    byCategory[cat] = (byCategory[cat] || 0) + 1;

    // Source
    const source = doc.source_name || 'unknown';
    if (!bySource[source]) bySource[source] = { count: 0, totalQuality: 0 };
    bySource[source].count++;
    bySource[source].totalQuality += quality;

    // OCR
    if (doc.ocr_applied) ocrApplied++;
    if (type === 'image' && !doc.ocr_applied) needsOCR++;
  });

  // Populate type breakdown
  const typeList = document.getElementById('typeBreakdown');
  const typeIcons = { text: '📄', image: '🖼️', hybrid: '🔀', unknown: '❓' };
  Object.entries(byType).forEach(([type, data]) => {
    const avgQuality = (data.totalQuality / data.count).toFixed(1);
    const li = document.createElement('li');
    li.innerHTML = `<strong>${typeIcons[type] || ''} ${type}</strong>: ${data.count} docs (avg quality: ${avgQuality}/100)`;
    typeList.appendChild(li);
  });

  // Populate quality breakdown
  const qualityList = document.getElementById('qualityBreakdown');
  [
    { label: '⭐ High (70-100)', count: byQuality.high },
    { label: '⚠️ Medium (30-70)', count: byQuality.medium },
    { label: '❌ Low (0-30)', count: byQuality.low }
  ].forEach(item => {
    const li = document.createElement('li');
    const pct = ((item.count / catalog.length) * 100).toFixed(1);
    li.innerHTML = `<strong>${item.label}</strong>: ${item.count} (${pct}%)`;
    qualityList.appendChild(li);
  });

  // Populate category breakdown
  const catList = document.getElementById('categoryBreakdown');
  const catLabels = {
    'evidence-list': 'Evidence List',
    'correspondence': 'Correspondence',
    'legal-filing': 'Legal Filing',
    'memorandum': 'Memorandum',
    'report': 'Report',
    'flight-log': 'Flight Log',
    'uncategorized': 'Uncategorized'
  };
  Object.entries(byCategory).sort((a, b) => b[1] - a[1]).forEach(([cat, count]) => {
    const li = document.createElement('li');
    li.innerHTML = `<strong>${catLabels[cat] || cat}</strong>: ${count}`;
    catList.appendChild(li);
  });

  // Populate OCR breakdown
  const ocrList = document.getElementById('ocrBreakdown');
  [
    { label: '🔍 OCR Applied', count: ocrApplied },
    { label: '🖼️ Image PDFs Needing OCR', count: needsOCR },
    { label: '📄 Text PDFs (no OCR needed)', count: (byType.text?.count || 0) + (byType.hybrid?.count || 0) }
  ].forEach(item => {
    const li = document.createElement('li');
    li.innerHTML = `<strong>${item.label}</strong>: ${item.count}`;
    ocrList.appendChild(li);
  });

  // Populate quality table
  const qualityTable = document.getElementById('qualityTable');
  Object.entries(byType).forEach(([type, data]) => {
    const row = qualityTable.insertRow();
    const avgQuality = (data.totalQuality / data.count).toFixed(1);
    row.innerHTML = `
      <td>${typeIcons[type] || ''} ${type}</td>
      <td>${data.count}</td>
      <td>${avgQuality}/100</td>
      <td>${data.high}</td>
      <td>${data.medium}</td>
      <td>${data.low}</td>
    `;
  });

  // Populate source table
  const sourceTable = document.getElementById('sourceTable');
  Object.entries(bySource).sort((a, b) => b[1].count - a[1].count).forEach(([source, data]) => {
    const row = sourceTable.insertRow();
    const avgQuality = (data.totalQuality / data.count).toFixed(1);
    row.innerHTML = `
      <td>${source}</td>
      <td>${data.count}</td>
      <td>${avgQuality}/100</td>
    `;
  });
}

loadStats();
