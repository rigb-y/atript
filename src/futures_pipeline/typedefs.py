from dataclasses import dataclass
from typing import Required, TypedDict
from pandas import Series

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

@dataclass
class EvaluationResult:
    pred_df: Series
    eval_df: Series 
    mae: float
    baseline_mae: float
    mae_skill: float
    rmse: float
    directional_accuracy: float
    loss: dict[float, float]
    baseline_loss: dict[float,float]
    pi_coverage: float
    nominal_coverage: float
    mean_interval_width: float
    quantile_calibration: dict[float, float]
    calibration_error: dict[float, float]


