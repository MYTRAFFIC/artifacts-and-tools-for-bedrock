# /// script
# dependencies = [
#   "requests<3",
#   "rich",
#   "boto3>=1.34.125",
#   "orjson>=3.10.5",
#   "pandas==2.2.3",
# ]
# ///

"""This script enables to inspect the session used by the application."""

import os

os.environ["SESSION_TABLE_NAME"] = "SessionTable"
os.environ["SESSION_BUCKET_NAME"] = (
    "artifactsandtools-playgroundsessionbucket48941b49-rnuq25dipxqz"
)
import boto3
from common.session import load_session

AWS_REGION = "eu-central-1"
user_id = "63a4c822-9011-702f-951d-fc4b528fab15"
session_id = "14ace7bc-4f6c-4499-bde6-597e1e600881"

s3_client = boto3.client(
    "s3", region_name=AWS_REGION, endpoint_url=f"https://s3.{AWS_REGION}.amazonaws.com"
)

session = load_session(s3_client, user_id, session_id)
breakpoint()
print("done")
