# File: llm_config.py
import os
from google import genai
from dotenv import load_dotenv
from pathlib import Path
import chromadb

# 1. Load environment variables (optional, but good practice)
load_dotenv()


# 2. Initialize the Client ONCE
print("🔌 Initializing Gemini Client...")
client = genai.Client()

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection(name="financial_reports")

# 3. (Optional) Define standardized model names here too
# This makes it easy to upgrade to "gemini-3.0" later in just one place
EMBEDDING_MODEL = "gemini-embedding-001"
REASONING_MODEL = "gemini-2.5-flash"
BASE_PDF_PATH = Path('data/pdf')
BASE_CORPUS_PATH = Path('data/corpus')
BASE_CHUNKS_PATH = Path('data/chunks')