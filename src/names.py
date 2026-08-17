from pathlib import Path, PosixPath

def get_output_name(symbol: str):
    return f"symbol_data/symbol_data_{symbol}{sum(1 for f in Path('symbol_data').iterdir() if f.is_file()) + 1}.csv"
