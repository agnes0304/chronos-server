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
@app.route('/product', methods=['POST'])
def get_product():
    data = request.get_json() 
    name = data.get('name') if data else None
    data = supabase.table("products").select("*").eq("name", name).execute().data
    
    return jsonify(data[0] if data else {})
    # {'id':1,'name':'test'} return


### 📌 결제 내역 조회
# body로 hashedmobile받아서 orders에 있는 모든 데이터 조회
@app.route('/orders', methods=['POST'])
def get_orders():
    data = request.get_json() 
    hashed_mobile = data.get('hashed_mobile') if data else None
    print(hashed_mobile)
    filelist = supabase.rpc("get_filenames_by_mobile", {'mobile': hashed_mobile}).execute().data
    print(filelist)
    response = create_presigned_url(filelist)
    print(response) # print test 필요
    return jsonify(response)


### 📌 결제 요청
@app.route('/paying_payapp', methods=['POST'])
def process_payment():
    order = request.get_json() 

    goodName = order.get('goodname') if order else None
    price = order.get('price') if order else None
    recvphone = order.get('recvphone') if order else None

    userID = os.getenv('PAYAPP_USERID')
    shopName = os.getenv('PAYAPP_SHOPNAME')
    returnURL = os.getenv('PAYAPP_RETURNURL')
    feedbackURL = os.getenv('PAYAPP_FEEDBACKURL')
    
    data = {
        'cmd': 'payrequest',
        'userid': userID,
        'shopname': shopName,
        'returnurl': returnURL,
        'goodname': goodName,
        'price': int(price),
        'recvphone': recvphone,
        'smsuse': 'n',
        'feedbackurl': feedbackURL,
        # 'redirectpay': '1',
        'skip_cstpage': 'y',
    }

    encoded_data = urllib.parse.urlencode(data)

    headers = {
        'Accept': 'text/html,application/xhtml+xml,*/*',
        'Host': 'api.payapp.kr',
        'Accept-Language': 'ko-KR',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    response = requests.post('http://api.payapp.kr/oapi/apiLoad.html', headers=headers, data=encoded_data)
    if response.status_code == 200:
        response_data = urllib.parse.parse_qs(response.text)

        if response_data['state'][0] == '0':
            return "결제 도중 에러가 발생했습니다. 다시 결제를 진행해 주시기바랍니다."
    else:
        return "Error with the external API request"


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