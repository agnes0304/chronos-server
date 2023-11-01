# Create에서 사용가능
from app import get_db_connection

object = [
    {'title': '부록: 연표 미기재 기출파트', 'body': '연표에는 없지만 한국사능력검정시험에 등장한 부분을 정리한 부록입니다.',
        'filename': 'ver1.5_AppendixPast.png', 'bloglink': 'https://blog.naver.com/loghistory/223017724700'},
    {'title': '조선 총 흐름정리', 'body': '조선시대 큰 흐름을 볼 수 있는 연표입니다.',
        'filename': 'ver1_JoseonFlow.jpg', 'bloglink': 'https://blog.naver.com/loghistory/222650231016'},
    {'title': '조선 유형별: 붕당', 'body': '조선시대 훈구, 사림에서 시작된 붕당을 정리한 연표입니다.',
        'filename': 'ver1_JoseonParties.jpg', 'bloglink': 'https://blog.naver.com/loghistory/222651224575'},
    {'title': '조선 유형별: 왕', 'body': '조선시대 각 국왕별 키워드 및 업적을 정리한 연표입니다.',
        'filename': 'ver1_JoseonKings.jpg', 'bloglink': 'https://blog.naver.com/loghistory/222650231016'},
    {'title': '조선 유형별: 제도', 'body': '조선시대 사회경제정치제도를 정리한 연표입니다.',
        'filename': 'ver1_JoseonSystem.jpg', 'bloglink': 'https://blog.naver.com/loghistory/222653640621'},
    {'title': '고려 총 흐름정리-외교,왕', 'body': '고려시대 대외관계, 왕 별 키워드 및 큰 흐름을 정리한 연표입니다.',
        'filename': 'ver1_GoryeoKeywords.jpg', 'bloglink': 'https://blog.naver.com/loghistory/222675395950'},
    {'title': '고려 유형별 정리: 제도', 'body': '고려시대 사회제도를 정리한 연표입니다.',
        'filename': 'ver1_GoryeoSystem.jpg', 'bloglink': 'https://blog.naver.com/loghistory/222676367544'},
    {'title': '부록: 한능검 빈출 01', 'body': '한국사능력검정시험에 자주 나오는 부분을 표시한 연표입니다.',
        'filename': 'ver1.5_AppendixFrequent01.png', 'bloglink': 'https://blog.naver.com/loghistory/223017724700'},
    {'title': '부록: 한능검 빈출 02', 'body': '한국사능력검정시험에 자주 나오는 부분을 표시한 연표입니다.',
        'filename': 'ver1.5_AppendixFrequent02.png', 'bloglink': 'https://blog.naver.com/loghistory/223017724700'},
    {'title': '일제강점기 총정리 연표', 'body': '일제강점기 총정리 연표입니다.',
        'filename': 'ver1.5_OccupationSummary.jpg', 'bloglink': 'https://blog.naver.com/loghistory/223017724700'},
    {'title': '일제강점기 유형별: 독립운동', 'body': '일제강점기 독립운동 정리 연표입니다.',
        'filename': 'ver1.5_OccupationIndeMove.jpg', 'bloglink': 'https://blog.naver.com/loghistory/222873128921'},
    {'title': '일제강점기 유형별: 사회문화', 'body': '일제강점기 사회문화 정리 연표입니다.',
        'filename': 'ver1.5_CccupationSystem.jpg', 'bloglink': 'https://blog.naver.com/loghistory/222873128921'},
    {'title': '부록: 선언문', 'body': '선언문 따로 정리한 부록입니다.',
        'filename': 'ver1.5_AppendixDelcaration.jpg', 'bloglink': 'https://blog.naver.com/loghistory/223017724700'},
    {'title': '유형별 기출문제: 지역', 'body': '한국사능력검정시험 기출문제 중 지역에 관련된 문제만 따로 모았습니다.',
        'filename': 'exam_region.pdf', 'bloglink': ''},
    {'title': '유형별 기출문제: 독립운동', 'body': '한국사능력검정시험 기출문제 중 독립운동에 관련된 문제만 따로 모았습니다.',
        'filename': 'exam_indeMove.pdf', 'bloglink': 'https://blog.naver.com/loghistory/222867544553'},
    {'title': '유형별 기출문제: 문화재', 'body': '한국사능력검정시험 기출문제 중 한국의 문화유산에 관련된 문제만 따로 모았습니다.',
        'filename': 'exam_heritage.pdf', 'bloglink': 'https://blog.naver.com/loghistory/222867543165'},
    {'title': '유형별 기출문제: 인물', 'body': '한국사능력검정시험 기출문제 중 인물에 관련된 문제만 따로 모았습니다.',
        'filename': 'exam_character.pdf', 'bloglink': 'https://blog.naver.com/loghistory/222867491295'},
]

# object에서 하나씩 꺼내서 db에 insert
with get_db_connection() as conn:
    with conn.cursor() as cursor:
        for obj in object:
            query = "INSERT INTO files (title, body, filename, bloglink) VALUES (%s, %s, %s, %s);"
            cursor.execute(query, (obj['title'], obj['body'], obj['filename'], obj['bloglink']))
        conn.commit()

print("insert success")