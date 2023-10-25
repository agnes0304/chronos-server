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
    return psycopg2.connect(**DATABASE_CONFIG)


@app.route('/posts', methods=['GET'])
def get_posts():
    search_term = request.args.get('search', None)

    conn = get_db_connection()
    cursor = conn.cursor()

    # table name: test
    if search_term:
        cursor.execute(
            "SELECT * FROM test WHERE post_content LIKE %s;", ('%' + search_term + '%',))
    else:
        cursor.execute("SELECT * FROM test;")

    posts = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(posts)


if __name__ == '__main__':
    app.run(debug=True)


# s3버킷에 있는 파일 url 생성 -> 프론트에서 클릭하면 해당 링크 갈 수 있게 api endpoint 만들기
def generate_presigned_url(bucket_name, object_name, expiration=3600):
    s3_client = boto3.client('s3', aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                             aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),)

    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except NoCredentialsError:
        print('Credentials not available')
        return None

    return response


# Example usage
bucket = os.getenv("S3_BUCKET")
object_name = "path/to/your/file.jpg"
url = generate_presigned_url(bucket, object_name)
print(url)
