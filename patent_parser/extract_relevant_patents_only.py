import logging

from preprocessing import extract_patents_only
from config import (
    DATA_FOLDER,
    PATENTS_PQ,
    SEED,
    USE_RANDOM_CHUNKS,
    N_RANDOM_CHUNKS,
    N_RANDOM_PATENTS,
)

logger = logging.getLogger(__name__)

logger.info("Starting processing...")
for chunk in range(0, 1000):
    extract_patents_only(
        chunks=[chunk],
        checkpoints=f"{DATA_FOLDER}/patents_only/checkpoints_chunk_{chunk}",
        patents_pq_file=PATENTS_PQ,
        seed=SEED,
        use_random_chunks=USE_RANDOM_CHUNKS,
        n_random_chuncks=N_RANDOM_CHUNKS,
        n_random_patents=N_RANDOM_PATENTS,
    )
