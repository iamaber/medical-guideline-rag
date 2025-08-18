import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = "gemini-2.0-flash"
NCBI_EMAIL = os.getenv("NCBI_EMAIL")
NCBI_API_KEY = os.getenv("NCBI_API_KEY")
JINA_API_KEY = os.getenv("JINA_API_KEY")

# Application Settings
MAX_MEDICATIONS = 10
DEFAULT_SEARCH_RESULTS = 5
CACHE_EXPIRY_HOURS = 24
API_PORT = 8000
UI_PORT = 8501

# File Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
DRUG_DB_PATH = DATA_DIR / "drug_db" / "medex_URL.json"
RAW_DATA_DIR = DATA_DIR / "raw"

# Vector Search Settings
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_SEARCH_TOP_K = 5
FAISS_INDEX_PATH = DATA_DIR / "vector_index.faiss"
DOCUMENTS_METADATA_PATH = DATA_DIR / "documents_metadata.json"

# Scraping Settings
JINA_BASE_URL = "https://r.jina.ai/"
REQUEST_TIMEOUT = 30
SCRAPING_DELAY = 1.0

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
