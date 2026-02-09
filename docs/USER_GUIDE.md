# Epstein Files Library - User Guide

## Getting Started

Visit [https://kleinpanic.github.io/The-Stein-Files/](https://kleinpanic.github.io/The-Stein-Files/) to start searching 947 officially released documents.

## Search Tips

### Basic Search
- Type any term in the search box and press Enter
- Search is **fuzzy** - handles typos and OCR errors
- Results show document title, source, date, and content preview

### Search Modes

Click the dropdown next to the search box to switch modes:

**Full text (fuzzy)** - Default mode, searches everything  
**👤 Person** - Search by person name (e.g., "Maxwell", "Epstein")  
**📍 Location** - Search by place (e.g., "Little St. James", "New York")  
**🔢 File number** - Exact match on EFTA/FBI numbers (e.g., "EFTA00004051")  
**Title only** - Search document titles only  
**Tags only** - Search auto-generated tags  
**Source only** - Search by source name  
**Filename/ID** - Search by filename or document ID  

### Keyboard Shortcuts

- **Ctrl+K** (or Cmd+K on Mac) - Focus search box
- **Esc** - Clear search and filters

## Filters

Click the **Filters** button to refine your search:

### Multi-Select Filters
- **Sources**: Select multiple sources (DOJ, FBI, etc.)
- **Years**: Select multiple release years
- **Tags**: Select multiple auto-generated tags

### Single-Select Filters
- **Document Type**: Text-based, image-based, or hybrid
- **Category**: Correspondence, depositions, flight logs, etc.
- **Quality**: Filter by document quality score (0-100)

### Advanced Filters
- **Date Range**: From/to date picker (YYYY-MM-DD)
- **File Size**: Small (<100KB), Medium (100KB-1MB), Large (1-10MB), XLarge (>10MB)
- **Page Count**: Single page, few (2-5), many (6-50), large (>50)
- **Has Photos**: Show only image/hybrid PDFs
- **OCR Quality**: Slider to filter by OCR confidence (0-100%)

### Filter Tips
- **Combine filters** for precise results (e.g., "flight-log + 1990s + high quality")
- **URL updates** as you filter - bookmark or share your search
- **Clear filters** button resets everything

## Exporting Results

After searching, click **📊 Export CSV** to download your results with full metadata:
- Document titles, sources, categories, dates
- Person names, locations, case numbers mentioned
- File numbers, tags, quality scores
- Direct links to each document

**Format**: UTF-8 CSV with BOM (Excel-compatible)  
**Use case**: Offline analysis, research notes, data visualization

## Sharing Searches

Click **🔗 Share** to copy the current search URL to your clipboard. The URL includes:
- Your search query and mode
- All active filters
- Sort order

Anyone with the link will see the same search results.

## Person Profiles

Click **People** in the navigation to explore major individuals mentioned in the documents.

### Features
- **Accordion view**: Click a person to expand their profile
- **Statistics**: Total mentions, document types, timeline span
- **Document breakdown**: Visual chart of document types (depositions, emails, etc.)
- **Timeline**: Chronological list of all documents mentioning this person (sort by newest/oldest)
- **Search within person**: Filter their documents by keyword or category

### Major People (5+ mentions)
- **Jeffrey Epstein** - 119 mentions
- **Ghislaine Maxwell** - 67 mentions
- **Lesley Groff** - 20 mentions

## Emails Section

Click **Emails** in the navigation to browse 149 email and correspondence documents.

### Features
- **Metadata extraction**: From, To, Subject, Date (when available)
- **Epstein filter**: Show only emails sent by or received by Jeffrey Epstein (15 identified)
- **Group by**: Chronological (year), by sender, by recipient
- **Sort**: Newest first / oldest first
- **Search**: Search within subject, sender, recipient, or content

## Mobile Usage

The site is optimized for mobile devices:

### Filters
- **Swipe up** from the "Filters" button to open the filter drawer
- **Swipe down** to close
- **Touch targets**: All buttons are WCAG 2.1 AAA compliant (48x48px minimum)

### Search
- **Sticky search bar**: Stays at the top when scrolling
- **Optimized rendering**: PDFs load faster on mobile devices

### Tips
- **Portrait mode recommended** for reading documents
- **Landscape mode** gives more screen space for filters
- **Pinch to zoom** on PDF pages

## Understanding Results

### Document Badges

**PDF Type**:
- 📄 **Text-based**: Searchable text embedded in PDF
- 🖼️ **Image-based**: Scanned documents (OCR applied)
- 🔀 **Hybrid**: Mix of text and images

**Quality**:
- ⭐ **High quality** (70-100): Clean, readable text
- ⚠️ **Medium quality** (30-69): Some OCR errors or formatting issues
- ❌ **Low quality** (0-29): Significant OCR errors, may be difficult to read

**Category Examples**:
- 📧 **Email**
- 📝 **Deposition**
- ⚖️ **Subpoena**
- 📷 **Evidence Photo**
- ✈️ **Flight Log**

**OCR Indicator**:
- 🔍 **OCR [X%]**: Document processed with Optical Character Recognition (confidence score)

### Related Documents

Each result shows up to 3 related documents based on:
1. **Same case numbers** (highest priority)
2. **Same person names**
3. **Same locations**
4. **Similar release dates** (within 30 days)

## Statistics Dashboard

Click **Stats** in the navigation for collection-wide analytics:

- **Timeline visualization**: Documents by release date
- **Type breakdown**: Text vs. image vs. hybrid distribution
- **Quality distribution**: Document quality scores
- **OCR status**: How many documents have OCR applied
- **Category breakdown**: Most common document types
- **Source statistics**: Documents per source

## Research Tips

### Finding Specific Information

**Looking for a person?**
- Use **Person search mode** or click their name in **People** section
- Check **Related Documents** for connections

**Looking for a location?**
- Use **Location search mode**
- Check document metadata for locations mentioned

**Looking for specific dates?**
- Use **Date Range filter**
- Check timeline views in Person Profiles

**Looking for evidence?**
- Filter by **Category** → "Evidence Photo" or "Evidence List"
- Check **Document Type** → "Image-based" for scanned evidence

### Advanced Research

**Cross-referencing**:
1. Search for a person → note their case numbers
2. Search by case number → find all related documents
3. Check Related Documents for additional connections

**Export for Analysis**:
1. Set up your filters (e.g., "flight logs + 1990s + high quality")
2. Export to CSV
3. Open in Excel/Google Sheets for sorting, filtering, pivot tables

**Bookmarking Key Searches**:
- Use browser bookmarks to save important search URLs
- Share links with colleagues for collaborative research

## Troubleshooting

**Search returns no results**:
- Check spelling (fuzzy search helps but isn't perfect)
- Try different search modes (person vs. full text)
- Remove some filters - you may be too restrictive

**PDF won't load**:
- Check your internet connection
- Some PDFs are large (10+ MB) and may take time
- Try refreshing the page
- Report persistent issues on GitHub

**Filters not working**:
- Clear browser cache
- Try a different browser
- Report persistent issues on GitHub

**Mobile issues**:
- Try requesting desktop site if filters don't respond
- Ensure JavaScript is enabled
- Update your browser to the latest version

## Source Information

All documents are from official U.S. federal government sources or official court releases:

- DOJ Epstein Library (Department of Justice)
- FBI disclosures
- Court filings and memoranda

See the **Sources** page for the complete list and status of upstream sources.

## Privacy & Offline Use

- **No tracking**: This site does not collect analytics or user data
- **Client-side search**: All searching happens in your browser (no server queries)
- **Offline capable**: Once loaded, the search index works offline
- **Shareable links**: URLs encode search state but don't contain personal data

## Reporting Issues

Found a bug? Have a suggestion?

- **GitHub Issues**: [https://github.com/kleinpanic/The-Stein-Files/issues](https://github.com/kleinpanic/The-Stein-Files/issues)
- **Email**: Contact via GitHub profile

Please include:
- What you were trying to do
- What happened vs. what you expected
- Browser and device information
- Screenshots if applicable

---

**Last updated**: February 2026
**Version**: 1.5.0+ (Phase 2-3 features)
