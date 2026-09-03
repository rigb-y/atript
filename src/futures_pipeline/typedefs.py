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
    window_start:  str
    window_start_gte: str
    window_start_lte: str
