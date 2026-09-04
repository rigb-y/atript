from .config import Settings, load_settings, MODEL_DIR
from .massive_client import create_massive_client
from .cli import create_parser
from argparse import ArgumentParser, Namespace
from .typedefs import MassiveParameters
from .fetch import fetch
from .preprocessing.preprocess import preprocess
from .model import run_model
import re

def main():
    settings: Settings = load_settings()
    parser: ArgumentParser = create_parser()

    args: Namespace = parser.parse_args()
    if args.ticker is None:
        parser.error("-t/--ticker is required")

    if args.resolution:
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
        case "model":
            hf_token = settings.hf_token
            if (not args.target):
                print(f"No target specified, using default target: {settings.default_target}")
                target = settings.default_target
            else:
                target = args.target

            if (not args.pred_length):
                print(f"No prediction length specified, using default length of {settings.default_prediction_length}")
                pred_length =  settings.default_prediction_length
            else:
                pred_length = args.pred_length

            run_model(args.ticker, target, pred_length, hf_token=hf_token, model_dir=MODEL_DIR/args.ticker, store_weights=args.store_weights, eval=args.eval)
        case _:
            return
    
if __name__ == "__main__":
    main()

