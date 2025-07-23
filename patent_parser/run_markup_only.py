import logging
from pathlib import Path
from config_logging import setup_logging

# from preprocessing import run_preprocessing, download_ftp_files
# from collect_patents import collect_pdf_links, download_patent_data
# from parse_pdfs import parse_pdfs_in_dir
from run_binding_markup import run_markup
# from config import (
# DATA_FOLDER,
# CHECKPOINTS_FOLDER,
# CHEMBL_FOLDER,
# SURE_CHEMBL_FOLDER,
# PC_MAP_PQ,
# COMPOUNDS_PQ,
# PATENTS_PQ,
# CHEMBL_URL,
# SURE_CHEMBL_URL,
# DOWNLOAD_CHEMBL,
# DOWNLOAD_SURE_CHEMBL,
# SEED,
# USE_RANDOM_CHUNKS,
# N_RANDOM_CHUNKS,
# N_RANDOM_PATENTS,
# CHUNKS,
# HEADERS,
# )

CHECKPOINTS_FOLDER = Path("/home/alex/dev/test-repkAI/data/that_sample")


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    # if DOWNLOAD_CHEMBL:
    #     logger.info("Downloading ChEMBL...")
    #     download_res_ChEMBL = download_ftp_files(CHEMBL_URL, CHEMBL_FOLDER)
    #     logger.info(download_res_ChEMBL)
    # else:
    #     logger.info("Skipping ChEMBL download...")

    # if DOWNLOAD_SURE_CHEMBL:
    #     logger.info("Downloading SureChEMBL...")
    #     download_res_SureChEMBL = download_ftp_files(
    #         SURE_CHEMBL_URL, SURE_CHEMBL_FOLDER
    #     )
    #     logger.info(download_res_SureChEMBL)
    # else:
    #     logger.info("Skipping SureChEMBL download...")

    # logger.info("Starting preprocessing...")
    # run_preprocessing(
    #     chunks=CHUNKS,
    #     patent_compound_map_pq_file=PC_MAP_PQ,
    #     compounds_pq_file=COMPOUNDS_PQ,
    #     checkpoints=CHECKPOINTS_FOLDER,
    #     patents_pq_file=PATENTS_PQ,
    #     seed=SEED,
    #     use_random_chunks=USE_RANDOM_CHUNKS,
    #     n_random_chuncks=N_RANDOM_CHUNKS,
    #     n_random_patents=N_RANDOM_PATENTS,
    # )

    # logger.info("Collecting pdf links...")
    # links_to_pdf = collect_pdf_links(CHECKPOINTS_FOLDER)

    # logger.info("Downloading patents pdfs...")
    # download_patent_data(links_to_pdf, CHECKPOINTS_FOLDER)

    # logger.info("Reading pdfs...")
    # parse_pdfs_in_dir(
    #     Path(
    #         CHECKPOINTS_FOLDER,
    #         "patent_pdfs",
    #     )
    # )

    logger.info("Marking regions of interest...")
    run_markup(CHECKPOINTS_FOLDER)

    logger.info("Finished parsing!")


if __name__ == "__main__":
    main()
