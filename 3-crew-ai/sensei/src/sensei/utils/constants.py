"""Application-wide constants for Sensei."""

from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
COURSES_DIR = DATA_DIR / "courses"
DATABASE_PATH = DATA_DIR / "sensei.db"
USER_PREFERENCES_PATH = DATA_DIR / "user_preferences.json"
CHAT_HISTORY_PATH = DATA_DIR / "chat_history.json"

# Defaults
DEFAULT_SESSION_LENGTH = 30  # minutes
DEFAULT_QUIZ_QUESTIONS = 5  # questions per quiz

# Thresholds
QUIZ_PASS_THRESHOLD = 0.8  # 80% to pass

# Limits
MAX_THREADS_PER_BLOCK = 1024  # Example from CUDA course
MAX_CHAT_HISTORY = 50  # messages to keep in memory
