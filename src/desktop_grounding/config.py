"""Central project configuration."""

from pathlib import Path


# Screen configuration
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 1.0

# API configuration
POSTS_API_URL = "https://jsonplaceholder.typicode.com/posts"
API_TIMEOUT_SECONDS = 10.0
POSTS_LIMIT = 10

# Output paths
OUTPUT_FOLDER_NAME = "tjm-project"
SCREENSHOTS_FOLDER_NAME = "screenshots"
RAW_SCREENSHOTS_FOLDER_NAME = "raw"
ANNOTATED_SCREENSHOTS_FOLDER_NAME = "annotated"

# Local project directories
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = PROJECT_ROOT / "assets"
TEMPLATES_DIR = ASSETS_DIR / "templates"

# Future vision thresholds
ICON_MATCH_CONFIDENCE_THRESHOLD = 0.85
OCR_MATCH_CONFIDENCE_THRESHOLD = 0.75
GROUNDING_CONFIDENCE_THRESHOLD = 0.80

# Future GUI timing
GUI_ACTION_DELAY_SECONDS = 0.25
WINDOW_LAUNCH_DELAY_SECONDS = 1.5
SAVE_DIALOG_DELAY_SECONDS = 0.5

# Gemini grounding configuration
ENABLE_GEMINI_GROUNDING = False
GEMINI_MODEL_NAME = "gemini-2.5-flash"
GEMINI_CONFIDENCE_THRESHOLD = 0.70
GEMINI_TIMEOUT_SECONDS = 10.0
GEMINI_RETRY_ATTEMPTS = 1
