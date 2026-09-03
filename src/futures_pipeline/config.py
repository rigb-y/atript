from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
import os

PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DATA_DIR: Path = DATA_DIR / "raw" 
PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
FORECAST_DATA_DIR: Path = DATA_DIR / "forecasts"
MODEL_DIR: Path = PROJECT_ROOT / "models"


@dataclass
class Settings:
    massive_api_key: str
    hf_token: str
    default_resolution: str = "15min"
    request_limit: int  = 100
    # The number of prior observations needed to compute the indicators for new data.
    indicator_lookback: int = 14

def load_settings() -> Settings:
    load_dotenv()

    massive_key = os.getenv("MASSIVE_API_KEY")
    if (not massive_key):
        raise RuntimeError("MASSIVE_API_KEY environment variable is not set.")

    hf_token: str | None = os.getenv("HF_TOKEN")
    if (not hf_token):
        raise RuntimeError("HF_TOKEN environment variable is not set.")

    return Settings(massive_api_key=massive_key, hf_token=hf_token)


