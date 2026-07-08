import os
from dotenv import load_dotenv

load_dotenv()

def get_massive_api_key() -> str | None: 
    return os.getenv("MASSIVE_API")

def get_account_id() -> str | None:
    return os.getenv("ACCOUNT_ID")

def get_bucket_name() -> str | None:
    return os.getenv("BUCKET_NAME")

def get_access_key_id() -> str | None:
    return os.getenv("ACCESS_KEY_ID")

def get_secret_access_key() -> str | None:
    return os.getenv("SECRET_ACCESS_KEY")

def get_s3_api_key() -> str | None:
    return os.getenv("S3_API_KEY")
