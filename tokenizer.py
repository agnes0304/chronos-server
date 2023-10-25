# import json file from the data folder
# tokenize the json file using konlpy

import json
from konlpy.tag import Okt
from collections import Counter

with open('./data/ocr.json', encoding='utf-8') as data_file:
    data = json.load(data_file)

words = []
for i in range(len(data["words"])):
    words.append(data["words"][i]["text"])
print(words) # words list printed!


### Tokenize RULEs
### 1. remove stopwords
### 2. remove punctuation
### 3. remove numbers
### 4. remove english words

# tokenize the json file
# okt = Okt()
# tokenized = []
