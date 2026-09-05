from argparse import ArgumentParser, SUPPRESS
from argparse import _SubParsersAction


def create_parser() -> ArgumentParser:

    shared = ArgumentParser(add_help=False, argument_default=SUPPRESS)
    shared.add_argument("-t", "--ticker", type=str)
    shared.add_argument("-r", "--resolution", type=str)

    parser = ArgumentParser(parents=[shared], argument_default=SUPPRESS)

    subparsers = parser.add_subparsers(dest="command", required=True)

    create_fetch_parser(subparsers, shared)
    create_preprocess_parser(subparsers, shared)
    create_model_parser(subparsers)

    return parser

def create_fetch_parser(subparsers: _SubParsersAction, common_args: ArgumentParser | None = None) -> ArgumentParser:
    if common_args is None:
        common_args = ArgumentParser(add_help=False)

    fetch_parser: ArgumentParser = subparsers.add_parser("fetch", argument_default=SUPPRESS)

    fetch_subparsers: _SubParsersAction = fetch_parser.add_subparsers(dest="fetch_command", required=True)

    latest_parser: ArgumentParser = fetch_subparsers.add_parser("latest", parents=[common_args], argument_default=SUPPRESS)

    lookback_parser: ArgumentParser = fetch_subparsers.add_parser("lookback", parents=[common_args], argument_default=SUPPRESS)
    lookback_parser.add_argument("--period", choices=["days","weeks","months","years"], required=True)
    lookback_parser.add_argument("--depth", required=True, type=int)

    range_parser: ArgumentParser = fetch_subparsers.add_parser("range", parents=[common_args], argument_default=SUPPRESS)
    range_parser.add_argument("--begin", required=True)
    range_parser.add_argument("--end", required=True)
    
    return fetch_parser

def create_preprocess_parser(subparsers: _SubParsersAction, common_args: ArgumentParser | None = None) -> ArgumentParser:
    if common_args is None:
        common_args = ArgumentParser(add_help=False)

    preproc_parser: ArgumentParser = subparsers.add_parser("preprocess", parents=[common_args], argument_default=SUPPRESS)
    return preproc_parser

def create_model_parser(subparsers: _SubParsersAction) -> None:
    parser: ArgumentParser = subparsers.add_parser("model", argument_default=SUPPRESS)
    parser.add_argument("--ticker", '-t', type=str)
    parser.add_argument("--pred_length", "-p", type=int)
    parser.add_argument("--target", "-T", type=str)
    parser.add_argument("--store_weights", "-s", action="store_true")
    parser.add_argument("--eval", "-e", action="store_true")
