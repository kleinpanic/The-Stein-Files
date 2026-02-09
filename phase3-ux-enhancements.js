// Phase 3 UX Enhancements for Eppie
// Features: Result count, CSV export, keyboard shortcuts

// 1. Update result count display (add to renderResults function)
function updateResultCount(filteredCount, totalCount) {
  const countEl = document.getElementById('resultCount');
  if (!countEl) return;
  
  if (filteredCount === totalCount) {
    countEl.textContent = `${totalCount} documents`;
  } else {
    countEl.textContent = `Showing ${filteredCount} of ${totalCount} documents`;
  }
}

// 2. Export results to CSV
function exportResultsToCSV(results, metaById) {
  const rows = [];
  
  // CSV header
  rows.push([
    'Title',
    'Source',
    'Category',
    'Date',
    'Type',
    'Quality Score',
    'Person Names',
    'Locations',
    'Case Numbers',
    'File Numbers',
    'URL'
  ]);
  
  // Data rows
  results.forEach(result => {
    const meta = metaById[result.id];
    if (!meta) return;
    
    rows.push([
      meta.title || '',
      meta.source_name || '',
      meta.document_category || '',
      meta.release_date || '',
      meta.pdf_type || '',
      meta.text_quality_score || '',
      (meta.person_names || []).join('; '),
      (meta.locations || []).join('; '),
      (meta.case_numbers || []).join('; '),
      (meta.extracted_file_numbers || []).join('; '),
      `https://kleinpanic.github.io/The-Stein-Files/${result.id}.html`
    ]);
  });
  
  // Convert to CSV string
  const csvContent = rows.map(row => 
    row.map(cell => {
      const str = String(cell);
      // Escape quotes and wrap in quotes if contains comma, quote, or newline
      if (str.includes(',') || str.includes('"') || str.includes('\n')) {
        return `"${str.replace(/"/g, '""')}"`;
      }
      return str;
    }).join(',')
  ).join('\n');
  
  // Download
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `eppie-search-results-${Date.now()}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// 3. Keyboard shortcuts
function setupKeyboardShortcuts(searchInput, clearButton) {
  document.addEventListener('keydown', (e) => {
    // Ctrl+K or Cmd+K - Focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      searchInput.focus();
      searchInput.select();
    }
    
    // Escape - Clear search if focused
    if (e.key === 'Escape') {
      if (document.activeElement === searchInput) {
        searchInput.value = '';
        searchInput.blur();
        if (clearButton) {
          clearButton.click();
        }
      }
    }
  });
}

// 4. Copy search URL button
function copySearchURL() {
  const url = window.location.href;
  navigator.clipboard.writeText(url).then(() => {
    // Show temporary feedback
    const btn = document.getElementById('copySearchURL');
    if (btn) {
      const originalText = btn.textContent;
      btn.textContent = '✓ Copied!';
      setTimeout(() => {
        btn.textContent = originalText;
      }, 2000);
    }
  }).catch(err => {
    console.error('Failed to copy URL:', err);
    alert('Failed to copy URL to clipboard');
  });
}

// Usage instructions:
// 1. In main app.js, after renderResults(), call:
//    updateResultCount(filteredResults.length, allResults.length);
//
// 2. Add export CSV button to index.html near resultCount:
//    <button id="exportCSV" class="button outline">Export CSV</button>
//
// 3. Add event listener for export button:
//    document.getElementById('exportCSV').addEventListener('click', () => {
//      exportResultsToCSV(currentFilteredResults, metaById);
//    });
//
// 4. Call setupKeyboardShortcuts() on page load:
//    setupKeyboardShortcuts(searchInput, clearFiltersButton);
//
// 5. Add copy URL button:
//    <button id="copySearchURL" class="button ghost">Share search</button>
//    document.getElementById('copySearchURL').addEventListener('click', copySearchURL);
