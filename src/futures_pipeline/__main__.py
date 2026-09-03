from .config import Settings, load_settings
from .massive_client import create_massive_client
from .cli import create_parser
from argparse import ArgumentParser, Namespace
from massive import RESTClient
from .typedefs import MassiveParameters
from .fetch import fetch
from .preprocessing.preprocess import preprocess
import re

def main():
    settings: Settings = load_settings()
    parser: ArgumentParser = create_parser()

    args: Namespace = parser.parse_args()
    if args.ticker is None:
        parser.error("-t/--ticker is required")

    if args.resoultion:
        if not (match := re.search(r"^(\d+)(sec|min|hour|session|week|month|quarter|year)$", args.resolution)):
            raise ValueError("Resolution not in the correct form.")
        if re.match(r"(month|quarter|year|session)", match.group(2)):
            raise ValueError(f"{match.group(2)} is not yet supported. Currently supported periods are [min,sec,hour,day,week]")

    resolution = args.resolution or settings.default_resolution
    match args.command:
        case "fetch":
            massive_parameters: MassiveParameters = {
                    # "limit": 100,
                    "sort": "window_start.desc",
                    "resolution": resolution,
                    "ticker": args.ticker,
                    }
            fetch(massive_parameters, create_massive_client(settings.massive_api_key), args)
        case "preprocess":
            preprocess(args.ticker, resolution)
        case _:
            return
    
if __name__ == "__main__":
    main()

