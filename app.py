import os
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from dotenv import load_dotenv
import boto3
import hashlib

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
    if isinstance(files, list):
        s3_client = boto3.client('s3',
                                 config=my_config,
                                 region_name='ap-northeast-2',
                                 aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                                 aws_secret_access_key=os.getenv(
                                     "AWS_SECRET_ACCESS_KEY")
                                 )
        bucket_name = os.getenv("S3_BUCKET")
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
        return response
    else:
        s3_client = boto3.client('s3',
                                 config=my_config,
                                 region_name='ap-northeast-2',
                                 aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                                 aws_secret_access_key=os.getenv(
                                     "AWS_SECRET_ACCESS_KEY")
                                 )
        bucket_name = os.getenv("S3_BUCKET")
        params = {'Bucket': bucket_name, 'Key': files}
        try:
            response = s3_client.generate_presigned_url('get_object',
                                                        Params=params,
                                                        ExpiresIn=expiration)
        except Exception as e:
            print(e)
            return None
        return response
    
    
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
        print(response)
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
@app.route('/product', methods=['GET'])
def get_product():
    name = request.args.get('name')
    data = supabase.table("products").select("*").eq("name", name).execute().data
    return jsonify(data[0] if data else {})


### 📌 결제 내역 조회
# body로 hashedmobile받아서 orders에 있는 모든 데이터 조회
@app.route('/orders', methods=['GET'])
def get_orders():
    hashed_mobile = request.args.get('hashed_mobile')
    filelist = supabase.rpc("get_filenames_by_mobile", {'mobile': hashed_mobile}).execute().data
    # 동작하는 거 확인함 ["all_appendix.pdf","all_blank.pdf"]
    # filelist에 있는 filename_ex들을 가지고 s3 url 생성해서 return
    response = create_presigned_url(filelist)
    print(response)
    return jsonify(response)


### 📌 페이앱에서 결제완료 후 전송하는 피드백
@app.route('/paying_feedback', methods=['POST'])
def process_payment_feedback():
    payapp_userid = 'payapp seller ID' 
    payapp_key = os.getenv('PAYAPP_API_KEY')
    payapp_val = os.getenv('PAYAPP_API_VALUE')

    if request.method == 'POST':
        if (payapp_userid == request.form.get('userid')) and (payapp_key == request.form.get('linkkey')) and (payapp_val == request.form.get('linkval')):
            # 결제완료 상태일 경우
            if request.form.get('pay_state') == '4':
                
                product = request.form.get('goodname')
                mobile = request.form.get('recvphone')
                price = int(request.form.get('price'))
                mul_no = int(request.form.get('mul_no'))

                mobile_hash = hashlib.sha512(mobile.encode()).hexdigest()

                response = supabase.table('orders').upsert([
                    {
                        'product': product,
                        'mobile': mobile_hash,
                        'price': price,
                        'mul_no': mul_no
                    }
                ]).execute()
                print(response)
                if response.error:
                    return jsonify({'error': 'Failed to insert data into orders table'}), 500

                response = make_response('SUCCESS', 200)
                return response


if __name__ == '__main__':
    app.debug = True
    app.run(port=5000)