// Phase 3 UX Enhancements - Add-on module
// Extends app.js without modifying it

(function() {
  'use strict';
  
  let currentResults = [];
  let currentMetaById = {};
  let totalDocumentCount = 0;
  
  // Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  
  function init() {
    setupKeyboardShortcuts();
    setupExportButton();
    setupShareButton();
    interceptResultRendering();
  }
  
  // Keyboard shortcuts
  function setupKeyboardShortcuts() {
    const searchInput = document.getElementById('searchInput');
    const clearButton = document.getElementById('clearFilters');
    
    if (!searchInput) return;
    
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
    
    // Add keyboard shortcut hint to search placeholder
    if (searchInput.placeholder) {
      searchInput.title = 'Press Ctrl+K to focus search, Esc to clear';
    }
  }
  
  // Export to CSV button
  function setupExportButton() {
    const searchMeta = document.querySelector('.search-meta .meta-left');
    if (!searchMeta) return;
    
    const exportBtn = document.createElement('button');
    exportBtn.id = 'exportCSV';
    exportBtn.className = 'button outline small';
    exportBtn.textContent = '📊 Export CSV';
    exportBtn.title = 'Export current search results to CSV';
    exportBtn.style.marginLeft = '1rem';
    
    exportBtn.addEventListener('click', exportToCSV);
    searchMeta.appendChild(exportBtn);
  }
  
  // Share search URL button
  function setupShareButton() {
    const searchMeta = document.querySelector('.search-meta .meta-left');
    if (!searchMeta) return;
    
    const shareBtn = document.createElement('button');
    shareBtn.id = 'shareSearch';
    shareBtn.className = 'button ghost small';
    shareBtn.textContent = '🔗 Share';
    shareBtn.title = 'Copy search URL to clipboard';
    shareBtn.style.marginLeft = '0.5rem';
    
    shareBtn.addEventListener('click', shareSearch);
    searchMeta.appendChild(shareBtn);
  }
  
  // Export results to CSV
  function exportToCSV() {
    if (currentResults.length === 0) {
      alert('No results to export');
      return;
    }
    
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
      'Tags',
      'URL'
    ]);
    
    // Data rows
    currentResults.forEach(result => {
      const meta = currentMetaById[result.id];
      if (!meta) return;
      
      rows.push([
        meta.title || '',
        meta.source_name || '',
        meta.document_category || '',
        meta.release_date || '',
        meta.pdf_type || '',
        meta.text_quality_score != null ? meta.text_quality_score : '',
        (meta.person_names || []).join('; '),
        (meta.locations || []).join('; '),
        (meta.case_numbers || []).join('; '),
        (meta.extracted_file_numbers || []).join('; '),
        (meta.tags || []).join('; '),
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
    
    // Add BOM for Excel compatibility
    const BOM = '\uFEFF';
    const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    
    // Generate filename with timestamp
    const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
    link.download = `eppie-results-${timestamp}.csv`;
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    // Show feedback
    const btn = document.getElementById('exportCSV');
    if (btn) {
      const originalText = btn.textContent;
      btn.textContent = '✓ Exported!';
      btn.disabled = true;
      setTimeout(() => {
        btn.textContent = originalText;
        btn.disabled = false;
      }, 2000);
    }
  }
  
  // Share search URL
  function shareSearch() {
    const url = window.location.href;
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(() => {
        const btn = document.getElementById('shareSearch');
        if (btn) {
          const originalText = btn.textContent;
          btn.textContent = '✓ Copied!';
          setTimeout(() => {
            btn.textContent = originalText;
          }, 2000);
        }
      }).catch(err => {
        console.error('Failed to copy URL:', err);
        fallbackCopyToClipboard(url);
      });
    } else {
      fallbackCopyToClipboard(url);
    }
  }
  
  // Fallback copy method for older browsers
  function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-9999px';
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand('copy');
      alert('URL copied to clipboard!');
    } catch (err) {
      alert('Failed to copy URL. Please copy manually: ' + text);
    }
    document.body.removeChild(textArea);
  }
  
  // Intercept result rendering to track current results
  function interceptResultRendering() {
    // Hook into MutationObserver to detect when results are rendered
    const resultsContainer = document.getElementById('results');
    if (!resultsContainer) return;
    
    // Store original fetch function to intercept catalog loading
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
      const promise = originalFetch.apply(this, args);
      
      promise.then(response => {
        const url = args[0];
        if (typeof url === 'string' && url.includes('catalog.json')) {
          response.clone().json().then(data => {
            totalDocumentCount = data.length;
            updateResultCountDisplay();
          });
        }
      });
      
      return promise;
    };
    
    // Observe result count changes
    const resultCountEl = document.getElementById('resultCount');
    if (resultCountEl) {
      const observer = new MutationObserver(() => {
        updateResultCountDisplay();
      });
      observer.observe(resultCountEl, { childList: true, characterData: true, subtree: true });
    }
  }
  
  // Enhanced result count display
  function updateResultCountDisplay() {
    const resultCountEl = document.getElementById('resultCount');
    if (!resultCountEl) return;
    
    const currentText = resultCountEl.textContent;
    const match = currentText.match(/(\d+)/);
    if (!match) return;
    
    const currentCount = parseInt(match[1].replace(/,/g, ''));
    
    if (totalDocumentCount > 0 && currentCount < totalDocumentCount) {
      resultCountEl.textContent = `Showing ${currentCount.toLocaleString()} of ${totalDocumentCount.toLocaleString()} documents`;
    } else if (totalDocumentCount > 0) {
      resultCountEl.textContent = `${currentCount.toLocaleString()} documents`;
    }
    
    // Update currentResults count for CSV export
    // (actual results array is tracked via the results container)
    currentResults = Array.from(document.querySelectorAll('.result-card')).map((card, i) => ({
      id: card.querySelector('a')?.href?.split('/').pop()?.replace('.html', '') || `doc-${i}`,
    }));
  }
  
  // Expose for debugging
  window.eppieUX = {
    currentResults,
    exportToCSV,
    shareSearch
  };
  
})();
