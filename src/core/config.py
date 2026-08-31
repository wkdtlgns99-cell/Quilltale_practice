"""
Core system configuration for Quilltale TRPG Engine.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
SAVES_DIR = DATA_DIR / "saves"
LEGACY_DIR = DATA_DIR / "legacy"
QDRANT_STORAGE_DIR = DATA_DIR / "qdrant_storage"
WORLDS_DIR = DATA_DIR / "worlds"
CHRONICLES_DIR = DATA_DIR / 'chronicles'
TEMPLATES_DIR = DATA_DIR / 'templates'

# Ensure directories exist
SAVES_DIR.mkdir(parents=True, exist_ok=True)
LEGACY_DIR.mkdir(parents=True, exist_ok=True)
QDRANT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
CHRONICLES_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

# LLM & Embedding configs
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-m3")
JINA_MODEL = os.getenv("JINA_MODEL", "jina-embeddings-v3")
JINA_API_KEY = os.getenv("JINA_API_KEY", "")
EMBEDDING_DIMENSION = 1024

# Vector DB configs
QDRANT_URL = os.getenv("QDRANT_URL", "")  # e.g. "http://localhost:6333" for Docker, empty for local disk
QDRANT_PATH = str(QDRANT_STORAGE_DIR) if not QDRANT_URL else None

# Game Master settings
MAX_RECENT_HISTORY = 5
MAX_RAG_MEMORIES = 4
DICE_BASE_DC = 12

# Balance & Stat Caps (Thresholds)
MAX_STAT_VALUE = 30
MIN_STAT_VALUE = 1
MAX_LEVELUP_STAT_GAIN = 2
MIN_LEVELUP_STAT_GAIN = 1

# Skill scaling
MIN_SKILL_SCALING = 0.5
MAX_SKILL_SCALING = 3.0

# Reputation
MIN_REPUTATION_DELTA = -25
MAX_REPUTATION_DELTA = 15
MIN_REPUTATION_TOTAL = -100
MAX_REPUTATION_TOTAL = 100

# Crit defaults
BASE_CRIT_RATE = 5.0      # percent
BASE_CRIT_DAMAGE = 150.0  # percent
CRIT_RATE_PER_POINT = 2.0
CRIT_DMG_PER_POINT = 5.0
LUCK_CRIT_BONUS = 0.5

# Equipment slots limits
MAX_RINGS = 20
MAX_EARRINGS = 8

# Incantation
BASE_INCANTATION_CHARS = 10   # base chars per turn
WISDOM_INCANT_BONUS = 1       # extra chars per wisdom point above 10
NO_INCANTATION_DAMAGE_MULT = 0.1  # 무영창 마법 위력은 본래의 1/10 (10%)

# Fatigue Settings
MAX_FATIGUE = 100
FATIGUE_TIRED_THRESHOLD = 50
FATIGUE_EXHAUSTED_THRESHOLD = 80

# Time Economy
TIME_TALK_MINUTES = 2
TIME_SEARCH_MINUTES = 20
TIME_COMBAT_BASE_MINUTES = 30
TIME_TRAVEL_MINUTES = 120

