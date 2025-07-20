from pathlib import Path

import requests
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
