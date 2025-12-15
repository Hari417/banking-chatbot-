"""Configuration settings for the banking chatbot."""
import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key-here")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))

# Vector DB Configuration
VECTOR_DB_PERSIST_DIR = os.getenv("VECTOR_DB_PERSIST_DIR", "./vectordb")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")

# API Configuration
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"

# Banking API Configuration (Mock for demo)
BANK_API_BASE_URL = os.getenv("BANK_API_BASE_URL", "http://localhost:8000")
BANK_API_TIMEOUT = int(os.getenv("BANK_API_TIMEOUT", "10"))
