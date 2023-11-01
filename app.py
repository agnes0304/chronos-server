import os
import psycopg2
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from psycopg2.extras import DictCursor
import boto3

load_dotenv()

app = Flask(__name__)
CORS(app)

DATABASE_CONFIG = {
    "dbname": "chronos",
    "user": "postgres",
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

def get_db_connection():
    return psycopg2.connect(**DATABASE_CONFIG)


# server end point
@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/posts', methods=['GET'])
def get_posts():

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cursor:  # Use DictCursor here
            query = "SELECT * FROM files;"
            cursor.execute(query)
            posts = cursor.fetchall()

    posts = [dict(row) for row in posts]

    return jsonify(posts)


# id값으로 조회
@app.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            query = "SELECT * FROM files WHERE id = %s;"
            cursor.execute(query, (post_id,))
            post = cursor.fetchone()

    post = dict(post)

    return jsonify(post)


# s3 url 생성 -> 일단 테스트해보기
@app.route('/download/<string:file_name>', methods=['GET'])
def get_download_link(file_name):
    s3_client = boto3.client('s3',
                             aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                             aws_secret_access_key=os.getenv(
                                 "AWS_SECRET_ACCESS_KEY")
                             )

    bucket_name = os.getenv("S3_BUCKET")
    params = {'Bucket': bucket_name, 'Key': file_name}
    try:
        url = s3_client.generate_presigned_url('get_object',
                                        Params=params,
                                        ExpiresIn=600)  # 10 min
        print(url)


        # DONE: CORS에러 test code
        # return jsonify({'url': 'test!!'})

        # DONE: NoSuchKey -> kor to eng(filename)
        return jsonify({'url': url})
    except Exception as e:
        print(e)
        return jsonify({'error': e})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
