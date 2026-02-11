#!/usr/bin/env python3
"""
Enumeration-based ingestion for DOJ Epstein files.

Instead of scraping HTML discovery pages (which only finds 0.3% of files),
this script directly enumerates EFTA file numbers and downloads them.

Strategy:
- DataSets are numbered 1-100 (potentially more)
- EFTA files are numbered EFTA00000001 to EFTA02731659+ (2.7M+ files)
- Each DataSet contains ~100K files (varies)
- Direct URL pattern: /files/DataSet%20{n}/EFTA{:08d}.pdf

Usage:
    python -m scripts.ingest_enumerate --datasets 1-5 --test      # Test mode
    python -m scripts.ingest_enumerate --datasets 1-10            # Real download
    python -m scripts.ingest_enumerate --datasets 1-100 --parallel 8  # Full ingestion
"""

import argparse
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Iterator
from urllib.parse import quote

import requests
from tqdm import tqdm

# Constants
BASE_URL = "https://www.justice.gov/epstein"
DATASET_PATTERN = "files/DataSet%20{dataset}/EFTA{efta_num:08d}.pdf"
EFTA_RANGE = (1, 2731659)  # Known range from investigation
CHUNK_SIZE = 10000  # Check 10K files per chunk
RETRY_LIMIT = 3
TIMEOUT = 30

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class DownloadTask:
    """A single file download task."""
    dataset: int
    efta_num: int
    url: str
    output_path: Path
    
    def __str__(self):
        return f"DataSet {self.dataset}, EFTA{self.efta_num:08d}"


