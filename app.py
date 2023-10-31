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
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cursor:  # Use DictCursor here
            query = "SELECT * FROM files;"
            cursor.execute(query)
            posts = cursor.fetchall()

    posts = [dict(row) for row in posts]

    return jsonify(posts)

# id값으로 조회
@app.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            query = "SELECT * FROM files WHERE id = %s;"
            cursor.execute(query, (post_id,))
            post = cursor.fetchone()

    post = dict(post)

    return jsonify(post)

if __name__ == '__main__':
    app.run(debug=True, port=5000)