#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec  8 23:56:51 2024

@author: komalwavhal
"""



import pandas as pd
import matplotlib.pyplot as plt1
from wordcloud import WordCloud
import matplotlib.pyplot as plt



import os 
import pandas as pd 

# Step 1: Get a list of all CSV files in the current directory
csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]

# Step 2: Read all CSV files and store them in a list of DataFrames
dfs = [pd.read_csv(f) for f in csv_files]

# Step 3: Concatenate all DataFrames into a single DataFrame
df = pd.concat(dfs, ignore_index=True)


# Step 2: Clean the 'Title' column to ensure all entries are strings and handle NaN values
df['Title'] = df['Title'].fillna('').astype(str)  # Replace NaN with empty string and ensure all are strings

# Step 3: Filter the titles based on the class (positive, negative, neutral)
positive_titles = " ".join(df[df['class'] == 'positive']['Title'])
negative_titles = " ".join(df[df['class'] == 'negative']['Title'])
all_titles = " ".join(df['Title'])  # All titles combined

from nltk.corpus import stopwords

stopwords_english = stopwords.words('english')  # Get English stopwords
  

custom_stopwords = ['Bitcoin', 'Ethereum', 'Tether',  'Binance', 'Solana', 'USD Coin', 'USDC' , 
             'Ripple', "Staked Ether", 'StETH', 'Dogecoin','btc', 'ethereum', 'Tether', 
             'binance', 'solana', 'usdcoin', 'ripple', 'steth', 'dogecoin', 'tron'  ,'a', 
             'an', 'the', 'and', 'but', 'or', 'nor', 'so', 'for', 'yet', 'in', 'on', 'at', 
    'by', 'with', 'about', 'against', 'into', 'through', 'during', 'before', 'after', 
    'I', 'you', 'he', 'she', 'it', 'we', 'they', 'them', 'this', 'that', 'which', 'who', 
    'whom', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 
    'do', 'does', 'did', 'very', 'too', 'quite', 'really', 'only', 'just', 'still', 'even', 
    'how', 'when', 'where', 'why', 'why', 'as', 'up', 'down', 'here', 'there', 'all', 'some', 
    'any', 'each', 'few', 'many', 'not', 'btc', 'ethereum', 'tether', 'binance', 'solana', 
    'usdcoin', 'ripple', 'steth', 'dogecoin', 'tron', 'blockchain', 'crypto', 'cryptocurrency', 
    'wallet', 'exchange', 'coin', 'trade', 'market', 'bitcoin', 'altcoin', 'buy', 'sell', 'hodl', 
    'nft', 'token', 'staking', 'mining', 'price', 'value', 'volume', 'ether', 'defi', 'smart', 
    'contract', 'gas', 'dao', 'dapp', 'staking', 'ledger', 'block', 'security', 'invest', 'tokenomics',
    'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'aren’t', 'aren', 
    'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'can', 
    'cannot', 'could', 'couldn’t', 'couldnt', 'did', 'didn’t', 'didnt', 'do', 'does', 'doesn’t', 'doesnt', 
    'don’t', 'don', 'doing', 'don’t', 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', 'hadn’t',
    'hadnt', 'has', 'hasn’t', 'hasnt', 'have', 'haven’t', 'havent', 'having', 'he', 'he’d', 'he’ll', 
    'he', 'how', "how’s", 'how' , 'however', 'i',  'i’ll', 'i’m', 'i’ve', 'i',  'if', 'if', 'in', 'into',
    'btc', 'bitcoin', 'ethereum', 'tether', 'binance', 'solana', 'usdcoin', 'ripple', 'steth', 
    'dogecoin', 'tron', 'blockchain', 'crypto', 'cryptocurrency', 'wallet', 'exchange', 'coin', 
    'trade', 'market', 'altcoin', 'buy', 'sell', 'hodl', 'nft', 'token', 'staking', 'mining', 
    'price', 'value', 'volume', 'ether', 'defi', 'smart', 'contract', 'gas', 'dao', 'dapp', 
    'staking', 'ledger', 'block', 'security', 'invest', 'tokenomics', 'stablecoin', 'decentralized',
    'transaction', 'blockchain', 'wallets', 'mining', 'blockchain', 'peer', 'hash', 'token', 'proof', 'network',
   'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 
    'are', 'aren’t', 'aren', 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'its', 'will', 'what', 'it','over','user','see',
    'between', 'both', 'but', 'by', 'can', 'cannot', 'could', 'couldn’t', 'couldnt', 'did', 'Really',
     'didnt', 'do', 'does', 'doesnt', 'dont', 'don', 'doing', 'don', 'New', 'ETF', 'Best','Bullish','Say', 'U', 'ETH','USDT',
    'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', 'hadn’t', 'hadnt', 'has', 'Billion','Says','Year','One', 
    'hasn’t', 'hasnt', 'have', 'haven’t', 'havent', 'having', 'he', 'he’d', 'he’ll', 'he’s', 'he', 
    'how', 'hows', 'how' , 'however', 'i', 'i’d', 'i’ll', 'i’m', 'i’ve', 'i'   ,  'lets', 'let', 'of','to', 'too', 'crypto',
    'now','m','million','k','may','fee','week','top','bitcoinistcom','more','us','first', 'b', 'know'
  ]


# Combine stopwords
stopwords = list(set(stopwords_english + custom_stopwords))


# Step 4: Combine NLTK's stopwords with the custom stopwords list
stopwords = list(set(custom_stopwords))

import re 
# Step 5: Function to clean text
def clean_text(text):
    # Remove non-alphabetic characters (keep only words)
    text = re.sub(r'[^A-Za-z\s]', '', text)
    # Convert text to lowercase
    text = text.lower()
    return text

# Step 6: Clean all titles (positive, negative, and all combined)
positive_titles_cleaned = clean_text(positive_titles)
negative_titles_cleaned = clean_text(negative_titles)
all_titles_cleaned = clean_text(all_titles)

# Step 7: Function to generate word cloud from cleaned text
def generate_wordcloud(text_data, title, stopwords):
    wordcloud = WordCloud(width=800, height=400, background_color='white', stopwords=stopwords).generate(text_data)
    plt.figure(figsize=(10, 6))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title(title)
    plt.show()
    return wordcloud

# Step 8: Generate word cloud for the full corpus
# generate_wordcloud(all_titles_cleaned, 'Most Salient Words - All Data', stopwords)

# Step 9: Optionally, generate word clouds for positive and negative classes
generate_wordcloud(positive_titles_cleaned, 'Most Salient Words - Positive Sentiment Scored Data', stopwords)
generate_wordcloud(negative_titles_cleaned, 'Most Salient Words - Negative Sentiment Scored Data', stopwords)


 