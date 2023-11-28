import boto3
from botocore.exceptions import ClientError

CHARSET = "UTF-8"
SENDER = "Sender Name <sender@example.com>"
RECIPIENT = "recipent@example.com"
AWS_REGION = "ap-northeast-2"
SUBJECT = "Amazon SES Test (SDK for Python)"

SUBJECT = "[입금] 입금 확인 요청"
BODY_TEXT = ("🚨 입금 확인 필요.\r\n"
                 "링크로 가서 주문내역을 확인해주세요.🥳 관리자 페이지. 입금확인 대기 리스트"
                )        
BODY_HTML = """<html>
<head></head>
<body>
  <h1>🚨 입금 확인 필요.</h1>
  <p>아래 링크로 가서 주문 내역을 확인해주세요.
    <a href=#>관리자 페이지</a>
    <a href=#>
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
else:
    print("Email sent! Message ID:"),
    print(response['MessageId'])