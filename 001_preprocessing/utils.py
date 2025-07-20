from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def download_ftp_files(ftp_index_url: str, output_dir: Path, include_exts=None):
    """Download all files from ftp recursively"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching index: {ftp_index_url}")
    resp = requests.get(ftp_index_url)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Collect candidate file links
    anchors = soup.find_all("a")
    downloaded = []
    skipped_existing = []
    skipped_filtered = []

    for a in anchors:
        href = a.get("href")
        if not href:
            continue

        # Skip query links, parent dirs, or subdirs (href ending with '/')
        if href.startswith("?") or href.endswith("/"):
            continue

        # Full URL to the file
        file_url = urljoin(ftp_index_url, href)

        # Derive a clean filename from the last path component
        filename = Path(href).name  # handles cases like "subdir/file.txt"
        if not filename:
            continue

        # Extension filter (if provided)
        if include_exts is not None:
            ext = Path(filename).suffix.lower()
            if ext not in include_exts:
                skipped_filtered.append(filename)
                continue

        dest_path = output_dir / filename

        if dest_path.exists():
            print(f"Skipping existing file: {filename}")
            skipped_existing.append(filename)
            continue

        print(f"Downloading: {filename}")
        with requests.get(file_url, stream=True) as r:
            r.raise_for_status()
            with dest_path.open("wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        print(f"Saved to: {dest_path}")
        downloaded.append(filename)

    return {
        "downloaded": downloaded,
        "skipped_existing": skipped_existing,
        "skipped_filtered": skipped_filtered,
    }


def extract_relevant_patents_from_pq(
    path_to_parquet: str,
    random_chunks: list[int] | None = None,
) -> pd.DataFrame:
    """Function to automatically read data from parquet. Supports random chunks subsets"""
    pf = pq.ParquetFile(path_to_parquet)
    dfs = []
    if random_chunks is not None:
        chunks = random_chunks
    else:
        chunks = range(pf.num_row_groups)

    for i in chunks:
        chunk = pf.read_row_group(
            i,
        ).to_pandas()
        mask = chunk["ipc"].astype(str).str.contains(
            "A61K|A61P", regex=True, na=False
        ) | chunk["cpc"].astype(str).str.contains("A61K|A61P", regex=True, na=False)
        chm = chunk[mask]
        dfs.append(chm)
        print(f"chunk{i}, mask_len={len(chm)}, dfs={len(dfs)}")

    return pd.concat(dfs, ignore_index=True)