class EnumerationIngester:
    """Enumerate and download all EFTA files by direct URL probing."""
    
    def __init__(
        self,
        output_dir: Path,
        test_mode: bool = False,
        max_workers: int = 4,
        chunk_size: int = CHUNK_SIZE
    ):
        self.output_dir = output_dir
        self.test_mode = test_mode
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Research Archive Bot)'
        })
        
        # Statistics
        self.stats = {
            'checked': 0,
            'found': 0,
            'downloaded': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # State file for resumption
        self.state_file = self.output_dir / 'ingest_state.json'
        self.state = self._load_state()
    
    def _load_state(self) -> dict:
        """Load previous ingestion state for resumption."""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {'completed_datasets': [], 'last_efta': 0}
    
    def _save_state(self):
        """Save current ingestion state."""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def build_url(self, dataset: int, efta_num: int) -> str:
        """Build direct URL for EFTA file."""
        path = DATASET_PATTERN.format(dataset=dataset, efta_num=efta_num)
        return f"{BASE_URL}/{path}"
    
    def check_file_exists(self, url: str) -> bool:
        """Check if file exists via HEAD request."""
        try:
            response = self.session.head(url, timeout=TIMEOUT, allow_redirects=True)
            return response.status_code == 200
        except requests.RequestException as e:
            logger.debug(f"HEAD request failed for {url}: {e}")
            return False
    
    def download_file(self, task: DownloadTask) -> bool:
        """Download a single file."""
        if task.output_path.exists():
            logger.debug(f"Skipping existing file: {task.output_path.name}")
            self.stats['skipped'] += 1
            return True
        
        if self.test_mode:
            # In test mode, just check existence
            exists = self.check_file_exists(task.url)
            if exists:
                self.stats['found'] += 1
                logger.info(f"✓ Found: {task}")
            return exists
        
        # Real download
        for attempt in range(RETRY_LIMIT):
            try:
                response = self.session.get(task.url, timeout=TIMEOUT, stream=True)
                
                if response.status_code == 200:
                    # Download to temp file, then rename (atomic)
                    temp_path = task.output_path.with_suffix('.pdf.tmp')
                    
                    with open(temp_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    temp_path.rename(task.output_path)
                    self.stats['downloaded'] += 1
                    logger.info(f"✓ Downloaded: {task}")
                    return True
                
                elif response.status_code == 404:
                    # File doesn't exist, not an error
                    return False
                
                else:
                    logger.warning(f"HTTP {response.status_code} for {task} (attempt {attempt+1})")
                    
            except requests.RequestException as e:
                logger.warning(f"Download failed for {task} (attempt {attempt+1}): {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
        
        self.stats['failed'] += 1
        logger.error(f"✗ Failed after {RETRY_LIMIT} attempts: {task}")
        return False
    
    def enumerate_dataset(self, dataset: int) -> Iterator[DownloadTask]:
        """Enumerate all files in a dataset."""
        logger.info(f"Enumerating DataSet {dataset}...")
        
        # Estimate range based on dataset number
        # Rough heuristic: 100K files per dataset
        start_efta = (dataset - 1) * 100000 + 1
        end_efta = min(dataset * 100000, EFTA_RANGE[1])
        
        for efta_num in range(start_efta, end_efta + 1):
            url = self.build_url(dataset, efta_num)
            output_path = self.output_dir / f"DataSet{dataset:02d}" / f"EFTA{efta_num:08d}.pdf"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            yield DownloadTask(
                dataset=dataset,
                efta_num=efta_num,
                url=url,
                output_path=output_path
            )
    
    def scan_dataset_range(self, dataset: int, start: int, end: int) -> list[int]:
        """
        Binary search-like scan to find which files exist in a range.
        Returns list of EFTA numbers that exist.
        """
        # Sample the range with binary search to find boundaries
        found_files = []
        
        # Quick sampling to find rough boundaries
        samples = [start, (start + end) // 2, end]
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for efta_num in samples:
                url = self.build_url(dataset, efta_num)
                future = executor.submit(self.check_file_exists, url)
                futures[future] = efta_num
            
            for future in as_completed(futures):
                efta_num = futures[future]
                if future.result():
                    found_files.append(efta_num)
                self.stats['checked'] += 1
        
        if not found_files:
            logger.info(f"  DataSet {dataset}: No files found in range {start}-{end}")
            return []
        
        logger.info(f"  DataSet {dataset}: Found files at {found_files}")
        
        # If we found files, enumerate the full range
        # (This is simplified; a production version would binary search boundaries)
        min_found = min(found_files)
        max_found = max(found_files)
        
        return list(range(min_found, max_found + 1))
    
    def ingest_dataset(self, dataset: int):
        """Ingest all files from a dataset."""
        if dataset in self.state['completed_datasets']:
            logger.info(f"Skipping already completed DataSet {dataset}")
            return
        
        logger.info(f"=== DataSet {dataset} ===")
        
        # First, do a quick scan to find the actual file range
        start_efta = (dataset - 1) * 100000 + 1
        end_efta = min(dataset * 100000, EFTA_RANGE[1])
        
        efta_range = self.scan_dataset_range(dataset, start_efta, end_efta)
        
        if not efta_range:
            logger.info(f"DataSet {dataset}: No files found, skipping")
            self.state['completed_datasets'].append(dataset)
            self._save_state()
            return
        
        # Now download all files in the found range
        tasks = [
            DownloadTask(
                dataset=dataset,
                efta_num=efta_num,
                url=self.build_url(dataset, efta_num),
                output_path=self.output_dir / f"DataSet{dataset:02d}" / f"EFTA{efta_num:08d}.pdf"
            )
            for efta_num in efta_range
        ]
        
        logger.info(f"DataSet {dataset}: Downloading {len(tasks)} files...")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.download_file, task): task for task in tasks}
            
            with tqdm(total=len(tasks), desc=f"DataSet {dataset}") as pbar:
                for future in as_completed(futures):
                    future.result()
                    pbar.update(1)
        
        # Mark dataset as complete
        self.state['completed_datasets'].append(dataset)
        self._save_state()
        
        logger.info(f"DataSet {dataset} complete. Stats: {self.stats}")
    
    def ingest_datasets(self, dataset_range: range):
        """Ingest multiple datasets."""
        logger.info(f"Starting ingestion for DataSets {dataset_range.start}-{dataset_range.stop-1}")
        logger.info(f"Mode: {'TEST' if self.test_mode else 'DOWNLOAD'}")
        logger.info(f"Workers: {self.max_workers}")
        logger.info(f"Output: {self.output_dir}")
        
        for dataset in dataset_range:
            self.ingest_dataset(dataset)
        
        logger.info("=== Ingestion Complete ===")
        logger.info(f"Checked: {self.stats['checked']}")
        logger.info(f"Found: {self.stats['found']}")
        logger.info(f"Downloaded: {self.stats['downloaded']}")
        logger.info(f"Skipped: {self.stats['skipped']}")
        logger.info(f"Failed: {self.stats['failed']}")


def parse_range(range_str: str) -> range:
    """Parse dataset range string like '1-5' into range object."""
    if '-' not in range_str:
        n = int(range_str)
        return range(n, n+1)
    
    start, end = map(int, range_str.split('-'))
    return range(start, end+1)


def main():
    parser = argparse.ArgumentParser(description='Enumerate and download DOJ Epstein files')
    parser.add_argument('--datasets', type=str, required=True,
                       help='Dataset range (e.g., "1-5" or "1-100")')
    parser.add_argument('--output', type=Path, default=Path('data/raw/pdfs'),
                       help='Output directory for PDFs')
    parser.add_argument('--test', action='store_true',
                       help='Test mode: check existence only, no download')
    parser.add_argument('--parallel', type=int, default=4,
                       help='Number of parallel downloads (default: 4)')
    parser.add_argument('--chunk-size', type=int, default=CHUNK_SIZE,
                       help=f'Files to check per chunk (default: {CHUNK_SIZE})')
    
    args = parser.parse_args()
    
    try:
        dataset_range = parse_range(args.datasets)
    except ValueError:
        logger.error(f"Invalid dataset range: {args.datasets}")
        sys.exit(1)
    
    ingester = EnumerationIngester(
        output_dir=args.output,
        test_mode=args.test,
        max_workers=args.parallel,
        chunk_size=args.chunk_size
    )
    
    ingester.ingest_datasets(dataset_range)


if __name__ == '__main__':
    main()
