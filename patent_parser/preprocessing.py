import random

from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class ChunksUsageError(Exception):
    pass


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


def extract_relevant_patents(
    path_to_parquet: str,
    random_chunks: list[int] | None = None,
) -> pd.DataFrame:
    """Function to automatically read and filter relevant data from parquet. Supports random chunks subsets"""
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


def extract_compound_ids_by_patent(
    path_to_parquet: str,
    target_patent_ids: list[int],
) -> dict[int, list[int]]:
    """Function to automatically read and filter relevant compound_ids from parquet"""
    pf = pq.ParquetFile(path_to_parquet)
    patent_id_set = set(target_patent_ids)
    dfs = []

    chunks = range(pf.num_row_groups)

    for i in chunks:
        chunk = pf.read_row_group(i, columns=["patent_id", "compound_id"])
        df = chunk.to_pandas()

        filtered = df[df["patent_id"].isin(patent_id_set)]
        if len(filtered) > 0:
            print(f"chunk{i}, mask_len={len(filtered)}, dfs={len(dfs)}")
            dfs.append(filtered)

    return pd.concat(dfs, ignore_index=True)


def extract_compounds_by_ids(
    path_to_parquet: str,
    target_compound_ids: list[int],
) -> dict[int, list[int]]:
    """Function to automatically read and filter relevant compounds from parquet"""

    pf = pq.ParquetFile(path_to_parquet)
    compounds_id_set = set(target_compound_ids)
    dfs = []

    chunks = range(pf.num_row_groups)

    for i in chunks:
        chunk = pf.read_row_group(i)
        df = chunk.to_pandas()

        filtered = df[df["id"].isin(compounds_id_set)]
        if len(filtered) > 0:
            print(f"chunk{i}, mask_len={len(filtered)}, dfs={len(dfs)}")
            dfs.append(filtered)

    return pd.concat(dfs, ignore_index=True)


def run_preprocessing(
    chunks: list[int] | None,
    patent_compound_map_pq_file: Path,
    compounds_pq_file: Path,
    checkpoints: Path,
    patents_pq_file: Path,
    seed: int,
    use_random_chunks: bool,
    n_random_chuncks: int,
    n_random_patents: int,
) -> None:
    print("Preprocessing params:")
    print(locals())

    preprocessing_checkpoints = Path(checkpoints, "preprocessing")
    preprocessing_checkpoints.mkdir(exist_ok=True, parents=True)

    if (not chunks or chunks is None) and use_random_chunks:
        will_use_random_chuncks = True
        random.seed(seed)
        n_random_chunks = n_random_chuncks
        chunks = [random.randint(1, 200) for _ in range(n_random_chunks)]
        print(f"Will use random chunks: {chunks}")
    elif (chunks and chunks is not None) and not use_random_chunks:
        will_use_random_chuncks = False
        print(f"Will use provided chunks: {chunks}")
    else:
        raise ChunksUsageError("Either do not provide chunks or do not use random")

    # Extract patents with codes
    patents = extract_relevant_patents(patents_pq_file, chunks)
    if will_use_random_chuncks:
        patents = patents.sample(n=n_random_patents, random_state=seed)
    patents.to_csv(
        Path(preprocessing_checkpoints, "patents_subset.tsv"), sep="\t", index=False
    )
    patents_id = patents.id.to_list()

    # Extract compound ids that match extracted patents
    compounds_id_df = extract_compound_ids_by_patent(
        patent_compound_map_pq_file, patents_id
    )
    compounds_id_df.to_csv(
        Path(preprocessing_checkpoints, "compounds_id_df.tsv"), sep="\t", index=False
    )
    compounds_id = compounds_id_df.compound_id.to_list()

    # Extract compounds themselves
    compounds = extract_compounds_by_ids(compounds_pq_file, compounds_id)
    compounds.to_csv(
        Path(preprocessing_checkpoints, "compounds.tsv"), sep="\t", index=False
    )

    # Merge results
    comp_with_pat = compounds.merge(
        compounds_id_df,
        left_on="id",
        right_on="compound_id",
        how="left",
    )
    comp_with_patent_info = comp_with_pat.merge(
        patents,
        left_on="patent_id",
        right_on="id",
        how="left",
        suffixes=("", "_pat"),
    )
    comp_with_patent_info = comp_with_patent_info.drop(
        ["compound_id", "id_pat"], axis=1
    ).rename(columns={"id": "compound_id"})

    comp_with_patent_info.to_csv(
        Path(preprocessing_checkpoints, "comp_with_patent_info.tsv"),
        sep="\t",
        index=False,
    )
