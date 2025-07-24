"""This file will contain all configs for patent parser"""

from pathlib import Path

# Paths
DATA_FOLDER = "data"
CHECKPOINTS_FOLDER = Path(
    DATA_FOLDER, "/home/alex/dev/test-repkAI/data/checkpoints_random_1234567"
)

# Set up pdf reading
INITIAL_PDF_CHUNK_SIZE = 3000 # size of a chunk in symbols
MIN_PDF_TEXT_LENGTH = INITIAL_PDF_CHUNK_SIZE
CHUNK_OVERLAPS = 5

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
SEED = 1234567
USE_RANDOM_CHUNKS = True
N_RANDOM_CHUNKS = 1
N_RANDOM_PATENTS = 10

### Use defined chunks
CHUNKS: list[int] | None = []

# Patent retrieval
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Requests LLM
MAX_CONCURRENT_REQUESTS = 6
USE_PARALLEL = True
BATCH_SIZE = 20

# AI agent
AGENT_TIMEOUT = 1000

LOG_DIR = Path(__file__).parent.parent / "logs"

STEPS = [
    "download_chembl",
    "download_surechembl",
    "preprocessing",
    "collect_pdf_links",
    "download_patents",
    "parse_and_markup",
    "extract_patents_with_binding",
]

CONTINUE_MARKUP = True
