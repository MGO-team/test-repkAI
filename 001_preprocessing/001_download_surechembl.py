from utils import download_ftp_files

if __name__ == "__main__":
    ftp_index_url = (
        "https://ftp.ebi.ac.uk/pub/databases/chembl/SureChEMBL/bulk_data/latest/"
    )
    output_dir = "/home/alex/dev/test-repkAI/data/SureChEMBL"
    results = download_ftp_files(ftp_index_url, output_dir)
    print("Summary:", results)
