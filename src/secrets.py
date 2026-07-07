import os

def get_massive_api_key() -> str | None: 
    return os.getenv("MASSIVE_API")
