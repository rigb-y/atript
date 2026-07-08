import json
from botocore.exceptions import ClientError

def write_json_to_bucket(s3, bucket_name: str, file: str):
    try:
        with open(file, "rb") as _file:
            s3.put_object(
                    Bucket=bucket_name,
                    Key=file,
                    Body=_file,
                    ContentType="application/json",
            )
    except ClientError as e:
        raise RuntimeError(f"Failed to upload {identifier} to R2: {e}") from e

def read_bucket_json_to_json(s3, bucket_name: str, identifier: str):
    return json.loads(
        s3.get_object(Bucket=bucket_name, Key=identifier)["Body"]
          .read()
          .decode("utf-8")
    )

# TODO: Implement this
def get_all_bucket_objects(s3, bucket_name: str) -> list[str]: 
    return [""]
