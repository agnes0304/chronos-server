import os
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from dotenv import load_dotenv
import boto3
import hashlib
import urllib.parse
import requests
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

# S3 presigned url 생성 함수
def create_presigned_url(files, expiration=86400):
    s3_client = boto3.client('s3',
                             config=my_config,
                             region_name='ap-northeast-2',
                             aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                             aws_secret_access_key=os.getenv(
                                 "AWS_SECRET_ACCESS_KEY")
                            )
    bucket_name = os.getenv("S3_PRIVATE_BUCKET")

    if isinstance(files, list):
        response = []
        for file in files:
            params = {'Bucket': bucket_name, 'Key': file}
            try:
                response.append(s3_client.generate_presigned_url('get_object',
                                                                 Params=params,
                                                                 ExpiresIn=expiration))
            except Exception as e:
                print(e)
                return None
        return {'urls': response}
    else:
        params = {'Bucket': bucket_name, 'Key': files}
        try:
            response = s3_client.generate_presigned_url('get_object',
                                                        Params=params,
                                                        ExpiresIn=expiration)
        except Exception as e:
            print(e)
            return None
        return {'urls': response}
    
    
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
        search_query = ' | '.join(search_terms)
        response = supabase.rpc("search_word", {'search_term': search_query}).execute().data
        return response
    else:
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
                                        ExpiresIn=86400)

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


### 📌 상품 정보 조회
@app.route('/product/<string:name>', methods=['GET'])
def get_product(name):
    data = supabase.table("products").select("*").eq("name", name).execute().data
    return jsonify(data[0] if data else {})
    # {'id':1,'name':'test'} return


### 📌 결제 내역 조회
# body로 hashedemail받아서 orders에 있는 모든 데이터 조회
@app.route('/orders/<string:email>', methods=['GET'])
def get_orders(email):
    filelist = supabase.rpc("get_filenames_by_email", {'email': email}).execute().data
    response = create_presigned_url(filelist)
    return jsonify(response)




if __name__ == '__main__':
    app.debug = True
    app.run(port=5000)