import os
from typing import List

# Relative candidate locations (project_root will be appended by helper)
INPUT_FILE_RELATIVE: List[str] = [
    "output/kaggle_output.csv",
    "../../output/kaggle_output.csv",
]

def build_possible_input_paths(project_root: str) -> List[str]:
    """Return list of possible input file paths to check for kaggle_output.csv."""
    paths = INPUT_FILE_RELATIVE.copy()
    paths.append(os.path.join(project_root, "output", "kaggle_output.csv"))
    return paths

# Defaults used by the scraper
DEFAULT_WAIT_SECONDS: float = 3.0
DEFAULT_DELAY: float = 1.0
OUTPUT_JSON_NAME: str = "kaggle_metadata.json"
OUTPUT_CSV_NAME: str = "kaggle_metadata.csv"

# Minimal messages (can be overridden by caller if needed)
START_MESSAGE: str = "Kaggle Metadata Scraper: starting"
NOT_FOUND_MESSAGE: str = "Error: Input file 'kaggle_output.csv' not found. Checked locations:"

# Driver options (simple flags)
DRIVER_HEADLESS: bool = True
