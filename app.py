### MEMO
'''
Postgresql 코드 전부 삭제함. 
Supabase 받아와서 전달하는 값 재확인 필요
'''

import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import boto3

from supabase import create_client, Client

from botocore.config import Config

my_config = Config(
    signature_version = 'v4',
)


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


### 📌 데이터 조회
### SUPABASE CODE
#  search=word1+word2+word3
@app.route('/posts', methods=['GET'])
def get_posts():
    search_terms = request.args.get('search').split(" ")
    if search_terms:
        search_query = ' | '.join(search_terms) # | 기준으로 공백필수.
        print(search_query)
        response = supabase.rpc("search_word", {'search_term': search_query}).execute().data
        print(response) # 
        return response
    else:
        print("search_terms is empty")
        response = supabase.table("files").select("*").execute().data
        return response


### 📌 개별 데이터 조회(ID)
### SUPABASE CODE
@app.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    data = supabase.table("files").select("*").eq("id", post_id).execute().data
    return jsonify(data[0] if data else {})


### 📌 S3 url 생성
@app.route('/download/<string:file_name>', methods=['GET'])
def get_download_link(file_name):
    s3_client = boto3.client('s3',
                             config=my_config,
                             region_name='ap-northeast-2',
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

        return jsonify({'url': url})
    except Exception as e:
        print(e)
        return jsonify({'error': e})


### 📌 자동완성 기능
### - 2글자 이상만 반영
### SUPABASE CODE
@app.route('/words', methods=['GET'])
def get_words():
    data = supabase.table("words").select("word").execute().data
    words = [word['word'] for word in data if len(word['word']) > 1]
    words = list(set(words))  
    return jsonify(words)


if __name__ == '__main__':
    app.debug = True
    app.run(port=5000)