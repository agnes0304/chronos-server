import os
import psycopg2
from flask import Flask, request, jsonify
from dotenv import load_dotenv

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

@app.route('/posts', methods=['GET'])
def get_posts():
    search_term = request.args.get('search', None)

    conn = get_db_connection()
    cursor = conn.cursor()

    # table name: test
    if search_term:
        cursor.execute("SELECT * FROM test WHERE post_content LIKE %s;", ('%' + search_term + '%',))
    else:
        cursor.execute("SELECT * FROM test;")

    posts = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(posts)

if __name__ == '__main__':
    app.run(debug=True)