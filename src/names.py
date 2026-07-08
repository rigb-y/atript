from pathlib import Path, PosixPath

def get_output_name():
    return f"dumps/dump{sum(1 for f in Path('dumps').iterdir() if f.is_file()) + 1}.json"
