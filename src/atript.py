#!usr/bin/python3
from datareader import read_data, make_csv
from typedefs import Limit
import boto3
from pathlib import Path
import os
from boto import write_json_to_bucket, read_bucket_json_to_json
from names import get_output_name
from pprint import pprint
from massive import RESTClient
import anthropic
import argparse
import json
from massive.rest.futures import FuturesAgg
from atript_secrets import ( 
                     get_massive_api_key,
                     get_account_id,
                     get_bucket_name,
                     get_access_key_id,
                     get_secret_access_key,
                     get_s3_api_key,
                     get_claude_key
                     )

# VWAP, RSI, EMA, ATR, bollinger Bands (20, 2\sigma)

KEYS: dict[str,str] = {
        "R2_ACCOUNT_ID" : get_account_id(),
        "R2_BUCKET" : get_bucket_name(),
        "AWS_ACCESS_KEY" : get_access_key_id(),
        "AWS_SECRET_ACCESS_KEY" : get_secret_access_key(),
        "ENDPOINT_URL" : get_s3_api_key(),
        "MASSIVE_API" : get_massive_api_key(),
        "CLAUDE_KEY":  get_claude_key()
}

TICKERS: list[str] = ["MESU6"]
MASSIVE_CLIENT = RESTClient(KEYS["MASSIVE_API"]);
CLAUDE_MODEL = "claude-sonnet-5"
MAX_TOKENS = 5000

def main() -> None:
    if not Path("symbol_data").exists():
        os.mkdir("symbol_data")

    client = anthropic.Anthropic(api_key=KEYS['CLAUDE_KEY'])

    data = read_data(MASSIVE_CLIENT, TICKERS, Limit(100))
    for ticker, d in data.items():
        make_csv(ticker,d)
    return

    with open(file, 'rb') as f:
        file_upload = client.beta.files.upload(
                file=(Path(file).name, f, "application/json")
        )

    message = client.beta.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        betas=["code-execution-2025-08-25", "files-api-2025-04-14"],
        tools=[
            {
                "type": "code_execution_20250825",
                "name": "code_execution"
           }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Load this JSON dataset and give me a summary of its structure and key statistics."
                        },
                    {
                        "type": "container_upload",
                        "file_id": file_upload.id
                        }
                    ]
                }
            ],
    )
    for block in message.content:
        if block.type == "text":
            print(block.text)

    # write_json_to_bucket(s3, KEYS["R2_BUCKET"], file)
    # pprint(read_bucket_json_to_json(s3, KEYS["R2_BUCKET"], identifier))

if __name__ == '__main__':
    main()
