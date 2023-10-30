import os
import boto3
from dotenv import load_dotenv
from botocore.exceptions import NoCredentialsError


def generate_public_url(bucket_name, object_name, region="ap-northeast-2"):
    base_url = f"https://{bucket_name}.s3.{region}.amazonaws.com"
    object_url = f"{base_url}/{object_name}"
    return object_url


def generate_presigned_url(bucket_name, object_name, expiration=3600):
    s3_client = boto3.client('s3',
                             aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                             aws_secret_access_key=os.getenv(
                                 "AWS_SECRET_ACCESS_KEY")
                             )

    try:
        params = {'Bucket': bucket_name, 'Key': object_name}
        return s3_client.generate_presigned_url('get_object', Params=params, ExpiresIn=expiration)
    except NoCredentialsError:
        print('Credentials not available')
        return None


## public_url = generate_public_url(bucket_name, object_name)
bucket_name = os.getenv("S3_BUCKET")
object_name = "path/my/file.jpg"
url = generate_public_url(bucket_name, object_name)

## presigned_url = generate_presigned_url(bucket_name, object_name)
bucket_private = os.getenv("S3_PRIVATE_BUCKET")
object_private = "path/my/file.jpg"
url = generate_presigned_url(bucket_private, object_private)
