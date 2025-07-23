import asyncio
import logging


from pathlib import Path


from config_logging import setup_logging
from preprocessing import run_preprocessing, download_ftp_files
from collect_patents import collect_pdf_links, download_patent_data
from parse_pdfs import parse_pdfs
from run_binding_markup import run_markup
from run_binding_markup_async import run_markup_async
from utils import batch_list


from config import (
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
    USE_PARALLEL,
    BATCH_SIZE,
    USE_DOWNLOADED_PATENTS
)


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    if not USE_DOWNLOADED_PATENTS:
        if DOWNLOAD_CHEMBL:
            logger.info("Downloading ChEMBL...")
            download_res_ChEMBL = download_ftp_files(CHEMBL_URL, CHEMBL_FOLDER)
            logger.info(download_res_ChEMBL)
        else:
            logger.info("Skipping ChEMBL download...")

        if DOWNLOAD_SURE_CHEMBL:
            logger.info("Downloading SureChEMBL...")
            download_res_SureChEMBL = download_ftp_files(
                SURE_CHEMBL_URL, SURE_CHEMBL_FOLDER
            )
            logger.info(download_res_SureChEMBL)
        else:
            logger.info("Skipping SureChEMBL download...")

        logger.info("Starting preprocessing...")
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
    else:
        logger.info("Skipping downloading and preprocessing based on config...")

    

    if not USE_DOWNLOADED_PATENTS:
        logger.info("Collecting pdf links...")
        links_to_pdf = collect_pdf_links(CHECKPOINTS_FOLDER)
        logger.info("Downloading patents pdfs...")
        download_patent_data(links_to_pdf, CHECKPOINTS_FOLDER)
    else:
        logger.info("Skipping patent PDF downloading based on config...")

    logger.info("Processing pdfs and marking regions of interest...")

    pdf_dir = Path(CHECKPOINTS_FOLDER, "patent_pdfs")
    all_pdf_files = list(pdf_dir.glob("*.pdf"))

    pdf_batches = list(batch_list(all_pdf_files, BATCH_SIZE))
    total_batches = len(pdf_batches)

    if USE_PARALLEL:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        for idx, batch in enumerate(pdf_batches, start=1):
            logger.info(f"Processing batch {idx}/{total_batches} ({len(batch)} PDFs)")

            patents_batch = parse_pdfs(batch)
            logger.info(f"  Parsed {len(patents_batch)} patents")

            logger.info(f"  Marking regions of interest for batch {idx}")
            if not USE_PARALLEL:
                run_markup(patents=patents_batch, CHECKPOINTS_FOLDER=CHECKPOINTS_FOLDER)
            else:
                loop.run_until_complete(run_markup_async(patents=patents_batch, checkpoints_folder=CHECKPOINTS_FOLDER))
    finally:
        if USE_PARALLEL:
            loop.close()


    logger.info("Finished parsing!")

if __name__ == "__main__":
    main()
