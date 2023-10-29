from app import get_db_connection
from konlpy.tag import Komoran
import json
import os

def filter_words(word_list, stopwords, punctuation):
    return [
        word for word in word_list 
        if word not in stopwords 
        and word not in punctuation 
        and not word.isdigit()
        # and len(word) > 1
    ]

def add_words_to_db(file_name):
    # Load JSON data from the data folder
    file_path=f'./data/{file_name}'
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Extract text from words in the JSON data
    words = [word_entry["text"] for word_entry in data["words"]]

    stopwords = [
    '와', '이', '그', '저', '것', '수', '등', '들', '것', 
    '때', '더', '그', '이', '수', '등', '등등', '때문', 
    '때문에', '위', '바로', '좀', '분', '씨', '제', '그것', 
    '이것', '저것', '의', '에도', '위해', '인의'
    ]

    punctuation = [
    '.', ',', '!', '?', '(', ')', '[', ']', '{', '}', ':', 
    ';', '-', '_', '+', '=', '/', '*', '~', '`', '@', '#', 
    '$', '%', '^', '&', '|', '\\', '「', '」', '→', '),', 
    ')=', '《', '》', '>', '·', 'X', '↑→', '↑', '):', '->', 
    ')+', ':(', "'", 'x'
    ]   

    tokenizer = Komoran()
    tokenized = [
        filter_words(tokenizer.nouns(word), stopwords, punctuation)
        for word in words
    ]

    tokenized = [tokens for tokens in tokenized if tokens]
    tokenized = [token for sublist in tokenized for token in sublist]
    tokenized = list(set(tokenized))

    # Connect to the database and insert tokenized words
    file_name_without_extension = os.path.splitext(file_name)[0]
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            for word in tokenized:
                cursor.execute(
                    "INSERT INTO words (word, file) VALUES (%s, %s)", (word, file_name_without_extension))
        conn.commit()

    print(f"Tokenization and database insertion complete for {file_name}")

def delete_words_table():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM words;")
            
            # Reset the auto-increment
            cursor.execute("ALTER SEQUENCE words_id_seq RESTART WITH 1;")
            
        conn.commit()
    print("All records deleted and auto-increment counter reset.")


data_folder = './data'
json_files = [f for f in os.listdir(data_folder) if f.endswith('.json')]

for file_name in json_files:
    add_words_to_db(file_name)


# Call the function to clear the table
# delete_words_table()