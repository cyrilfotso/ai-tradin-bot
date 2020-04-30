#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 00:53:53 2020

@author: c106763

"""

import re
import string
import nltk
import pickle
import pandas as pd
import TwitterSearch as Twiter
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestClassifier

# do this only the first time
#nltk.download('stopwords')

ps = nltk.PorterStemmer()

url1 = 'https://seekingalpha.com/symbol/{}?s={}'
# doc : https://www.kaggle.com/ragnisah/text-data-cleaning-tweets-analysis


stopword = nltk.corpus.stopwords.words('english')

def clean_text(text):
    text_lc = "".join([word.lower() for word in text if word not in string.punctuation]) # remove puntuation
    text_rc = re.sub('[0-9]+', '', text_lc)
    tokens = re.split('\W+', text_rc)    # tokenization
    # remove stopwords and stemming
    # Stemming and Lammitization Ex - developed, development
    text = [ps.stem(word) for word in tokens if word not in stopword]  
    return ' '.join(text)



def predict_stock_move(stock_data):
    df=pd.read_csv('Data.csv', encoding = "ISO-8859-1")
    train = df[df['Date'] < '20150101']
    # Removing punctuations
    data=train.iloc[:,2:27]
    data.replace("[^a-zA-Z]"," ",regex=True, inplace=True)
    
    # Renaming column names for ease of access
    list1= [i for i in range(25)]
    new_Index=[str(i) for i in list1]
    data.columns= new_Index
    for index in new_Index:
        data[index]=data[index].str.lower()
    headlines = []
    for row in range(0,len(data.index)):
        headlines.append(' '.join(str(x) for x in data.iloc[row,0:25]))
        
    countvector=CountVectorizer(ngram_range=(2,2))
    countvector.fit_transform(headlines)
    test_dataset_msft = countvector.transform(stock_data)
    
    filename = 'finalized_model.sav'
    loaded_model = pickle.load(open(filename, 'rb'))
    result_predicted = loaded_model.predict(test_dataset_msft)
    
    return result_predicted
    
    
def process_prediction(symbol = 'RLLCF'):
    try:
        tso = Twiter.TwitterSearchOrder() # create a TwitterSearchOrder object
        tso.set_keywords(['{} stock'.format(symbol)]) # let's define all words we would like to have a look for
        tso.set_language('en') # we want to see German tweets only
        tso.set_include_entities(False) # and don't give us all those entity information
    
        # it's about time to create a TwitterSearch object with our secret tokens
        ts = Twiter.TwitterSearch(
            consumer_key = '0JQ2IcInTurFu7HbmcykbZiBV',
            consumer_secret = 'SnYijmVU70cmuFPxv1iH0Q6vTf4W4NlpYSD05u0PeAUJfJowVj',
            access_token = '991625774-r0nMyb9fdl7lZ77DHDRZDnSrCK73cUEcTextrrEQ',
            access_token_secret = '7KyOSJjE4N3iaKkAAMkoQ9nYJMMnGNjWl6XfYzNp8fUVy'
        )
    
        # this is where the fun actually starts :)
        msft_data_txt = ""
        for tweet in ts.search_tweets_iterable(tso):
            #print( '@%s tweeted: %s' % ( tweet['user']['screen_name'], tweet['text'] ) )
            msft_data_txt += tweet['text']
        
        msft_data_txt = [clean_text(msft_data_txt)]
        
        # load the model from disk
        out_predicted = predict_stock_move(msft_data_txt)
        
        return out_predicted
    
    except Twiter.TwitterSearchException as e: 
        print(e)
        
        
if __name__ == "__main__":
    symbol = 'msft'
    print(process_prediction(symbol))
    
    
    
    
    
