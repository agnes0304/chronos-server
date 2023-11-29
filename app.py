import os
from flask import Flask, jsonify, request, session, redirect, g
from flask_cors import CORS
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError
from supabase import create_client, Client
from supabase.client import ClientOptions
from botocore.config import Config
from gotrue import SyncSupportedStorage
from werkzeug.local import LocalProxy

### ⚙️ ENV
load_dotenv()


### ⚙️ FLASK SESSION STORAGE FOR SUPABASE (FOR GITHUB OAUTH)
class FlaskSessionStorage(SyncSupportedStorage):
    def __init__(self):
        self.storage = session

    def get_item(self, key: str) -> str | None:
        if key in self.storage:
            return self.storage[key]

    def set_item(self, key: str, value: str) -> None:
        self.storage[key] = value

    def remove_item(self, key: str) -> None:
        if key in self.storage:
            self.storage.pop(key, None)


### ⚙️ S3 BUCKET CONFIG
my_config = Config(
    signature_version = 'v4',
)

### ⚙️ SUPABASE ACCESS
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
# supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

### ⚙️ SUPABASE CONFIG (FOR GITHUB OAUTH)
def get_supabase() -> Client:
    if "supabase" not in g:
        g.supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY,
            options=ClientOptions(storage=FlaskSessionStorage(),flow_type="pkce"),
        )
    return g.supabase

supabase: Client = LocalProxy(get_supabase)


### ⚙️ AWS SES
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
    # search_terms = request.args.get('search').split(" ") -> get 실패가능.  
    search_terms = request.args.get('search')
    print("지우1", search_terms)
    if search_terms:
        print("지우2", search_terms)
        search_query = ' | '.join(search_terms.split(" "))
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
        return jsonify({'message': "success"})

    return jsonify({'message': "상태 업데이트에 실패했습니다."})


### 📍 판매자에게 입금확인 요청 이메일 전송
@app.route('/email', methods=['GET'])
def sendemail_admin():

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
    

### 📍 구매자에게 입금확인 이메일 전송
@app.route('/email/<string:email>', methods=['GET'])
def sendemail_user(email):

    CHARSET = "UTF-8"
    SENDER = f"필기깎는화석 <{AWS_SES_SENDER}>"
    RECIPIENT = email
    AWS_REGION = "ap-northeast-2"
    SUBJECT = "[필기깎는화석] 자료 다운로드가 가능해요!"
    BODY_TEXT = ("안녕하세요 화석입니다.\r\n"
                "올인원 한국사 연표 필기노트를 구매해주셔서 감사합니다😊.\n"
                "필기노트 원본의 용량이 커서 받으시는 분들의 네트워크 상황에 따라 다운로드가 원활하지 않은 경우가 종종 발생합니다.\n"
                "하여 기존 원본을 파트 별로 나누어 다운로드가 가능하게끔 만들었어요!\n"
                "자료 순서는 '연표-빈칸-플러스,부록-필기노트' 순서입니다.\n"
                "준비하시는 일들, 원하시는 결과와 함께 잘 마무리할 수 있는 2023년 한 해 되시길 바랍니다.\n"
                "*참고: PDF라는 파일의 특성상 환불이 어려운 점 양해부탁드립니다.\n"
                "🔗 다운로드 받기\n"
                "🏠 필기깎는화석 홈으로\n"
                )        
    BODY_HTML = """<html>
<head></head>
<body>
  <h1>안녕하세요 화석입니다.</h1>
  <article>
    <p>올인원 한국사 연표 필기노트를 구매해주셔서 감사합니다😊.<p>
    <p>필기노트 원본의 용량이 커서 받으시는 분들의 네트워크 상황에 따라 다운로드가 원활하지 않은 경우가 종종 발생합니다.<p>
    <p>하여 기존 원본을 파트 별로 나누어 다운로드가 가능하게끔 만들었어요!<p>
    <p>자료 순서는 '연표-빈칸-플러스,부록-필기노트' 순서입니다.<p>
    <p>준비하시는 일들, 원하시는 결과와 함께 잘 마무리할 수 있는 2023년 한 해 되시길 바랍니다.<p>
    <p>*참고: PDF라는 파일의 특성상 환불이 어려운 점 양해부탁드립니다.<p>
    <p>🔗 
        <a href='https://chronos.jiwoo.best/payment/success'>다운로드 받기</a>
    </p>
    <p>🏠 
        <a href='https://chronos.jiwoo.best'>필기깎는화석 홈으로</a>
    </p>
  </article>
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


### 📍 깃허브 로그인
@app.route('/signin/github')
def signin_with_github():
    # host_url = os.getenv("HOST_URL")
    res = supabase.auth.sign_in_with_oauth(
        {
            "provider": "github",
            "options": {
                # "redirect_to": f"{host_url}/callback"
                "redirect_to": f"{request.host_url}/callback"
            },
        }
    )
    return redirect(res.url)


### 📍 깃허브 로그인 콜백
@app.route("/callback")
def callback():
    code = request.args.get("code")
    next = request.args.get("next", "/")

    if code:
        res = supabase.auth.exchange_code_for_session({"auth_code": code})

    return redirect(next)


if __name__ == '__main__':
    # app.secret_key = os.getenv('FLASK_SECRET_KEY', 'a_secret_key')
    app.debug = True
    app.run(port=5000)