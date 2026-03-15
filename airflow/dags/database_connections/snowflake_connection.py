import os
from cryptography.hazmat.primitives import serialization
import snowflake.connector


def get_private_key_bytes():
    key_path = os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"]
    with open(key_path, "rb") as f:
        private_key_obj = serialization.load_pem_private_key(f.read(), password=None)
    return private_key_obj.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )


def get_snowflake_connection():
    return snowflake.connector.connect(
        user="DATA_PIPELINE_USER",
        account="VIBIZOV-IS28444",
        private_key=get_private_key_bytes(),
        warehouse="DW_FIND_A_MOVIE",
        database="DB_FIND_A_MOVIE",
        schema="BRONZE_PMS",
        role="DATA_PIPELINE_ROLE"
    )
