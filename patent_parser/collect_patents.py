import time
import random

from pathlib import Path

import requests
import pandas as pd

from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_pdf_link(
    query: str,
    headers: dict[str, str] = HEADERS,
    n_retries: int = 3,
    backoff_factor: float = 0.3,
) -> str | dict:
    """Get link to patent pdf from google patents"""

    session = requests.Session()
    retry_strategy = Retry(
        total=n_retries,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        backoff_factor=backoff_factor,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    query = query.replace("-", "")

    url = f"https://patents.google.com/patent/{query}/en?oq={query}"

    resp = session.get(url, headers=headers)
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, "html.parser")
        tag = soup.find("meta", attrs={"name": "citation_pdf_url"})
        return tag["content"] if tag else {"error": "pdf_url not found"}
    else:
        return {"error": resp.status_code}


def download_pdf(
    url: str,
    folder: Path,
    headers: dict[str, str] = HEADERS,
) -> str | dict[str, str]:
    """Download pdf"""

    try:
        print(url)
        filename = folder / Path(url).name

        response = requests.get(url, headers=headers, stream=True, timeout=15)
        if response.status_code == 200:
            with filename.open("wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
            print(f"success: downloaded to {filename}")
            return "success"
        else:
            print({"error": response.status_code, "filename": filename})
            return {"error": response.status_code}
    except requests.RequestException as e:
        print({"error": e})
        return {"error": e}


def collect_pdf_links(
    checkpoints_folder: Path,
):
    """Parse patent pdf links"""

    comp_with_patent_info_df_path = Path(
        checkpoints_folder, "preprocessing", "comp_with_patent_info.tsv"
    )

    pdf_links_checkpoints_folder = Path(checkpoints_folder, "pdf_links")
    pdf_links_checkpoints_folder.mkdir(exist_ok=True, parents=True)

    df = pd.read_csv(
        comp_with_patent_info_df_path,
        sep="\t",
    )

    link_mapping_list = []

    for patent_number in df["patent_number"].unique():
        pdf_link = get_pdf_link(patent_number)
        link_mapping_list.append({"patent_number": patent_number, "pdf_link": pdf_link})
        time.sleep(random.uniform(0, 1))

    links_to_pdf = pd.DataFrame(link_mapping_list)
    links_to_pdf.to_csv(
        Path(pdf_links_checkpoints_folder, "links_to_pdf.tsv"), sep="\t", index=False
    )

    return links_to_pdf


def download_patent_data(links_to_pdf: pd.DataFrame, checkpoints_folder: Path):
    """Download patent pdf"""
    patent_pdf_folder = Path(checkpoints_folder, "patent_pdfs")
    patent_pdf_folder.mkdir(exist_ok=True, parents=True)

    pdf_links_checkpoints_folder = Path(checkpoints_folder, "pdf_links")
    pdf_links_checkpoints_folder.mkdir(exist_ok=True, parents=True)

    flattened_links_to_pdf = links_to_pdf.to_dict(orient="index")
    link_mapping_list = [d for d in flattened_links_to_pdf.values()]

    link_download_list = []

    for link_data in link_mapping_list:
        link = link_data["pdf_link"]
        patent_number = link_data["patent_number"]

        if "error" in link or isinstance(link, dict):
            link_download_list.append(
                {
                    "patent_number": patent_number,
                    "pdf_link": link,
                    "download_status": '{"error": "pdf_url not found"}',
                }
            )
        else:
            link_download_list.append(
                {
                    "patent_number": patent_number,
                    "pdf_link": link,
                    "download_status": download_pdf(link, patent_pdf_folder),
                }
            )
        time.sleep(random.uniform(2, 3))

    links_to_pdf_with_download_status = pd.DataFrame(link_download_list)

    links_to_pdf_with_download_status.to_csv(
        Path(pdf_links_checkpoints_folder, "links_to_pdf_with_download_status.tsv"),
        sep="\t",
        index=False,
    )
