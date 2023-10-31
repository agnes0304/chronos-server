import os
import psycopg2
from flask import Flask, jsonify
from dotenv import load_dotenv
from psycopg2.extras import DictCursor

load_dotenv()

app = Flask(__name__)

DATABASE_CONFIG = {
    "dbname": "chronos",
    "user": "postgres",
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}


def get_db_connection():
    return psycopg2.connect(**DATABASE_CONFIG)


# server end point
@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/posts', methods=['GET'])
def get_posts():
    print("Get")
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            query = "SELECT * FROM files;"
            cursor.execute(query)
            
            colnames = [desc[0] for desc in cursor.description]
            print("Column names:", colnames)
            rows = cursor.fetchall()
            print("Rows fetched:", rows)

    posts = [dict(zip(colnames, row)) for row in rows]
    print("Posts:", posts)

    return jsonify(posts)


if __name__ == '__main__':
    app.run(debug=True, port=5000)