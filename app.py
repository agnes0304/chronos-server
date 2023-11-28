import os
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError
# import json
from supabase import create_client, Client
# from flask_mail import Mail, Message
from botocore.config import Config

# ⚙️ ENV
load_dotenv()

# ⚙️ S3 BUCKET CONFIG
my_config = Config(
    signature_version = 'v4',
)

# ⚙️ SUPABASE ACCESS
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ⚙️ AWS SES
AWS_SES_SENDER = os.getenv('SENDER_EMAIL')
ADMIN_RECIPENT = os.getenv('ADMIN_EMAIL')
ADMIN_URL = os.getenv('ADMIN_URL')
ORDER_URL = os.getenv('ORDER_URL')


app = Flask(__name__)
CORS(app)


### ⚙️ FUNC: S3 presigned url 생성 함수
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
    

### 📍 MAIN
@app.route('/')
def hello_world():
    return 'Hello, World!'


### 📍 검색 자동 완성
### - 2글자 이상만 반영
@app.route('/words', methods=['GET'])
def get_words():
    data = supabase.table("words").select("word").execute().data
    words = [word['word'] for word in data if len(word['word']) > 1]
    words = list(set(words))  
    return jsonify(words)


### 📍 전체 데이터 조회
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


### 📍 개별 포스트 데이터 조회(ID)
@app.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    data = supabase.table("files").select("*").eq("id", post_id).execute().data
    return jsonify(data[0] if data else {})


### 📍 무료 자료 다운로드 링크 생성
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


### 📍 주문서 용 상품 정보 조회
@app.route('/product/<string:name>', methods=['GET'])
def get_product(name):
    data = supabase.table("products").select("*").eq("name", name).execute().data
    return jsonify(data[0] if data else {})


### 📍 구매한 상품 url 조회
# body로 hashedemail받아서 orders에 있는 모든 데이터 조회
# confirm가 true인 데이터만 조회 -> DONE
@app.route('/orders/<string:email>', methods=['GET'])
def get_orders(email):
    filelist = supabase.rpc("get_filenames_by_email", {'email': email}).execute().data
    response = create_presigned_url(filelist)
    return jsonify(response)


### 📍 입금확인 대기중인 주문 내역 생성
@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    data['isConfirm']=False
    response = supabase.table("orders").insert(data).execute()
    if response.data[0]:
        return jsonify({'message': response.data[0]})

    return jsonify({'message': "Insert Failed"})


### 📍 관리자 로그인
@app.route('/admin', methods=['POST'])
def admin_login():
    data = request.get_json()
    response = supabase.table("users").select("*").eq("email", data['email']).execute().data
    if response[0].get('role') == 1:
        return jsonify({'message': "success"})
    return jsonify({'message': "failed"})


### 📍 입금확인 대기중인 주문 내역 조회
@app.route('/queue', methods=['GET'])
def get_queue():
    response = supabase.table("orders").select("*").eq("isConfirm", False).execute().data
    return jsonify(response)


### 📍 입금확인
@app.route('/queue/<int:order_id>', methods=['PUT'])
def confirm_order(order_id):
    response = supabase.table("orders").update({"isConfirm": True}).eq("id", order_id).execute()
    if response.data[0]:
        return jsonify({'message': response.data[0]})

    return jsonify({'message': "Update Failed"})



### 📍 판매자에게 입금확인 요청 이메일 전송
### *가능하면 구매자에게도 입금 확인 이메일 전송하게끔. 
@app.route('/email', methods=['GET'])
def sendemail():
    
    CHARSET = "UTF-8"
    SENDER = f"필기깎는화석 <{AWS_SES_SENDER}>"
    RECIPIENT = ADMIN_RECIPENT
    AWS_REGION = "ap-northeast-2"
    SUBJECT = "[입금] 입금 확인 요청"
    BODY_TEXT = ("🚨 입금 확인 필요.\r\n"
                 "아래 링크로 가서 주문내역을 확인해주세요🥳 관리자 페이지.\n"
                     "입금확인 대기 리스트"
                )        
    BODY_HTML = """<html>
<head></head>
<body>
  <h1>🚨 입금 확인 필요.</h1>
  <p>아래 링크로 가서 주문 내역을 확인해주세요🥳.
    <a href={ADMIN_URL}>관리자 페이지</a>
    <a href={ORDER_URL}>
      입금확인 대기 리스트</a>.</p>
</body>
</html>
            """            

    client = boto3.client('ses',region_name=AWS_REGION)
    try:
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
        return jsonify({'message': "failed"})
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
        return jsonify({'message': "sent"})


### 📍 이메일 전송
# flask-mail 사용

# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 465
# app.config['MAIL_USERNAME'] = os.getenv('GMAIL')
# app.config['MAIL_PASSWORD'] = os.getenv('GMAIL_APP_PASSWORD') 
# app.config['MAIL_USE_TLS'] = False
# app.config['MAIL_USE_SSL'] = True

# mail = Mail(app)

# @app.route('/email', methods=['GET'])
# def sendemail():
#     msg = Message('Hello', sender=app.config.MAIL_USERNAME, recipients=['jiwoochoi0304@gmail.com'])
#     msg.body = 'Hello Flask'
#     mail.send(msg)
#     return jsonify({'message': "sent"})


if __name__ == '__main__':
    app.debug = True
    app.run(port=5000)