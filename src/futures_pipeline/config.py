from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
import os

PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw" 
PROCESSED_DATA_DIR = DATA_DIR / "processed"
FORECAST_DATA_DIR = DATA_DIR / "forecasts"

@dataclass
class Settings:
    massive_api_key: str
    default_resolution: str = "15min"
    request_limit: int  = 100
    # The number of prior observations needed to compute the indicators for new data.
    indicator_lookback: int = 14

def load_settings() -> Settings:
    load_dotenv()
    api_key = os.getenv("MASSIVE_API_KEY")
    if (not api_key):
        raise RuntimeError("MASSIVE_API_KEY environment variable is not set.")
    return Settings(massive_api_key=api_key)


