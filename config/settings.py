"""Shared application limits and local configuration loading."""

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=False)

APP_TITLE = "SourceSpark"
# This ceiling bounds a single response, never the accumulated topic library.
MAX_BATCH_TOPICS = 10
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_CAMPAIGN_BYTES = 50 * 1024 * 1024
MAX_DOCUMENTS = 20
TABLE_PREVIEW_ROWS = 100
MAX_CONTEXT_CHARACTERS = 400_000
API_TIMEOUT_SECONDS = 60
MAX_API_RETRIES = 1
MAX_WORKSPACE_BYTES = 20 * 1024 * 1024
# Snapshot parsing guard; this is not a campaign target or generation batch cap.
MAX_SAVED_TOPICS = 10_000
MAX_ARCHIVE_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_TABLE_CELLS = 1_000_000

# Provider credentials stay local; their models are tried only on explicit generation actions.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.8-flash").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

# Groq's documented GPT-OSS 120B context/output limits; no truncation is permitted.
GROQ_CONTEXT_TOKENS = 131_072
GROQ_MAX_OUTPUT_TOKENS = 65_536
MAX_PROVIDER_RESPONSE_BYTES = 2 * 1024 * 1024
