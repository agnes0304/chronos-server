### Create에서 사용가능
from app import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO files (title, body, filename) VALUES (%s, %s, %s)", ("일제강점기 총정리 요약", "일제강점기 연표 총정리 요약본입니다.", "ver1.5_일제강점기_요약"))
    conn.commit()

print("insert success")
