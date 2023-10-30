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
    """Get a new database connection based on the configuration."""
    return psycopg2.connect(**DATABASE_CONFIG)



### server end point
@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/posts', methods=['GET'])
def get_posts():
    """Endpoint to retrieve posts, optionally filtered by a search term."""
    print("jiwoo01")
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            query = "SELECT * FROM files;"
            cursor.execute(query)
            posts = cursor.fetchall()

    return jsonify(posts)

if __name__ == '__main__':
    app.run(debug=True, port=5000)