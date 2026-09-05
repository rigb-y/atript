from datetime import date
import re
from typing import Literal
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


type InputArgs = (
        CommandArgs 
        | FetchLookbackArgs 
        | FetchRangeArgs 
        | FetchLatestArgs 
        | ModelArgs 
        | PreprocessArgs
)

class CommandArgs(BaseModel):
    ticker: str = Field(min_length=1)
    resolution: str = Field(min_length=1)
    command: str = Field(min_length=1)

    @field_validator("resolution")
    @classmethod
    def validate_resolution(cls, res):
        if not (match := re.search(r"^(\d+)(sec|min|day|hour|session|week|month|quarter|year)$", res)):
            raise ValueError("Resolution not in the correct form.")
        if re.match(r"(month|quarter|year|session)", match.group(2)):
            raise ValueError(f"{match.group(2)} is not yet supported. Currently supported periods are [min,sec,hour,day,week]")

        return res

class FetchLookbackArgs(CommandArgs):
    period: Literal["days", "weeks", "months", "years"]
    depth: int = Field(gt=0)


class FetchLatestArgs(CommandArgs):
    ...

class FetchRangeArgs(CommandArgs):
    begin_date: date
    end_date: date


    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.begin_date > self.end_date:
            raise ValueError("Starting date must not come after end date.")
        return self


class ModelArgs(CommandArgs):
    pred_length: int = Field(gt=0)
    target: str = Field(default="returns", min_length=1)
    store_weights: bool = Field(default=False)
    eval: bool = Field(default=False)
    quantiles: list = Field(default_factory=lambda: [0.1,0.5,0.9])
    prediction_interval: tuple[float, float]

    @field_validator("quantiles")
    @classmethod
    def validate_quantiles(cls, quantiles):
        if not len(quantiles):
            raise ValueError("Need at least one quantile.")
    
        if not all(0 <= q <= 1 for q in quantiles):
            raise ValueError("Quantiles must be strictly between 0 and 1")

        return quantiles

    @model_validator(mode="after")
    def validate_pi(self) -> Self:
        if self.prediction_interval[0] > self.prediction_interval[1]:
            raise ValueError("Lower bound must not exceed upper bound.")
        if (
                self.prediction_interval[0] not in self.quantiles 
                or self.prediction_interval[1] not in self.quantiles
        ):
            raise ValueError("Prediction interval bounds must be included in quantiles.")
        return self



class PreprocessArgs(CommandArgs):
    ...

def validate_input(args: dict):
    match (args.get("command"), args.get("fetch_command")):
        case ("fetch", "latest"):
            return FetchLatestArgs(**args)
        case ("fetch", "lookback"):
            return FetchLookbackArgs(**args)
        case ("fetch", "range"):
            return FetchRangeArgs(**args)
        case ("preprocess", _):
            return PreprocessArgs(**args)
        case ("model", _):
            return ModelArgs(**args)

    return CommandArgs(**args)





