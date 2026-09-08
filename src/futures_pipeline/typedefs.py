from dataclasses import dataclass
from typing import Required, TypedDict
from pandas import Series, DataFrame
from .validate import CommandArgs, FetchLatestArgs, FetchRangeArgs, FetchLookbackArgs, ModelArgs, PreprocessArgs
from typing import Literal
import re

@dataclass
class Limit:
    limit: int

class MassiveParameters(TypedDict, total=False):
    ticker: Required[str]
    limit: int
    sort: str
    resolution: Required[str]
    window_start:  str
    window_start_gte: str
    window_start_lte: str
    window_start_gt: str
    window_start_lt: str


@dataclass
class EvaluationResult:
    pred_df: Series
    eval_df: Series 
    by_horizon: DataFrame
    mae: float
    baseline_mae: float
    mae_skill: float
    rmse: float
    directional_accuracy: float
    by_horizon_loss: DataFrame
    loss: dict[float, float]
    baseline_loss: dict[float,float]
    intervals_by_horizon: DataFrame
    pi_coverage: float
    nominal_coverage: float
    mean_interval_width: float
    quantile_calibration: dict[float, float]
    calibration_error: dict[float, float]

type InputArgs = (
        CommandArgs 
        | FetchLookbackArgs 
        | FetchRangeArgs 
        | FetchLatestArgs 
        | ModelArgs 
        | PreprocessArgs
)

type TimedeltaUnit = Literal["s", "min", "h", "D", "W"]

class CandleResolution:
    resolution: str
    length: int
    unit: str

    __fixed_units: dict[str, TimedeltaUnit] = {
            "sec": "s",
            "min": "min",
            "hour": 'h',
            "day": "D",
            "week": "W"
    }

    def __init__(self, resolution: str) -> None:
        self.resolution = resolution
        #  Parse resolution.
        match = re.match(r"^(\d+)(sec|min|day|hour|session|week|month|quarter|year)$", resolution)
    
        if (match is None):
            raise ValueError(f"{resolution} is not a valid resolution.")
    
        self.length = int(match.group(1))
        self.unit = match.group(2)

    # Maps resolution units to a unit from TimeDeltaUnitChoices.
    def to_timedelta_unit(self) -> TimedeltaUnit:
        return self.__fixed_units[self.unit]

