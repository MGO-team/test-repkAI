import requests

def get_uniprot_fasta_by_gene(gene_name):

    query_url = "https://rest.uniprot.org/uniprotkb/search"
    query = f"(gene_exact:{gene_name}) AND (organism_name:Homo sapiens) AND reviewed:true"
    params = {"query": query, "format": "json", "size": 1, "fields": "accession"}
    r = requests.get(query_url, params=params)

    if not r.ok or not r.json()["results"]:
        raise RuntimeError(f"Accession not found for gene {gene_name}")

    accession = r.json()["results"][0]["primaryAccession"]

    fasta_url = f"https://rest.uniprot.org/uniprotkb/{accession}.fasta"
    fasta_r = requests.get(fasta_url)

    if not fasta_r.ok:
        raise RuntimeError(f"Failed to fetch FASTA for accession {accession}")

    return fasta_r.text