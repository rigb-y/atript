from argparse import ArgumentParser
from argparse import _SubParsersAction


def create_parser() -> ArgumentParser:

    shared = ArgumentParser(add_help=False)
    shared.add_argument("-t", "--ticker", type=str, required=True)
    shared.add_argument("-r", "--resolution", type=str, required=True)

    parser = ArgumentParser(parents=[shared])

    subparsers = parser.add_subparsers(dest="command", required=True)

    create_fetch_parser(subparsers, shared)
    create_preprocess_parser(subparsers, shared)

    return parser

def create_fetch_parser(subparsers: _SubParsersAction, common_args: ArgumentParser | None = None) -> ArgumentParser:
    if common_args is None:
        common_args = ArgumentParser(add_help=False)

    fetch_parser: ArgumentParser = subparsers.add_parser("fetch")

    fetch_subparsers: _SubParsersAction = fetch_parser.add_subparsers(dest="fetch_command", required=True)

    latest_parser: ArgumentParser = fetch_subparsers.add_parser("latest", parents=[common_args])

    lookback_parser: ArgumentParser = fetch_subparsers.add_parser("lookback", parents=[common_args])
    lookback_parser.add_argument("--period", choices=["days","weeks","months","years"], required=True)
    lookback_parser.add_argument("--depth", required=True, type=int)

    range_parser: ArgumentParser = fetch_subparsers.add_parser("range", parents=[common_args])
    range_parser.add_argument("--begin", required=True)
    range_parser.add_argument("--end", required=True)
    
    return fetch_parser

def create_preprocess_parser(subparsers: _SubParsersAction, common_args: ArgumentParser | None = None) -> ArgumentParser:
    if common_args is None:
        common_args = ArgumentParser(add_help=False)

    preproc_parser: ArgumentParser = subparsers.add_parser("preprocess", parents=[common_args])
    return preproc_parser
