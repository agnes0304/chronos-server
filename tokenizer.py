import json
from konlpy.tag import Komoran

# Function to remove unwanted words based on various conditions
def filter_words(word_list, stopwords=stopwords, punctuation=punctuation):
    return [
        word for word in word_list 
        if word not in stopwords 
        and word not in punctuation 
        and not word.isdigit()
        # and len(word) > 1
    ]

# Load JSON data
with open('./data/ocr.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract text from words in the JSON data
words = [word_entry["text"] for word_entry in data["words"]]

tokenizer = Komoran()

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

# Tokenize and filter
tokenized = [
    filter_words(tokenizer.nouns(word), stopwords, punctuation) 
    for word in words
]

# Remove empty lists
tokenized = [tokens for tokens in tokenized if tokens]

# Flatten the list of lists
tokenized = [token for sublist in tokenized for token in sublist]

# Remove duplicate tokens
tokenized = list(set(tokenized))

print(tokenized)
