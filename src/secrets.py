import os
from dotenv import load_dotenv

load_dotenv()

def get_massive_api_key() -> str | None: 
    return os.getenv("MASSIVE_API")
