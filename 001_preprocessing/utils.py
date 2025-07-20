from pathlib import Path
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def download_ftp_files(ftp_index_url: str, output_dir: Path, include_exts=None):
    """Download sure"""
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
