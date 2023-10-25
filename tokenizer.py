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
# print(words) # words list printed!


### Tokenize RULEs
### 1. remove stopwords -> OK
### 2. remove punctuation -> OK
### 3. remove numbers -> OK
### 4. remove english words
### 5. remove duplicated words
### 6. remove empty lists -> OK
### 7. remove words with length less then 2 -> OK


# tokenize the json file
okt = Okt()
tokenized = []
for i in range(len(words)):
    # tokenized.append(okt.morphs(words[i])) -> nouns가 더 나은 결과를 보여주는 것 같음.
    tokenized.append(okt.nouns(words[i]))

# remove stopwords
stopwords = ['와','이', '그', '저', '것', '수', '등', '들', '것', '때', '더', '그', '이', '수', '등', '등등', '때문', '때문에', '위', '바로', '좀', '분', '씨', '제', '그것', '이것', '저것','의','에도']
tokenized = [[j for j in i if j not in stopwords] for i in tokenized]

# remove punctuation
punctuation = ['.', ',', '!', '?', '(', ')', '[', ']', '{', '}', ':', ';', '-', '_', '+', '=', '/', '*', '~', '`', '@', '#', '$', '%', '^', '&', '|', '\\', '「', '」', '→', '),',')=' ,'《','》','>','·','X','↑→','↑','):','->',')+',':(',"'",'x']
tokenized = [[j for j in i if j not in punctuation] for i in tokenized]

# remove numbers
tokenized = [[j for j in i if not j.isdigit()] for i in tokenized]

# remove words with length less than 2
tokenized = [[j for j in i if len(j) > 1] for i in tokenized]

# remove empty lists
tokenized = [i for i in tokenized if i != []]

# tokenized 리스트 안에 있는 리스트 항목들 벗겨내기
tokenized = [item for sublist in tokenized for item in sublist]

# remove duplicated words
tokenized = list(set(tokenized))

print(tokenized)
