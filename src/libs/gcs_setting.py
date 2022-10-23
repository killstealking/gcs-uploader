import os

from dotenv import load_dotenv
from google.cloud import storage as gcs
from google.oauth2 import service_account

load_dotenv()


def get_gcp_credentials():
    key_path = os.environ.get("GCS_KEY_PATH")
    return service_account.Credentials.from_service_account_file(key_path)


def get_gcs_client():
    project_id = os.environ.get("PROJECT_ID")
    return gcs.Client(project_id, get_gcp_credentials())
