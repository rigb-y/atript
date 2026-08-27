from .config import Settings, load_settings
from .massive_client import create_massive_client
from .cli import create_parser
from argparse import ArgumentParser, Namespace
from massive import RESTClient

def main():
    settings: Settings = load_settings()
    massive_client: RESTClient = create_massive_client(settings.massive_api_key)
    
    parser: ArgumentParser = create_parser()
    args: Namespace = parser.parse_args()

    print(args)

    
if __name__ == "__main__":
    main()

