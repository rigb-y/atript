from dataclasses import dataclass
from typing import Required, TypedDict
from pandas import DataFrame

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
    pred_df: DataFrame
    eval_df: DataFrame
    mae: float
    baseline_mae: float
    mae_skill: float
    rmse: float
    directional_accuracy: float
    loss: dict[float, float]

