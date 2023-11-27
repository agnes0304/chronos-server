import os
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from dotenv import load_dotenv
import boto3
import json
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


### 📌 검색 자동 완성
### - 2글자 이상만 반영
@app.route('/words', methods=['GET'])
def get_words():
    data = supabase.table("words").select("word").execute().data
    words = [word['word'] for word in data if len(word['word']) > 1]
    words = list(set(words))  
    return jsonify(words)


### 📌 전체 데이터 조회
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


### 📌 개별 포스트 데이터 조회(ID)
@app.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    data = supabase.table("files").select("*").eq("id", post_id).execute().data
    return jsonify(data[0] if data else {})


### 📌 무료 자료 다운로드 링크 생성
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


### 📌 주문서 용 상품 정보 조회
@app.route('/product/<string:name>', methods=['GET'])
def get_product(name):
    data = supabase.table("products").select("*").eq("name", name).execute().data
    return jsonify(data[0] if data else {})


### 📌 구매한 상품 url 조회
# body로 hashedemail받아서 orders에 있는 모든 데이터 조회
# confirm가 true인 데이터만 조회 -> DONE
@app.route('/orders/<string:email>', methods=['GET'])
def get_orders(email):
    filelist = supabase.rpc("get_filenames_by_email", {'email': email}).execute().data
    response = create_presigned_url(filelist)
    return jsonify(response)


### 📌 입금확인 대기중인 주문 내역 생성
# TODO: confirmed column 추가해서 false로 저장
@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    data['isConfirm']=False
    response = supabase.table("orders").insert(data).execute()
    if response.data[0]:
        return jsonify({'message': response.data[0]})

    return jsonify({'message': "Insert Failed"})


### 📌 관리자 로그인
@app.route('/admin', methods=['POST'])
def admin_login():
    data = request.get_json()
    response = supabase.table("users").select("*").eq("email", data['email']).execute().data
    if response.data[0].get('role') == 1:
        return jsonify({'message': "success"})
    return jsonify({'message': "failed"})


# ### 📌 입금확인 대기중인 주문 내역 조회
# # TODO: confirmed가 false인 데이터만 조회
# @app.route('/queue', methods=['GET'])


# ### 📌 입금확인
# # TODO: confirmed를 true로 변경
# @app.route('/orders/<int:order_id>', methods=['PUT'])



# ### 📌 판매자에게 입금확인 요청 이메일 전송
# # TODO: AWS SES 사용
# @app.route('/email', methods=['POST'])


if __name__ == '__main__':
    app.debug = True
    app.run(port=5000)