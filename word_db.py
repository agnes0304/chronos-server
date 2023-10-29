from app import get_db_connection
from tokenizer import filter_words, stopwords, punctuation
from konlpy.tag import Komoran
import json
import os

def add_words_to_db(file_name):
    # Load JSON data from the data folder
    file_path=f'./data/{file_name}'
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Extract text from words in the JSON data
    words = [word_entry["text"] for word_entry in data["words"]]

    tokenizer = Komoran()
    tokenized = [
        filter_words(tokenizer.nouns(word), stopwords, punctuation)
        for word in words
    ]

    tokenized = [tokens for tokens in tokenized if tokens]
    tokenized = [token for sublist in tokenized for token in sublist]
    tokenized = list(set(tokenized))

    # Connect to the database and insert tokenized words
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            for word in tokenized:
                cursor.execute(
                    "INSERT INTO words (name, file) VALUES (%s, %s)", (word, file_name))
        conn.commit()

    print(f"Tokenization and database insertion complete for {file_name}")


data_folder = './data'
json_files = [f for f in os.listdir(data_folder) if f.endswith('.json')]

for file_name in json_files:
    add_words_to_db(file_name)
