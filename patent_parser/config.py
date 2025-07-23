"""This file will contain all configs for patent parser"""

from pathlib import Path

# Paths
DATA_FOLDER = "data"
CHECKPOINTS_FOLDER = Path(DATA_FOLDER, "checkpoints_random_dev_check")

# Set up pdf reading
INITIAL_PDF_CHUNK_SIZE = 3000
CHUNK_OVERLAPS = 2

CHEMBL_FOLDER = Path(DATA_FOLDER, "ChEMBL")
SURE_CHEMBL_FOLDER = Path(DATA_FOLDER, "SureChEMBL")

PC_MAP_PQ = Path(SURE_CHEMBL_FOLDER, "patent_compound_map.parquet")
COMPOUNDS_PQ = Path(SURE_CHEMBL_FOLDER, "compounds.parquet")
PATENTS_PQ = Path(SURE_CHEMBL_FOLDER, "patents.parquet")

# URLs
CHEMBL_URL = "https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/"
SURE_CHEMBL_URL = (
    "https://ftp.ebi.ac.uk/pub/databases/chembl/SureChEMBL/bulk_data/latest/"
)

# DB params
DOWNLOAD_CHEMBL = False
DOWNLOAD_SURE_CHEMBL = True

# Preprocessing
### Set random subsample
SEED = 123
USE_RANDOM_CHUNKS = True
N_RANDOM_CHUNKS = 3
N_RANDOM_PATENTS = 10

### Use defined chunks
CHUNKS: list[int] | None = []

# Patent retrieval
HEADERS = {"User-Agent": "Mozilla/5.0"}


LOG_DIR = Path(__file__).parent.parent / "logs"
