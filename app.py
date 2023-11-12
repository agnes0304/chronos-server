import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import boto3

from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

load_dotenv()

app = Flask(__name__)
CORS(app)

### MAIN
@app.route('/')
def hello_world():
    return 'Hello, World!'


### SUPABASE CODE
@app.route('/posts', methods=['GET'])
def get_posts():
    search_terms = request.args.getlist('search')
    if search_terms:
        print(f"search_terms: {search_terms}")
        search_query = '|'.join(search_terms)

        response = supabase.rpc("search_word", {'search_term': search_query}).execute().data

        return response
    else:
        print("search_terms is empty")
        response = supabase.table("files").select("*").execute().data
        return response

### POSTGRESQL CODE
# @app.route('/posts', methods=['GET'])
# def get_posts():
#     search_terms = request.args.getlist('search')
#     print(search_terms)
#     with get_db_connection() as conn:
#         with conn.cursor(cursor_factory=DictCursor) as cursor:
#             if search_terms:
#                 like_terms = ["%" + term + "%" for term in search_terms] 
#                 query = """
#                 SELECT DISTINCT f.* FROM words w
#                 INNER JOIN files f ON w.file = f.id
#                 WHERE w.word ILIKE ANY(%s);
#                 """
#                 cursor.execute(query, (like_terms,))
#             else:
#                 query = "SELECT DISTINCT * FROM files;"
#                 cursor.execute(query)
#             posts = cursor.fetchall()
#     posts = [dict(row) for row in posts]
#     return jsonify(posts)


### id값으로 조회
### SUPABASE CODE
@app.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    data = supabase.table("files").select("*").eq("id", post_id).execute().data
    return jsonify(data[0] if data else {})

### POSTGRESQL CODE
# @app.route('/posts/<int:post_id>', methods=['GET'])
# def get_post(post_id):
#     with get_db_connection() as conn:
#         with conn.cursor(cursor_factory=DictCursor) as cursor:
#             query = "SELECT * FROM files WHERE id = %s;"
#             cursor.execute(query, (post_id,))
#             post = cursor.fetchone()
#     post = dict(post)
#     return jsonify(post)


### s3 url 생성
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
                                        ExpiresIn=600)
        # DONE: CORS에러 test code
        # return jsonify({'url': 'test!!'})
        # DONE: NoSuchKey -> kor to eng(filename)
        return jsonify({'url': url})
    except Exception as e:
        print(e)
        return jsonify({'error': e})


### 자동완성 기능
### - 2글자 이상만 반영
### SUPABASE CODE
@app.route('/words', methods=['GET'])
def get_words():
    data = supabase.table("words").select("word").execute().data
    words = [word['word'] for word in data if len(word['word']) > 1]
    words = list(set(words))  
    return jsonify(words)

### POSTGRESQL CODE
# @app.route('/words', methods=['GET'])
# def get_words():
#     with get_db_connection() as conn:
#         with conn.cursor() as cursor:
#             query = "SELECT word FROM words WHERE LENGTH(word) > 1;"
#             cursor.execute(query)
#             words = cursor.fetchall()
#     words = [word[0] for word in words]
#     # 중복제거
#     words = list(set(words))
#     return jsonify(words)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
