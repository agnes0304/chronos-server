import os
import psycopg2
import boto3
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from botocore.exceptions import NoCredentialsError

load_dotenv()

app = Flask(__name__)

DATABASE_CONFIG = {
    "dbname": "chronos",
    "user": "postgres",
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

def get_db_connection():
    """Get a new database connection based on the configuration."""
    return psycopg2.connect(**DATABASE_CONFIG)

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

### server end point
@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/posts', methods=['GET'])
def get_posts():
    """Endpoint to retrieve posts, optionally filtered by a search term."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            query = "SELECT * FROM files;"
            cursor.execute(query)
            posts = cursor.fetchall()

    return jsonify(posts)

if __name__ == '__main__':
    app.run(debug=True, port=5000)



### Example usage fo get S3 object url
### public_url = generate_public_url(bucket_name, object_name)
# bucket_name = os.getenv("S3_BUCKET")
# object_name = "path/my/file.jpg"
# url = generate_public_url(bucket_name, object_name)

### presigned_url = generate_presigned_url(bucket_name, object_name)
# bucket_private = os.getenv("S3_PRIVATE_BUCKET")
# object_private = "path/my/file.jpg"
# url = generate_presigned_url(bucket_private, object_private)
