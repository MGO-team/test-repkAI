import requests
import logging

logger = logging.getLogger(__name__)


def parse_fasta(fasta_string: str) -> tuple[str, str]:
    lines = fasta_string.strip().split("\n")
    header = lines[0][1:]
    sequence = "".join(lines[1:])
    return header, sequence


def get_uniprot_fasta_by_gene(
    protein_name: str, organism: str = "Homo sapiens"
) -> dict[str, str]:
    query_url = "https://rest.uniprot.org/uniprotkb/search"
    query = f'(protein_name:"{protein_name}") AND (organism_name:"{organism}") AND reviewed:true'
    params = {"query": query, "format": "json", "size": 1, "fields": "accession"}

    try:
        logger.info(f"Fetching protein {protein_name}")
        r = requests.get(query_url, params=params)

        if not r.ok or not r.json()["results"]:
            raise RuntimeError(
                f"Accession not found for gene {protein_name}, status_code: {r.status_code}"
            )

        accession = r.json()["results"][0]["primaryAccession"]

        fasta_url = f"https://rest.uniprot.org/uniprotkb/{accession}.fasta"
        fasta_r = requests.get(fasta_url)

        if not fasta_r.ok:
            raise RuntimeError(
                f"Failed to fetch FASTA for accession {accession}, status_code: {r.status_code}"
            )

        logger.info(f"success: {protein_name}")
        header, sequence = parse_fasta(fasta_r.text)
        return {"header": header, "sequence": sequence}

    except RuntimeError as e:
        logger.warning(f"Failed to fetch: {protein_name}")
        logger.warning(e)
        return {"error": e}
