from dataclasses import dataclass
from typing import Required, TypedDict
@dataclass
class Limit:
    limit: int

class MassiveParameters(TypedDict, total=False):
    ticker: Required[str]
    limit: int
    sort: str
    resolution: Required[str]
    window_start: int
    window_start_gte: str | int
    window_start_lte: str | int

