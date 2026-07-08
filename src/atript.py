#!usr/bin/python3
from secrets import get_massive_api_key
from datareader import read_data
from typedefs import Limit
import boto3
from boto import write_json_to_bucket, read_bucket_json_to_json
from names import get_output_name
from pprint import pprint
from massive import RESTClient
from massive.rest.futures import FuturesAgg
from secrets import (get_account_id,
                     get_bucket_name,
                     get_access_key_id,
                     get_secret_access_key,
                     get_s3_api_key)

KEYS: dict[str,str] = {
        "R2_ACCOUNT_ID" : get_account_id(),
        "R2_BUCKET" : get_bucket_name(),
        "AWS_ACCESS_KEY" : get_access_key_id(),
        "AWS_SECRET_ACCESS_KEY" : get_secret_access_key(),
        "ENDPOINT_URL" : get_s3_api_key(),
        "MASSIVE_API" : get_massive_api_key()
}

TICKERS: list[str] = ["MESU6"]

MASSIVE_CLIENT = RESTClient(KEYS["MASSIVE_API"]);

s3 = boto3.client(
    service_name="s3",
    endpoint_url=KEYS["ENDPOINT_URL"],
    aws_access_key_id=KEYS["AWS_ACCESS_KEY"],
    aws_secret_access_key=KEYS["AWS_SECRET_ACCESS_KEY"],
    region_name="auto"
)

def main(*args, **kwargs) -> None: 
    file: str = get_output_name()
    identifier: str = file.removeprefix("./")
    read_data(MASSIVE_CLIENT, KEYS["MASSIVE_API"], TICKERS, Limit(100), file)
    write_json_to_bucket(s3, KEYS["R2_BUCKET"], identifier, file)
    # pprint(read_bucket_json_to_json(s3, KEYS["R2_BUCKET"], identifier))

if __name__ == '__main__':
    main()
