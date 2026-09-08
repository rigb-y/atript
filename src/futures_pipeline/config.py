from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv
import os
from .typedefs import TradingFees
import tomlkit 
from tomlkit.exceptions import NonExistentKey
from tomlkit.items import Table
from collections.abc import Mapping


PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DATA_DIR: Path = DATA_DIR / "raw" 
PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
FORECAST_DATA_DIR: Path = DATA_DIR / "forecasts"
MODEL_DIR: Path = PROJECT_ROOT / "models"
CONFIG_FILE: Path = PROJECT_ROOT / "config.toml"


@dataclass(frozen=True)
class Defaults:
    resolution: str = "15min"
    target: str = "returns"
    pred_length: int = 24
    quantiles: list[float] = field(default_factory=lambda: [0.1,0.5,0.9])
    prediction_interval: tuple[float, float] = (0.1, 0.9)

@dataclass
class Settings:
    massive_api_key: str
    hf_token: str
    defaults: Defaults = Defaults()
    request_limit: int  = 100



def load_fees() -> TradingFees:
    with open(CONFIG_FILE, 'r') as f:
        config: tomlkit.TOMLDocument = tomlkit.load(f)
    trading_costs: Mapping = config.get("trading_costs", {})
    return TradingFees.model_validate(trading_costs) 
"""

"""

def store_fees(Fees: TradingFees) -> None:
    if (not CONFIG_FILE.exists()):
        raise RuntimeError("Attempted to call store_fees() when config.toml does not exist in project root. Run config.initialize_config().")

    with open(CONFIG_FILE, 'r') as f:
        config: tomlkit.TOMLDocument = tomlkit.load(f)
    table: Table = config.get("trading_costs", {})
    for type, amount in Fees.model_dump().items():
        if amount is not None:
            table[type] = amount

    with open(CONFIG_FILE, 'w') as f:
        tomlkit.dump(config, f)

def initialize_config(reset=False) -> None:
    config_file = Path(CONFIG_FILE) 

    if config_file.exists() and not reset: 
        return

    config_file.touch(exist_ok=True)

    doc = tomlkit.document()
    trading_costs = tomlkit.table()

    doc.add("trading_costs", trading_costs) 
    with config_file.open('w') as f:
        tomlkit.dump(doc, f)

def load_settings() -> Settings:
    load_dotenv()

    massive_key = os.getenv("MASSIVE_API_KEY")
    if (not massive_key):
        raise RuntimeError("MASSIVE_API_KEY environment variable is not set.")

    hf_token: str | None = os.getenv("HF_TOKEN")
    if (not hf_token):
        raise RuntimeError("HF_TOKEN environment variable is not set.")

    return Settings(massive_api_key=massive_key, hf_token=hf_token, trading_fees=load_fees())



