import pandas as pd
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
    ValidationError,
    field_validator,
)
from typing import Self, Iterable
from massive.rest.futures import FuturesAgg
from datetime import datetime, timezone


class FuturesOHLC(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    ticker: str = Field(min_length=1)
    open: float = Field(allow_inf_nan=False)
    high: float = Field(allow_inf_nan=False)
    low: float = Field(allow_inf_nan=False)
    close: float = Field(allow_inf_nan=False)
    volume: int = Field(ge=0)
    transactions: int = Field(ge=0)
    window_start: str
    session_end_date: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_ohlc(self) -> Self:
        if self.high < max(self.low, self.open, self.close):
            raise ValueError(
                "High is not greater than or equal to 'open', 'close', and 'low'."
            )

        if self.low > min(self.high, self.open, self.close):
            raise ValueError(
                "Low is not less than or equal to 'open', 'close', and 'high'."
            )
        return self

    @field_validator("window_start", mode="before")
    @classmethod
    def normalize_window_start(cls, window_start: int) -> str:
        return datetime.fromtimestamp(
            window_start / 1_000_000_000, tz=timezone.utc
        ).isoformat()
    

def validate_data(observations: Iterable[FuturesAgg | bytes]) -> list[FuturesOHLC]:
    validated: list[FuturesOHLC] = []
    for observation in observations:
        try:
            validated.append(FuturesOHLC.model_validate(vars(observation)))
        except ValidationError as e:
            print(str(e))
    return validated
