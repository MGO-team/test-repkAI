from preprocessing import run_preprocessing, download_ftp_files

from config import (
    # DATA_FOLDER,
    CHECKPOINTS_FOLDER,
    CHEMBL_FOLDER,
    SURE_CHEMBL_FOLDER,
    PC_MAP_PQ,
    COMPOUNDS_PQ,
    PATENTS_PQ,
    CHEMBL_URL,
    SURE_CHEMBL_URL,
    DOWNLOAD_CHEMBL,
    DOWNLOAD_SURE_CHEMBL,
    SEED,
    USE_RANDOM_CHUNKS,
    N_RANDOM_CHUNKS,
    N_RANDOM_PATENTS,
    CHUNKS,
)


if DOWNLOAD_CHEMBL:
    print("Downloading ChEMBL...")
    download_res_ChEMBL = download_ftp_files(CHEMBL_URL, CHEMBL_FOLDER)
    print(download_res_ChEMBL)
else:
    print("Skipping ChEMBL download...")


if DOWNLOAD_SURE_CHEMBL:
    print("Downloading SureChEMBL...")
    download_res_SureChEMBL = download_ftp_files(SURE_CHEMBL_URL, SURE_CHEMBL_FOLDER)
    print(download_res_SureChEMBL)
else:
    print("Skipping SureChEMBL download...")

print("Starting preprocessing...")
run_preprocessing(
    chunks=CHUNKS,
    patent_compound_map_pq_file=PC_MAP_PQ,
    compounds_pq_file=COMPOUNDS_PQ,
    checkpoints=CHECKPOINTS_FOLDER,
    patents_pq_file=PATENTS_PQ,
    seed=SEED,
    use_random_chunks=USE_RANDOM_CHUNKS,
    n_random_chuncks=N_RANDOM_CHUNKS,
    n_random_patents=N_RANDOM_PATENTS,
)

print("Finished parsing!")
