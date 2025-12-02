import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required. Please set it in your .env file.")

# Model Configuration
OPENAI_MODEL = "gpt-4.1"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-large"

# Data directories
DATA_DIR = "./data"
UPLOAD_DIR = "./data/uploads"
CHROMA_DIR = "./data/chroma_db"
