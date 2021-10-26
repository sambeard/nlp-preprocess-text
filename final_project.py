import csv
from sklearn.feature_extraction.text import CountVectorizer
from nltk import word_tokenize
reader = csv.reader(open('PoetryFoundationData.csv', 'r', encoding='utf8'), delimiter= ",",quotechar='\"')
data = []
for line in reader:
    data.append(line)

poems = [l[2] for l in data]

tokens = []
for poem in poems:
    tokens += word_tokenize(poem)

# cv = CountVectorizer(input='content')
# cv.fit(poems)
#tokens = cv.get_feature_names_out()
print(len(tokens))