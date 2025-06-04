#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec  8 07:26:07 2024

@author: komalwavhal
"""

import praw
import pandas as pd
import time
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from openpyxl import Workbook 
import praw
import pandas as pd
from datetime import datetime
import asyncpraw
import pandas as pd
import asyncio
from datetime import datetime
import asyncpraw
import asyncio
import requests 
import pandas as pd 
from nltk.sentiment import SentimentIntensityAnalyzer 
import time 
import nltk 
from datetime import datetime
 

# ################################################################################################################
 
   
# client_id='KJa61RdZeAQ6VRq9NfiElQ',         # Replace with your Reddit app's client ID
# client_secret='PJ84Psahlrl0o9TqY7fpWpcxO1BScg', # Replace with your Reddit app's client secret
# user_agent='Testing_APIs'        # Replace with your user agent (a string describing your app)



# Download the VADER lexicon if not already downloaded 
nltk.download('vader_lexicon')

# Initialize the Sentiment Intensity Analyzer 
sia = SentimentIntensityAnalyzer() 

# Function to collect news data from News API 
def collect_news(api_key, query='cryptocurrency', max_articles=10000): 
    base_url = 'https://newsapi.org/v2/everything' 
    all_articles = [] 
    page_size = 100  # Maximum number of articles per API call 
    page = 1
  
    while len(all_articles) < max_articles: 
        params = { 
            'q': query, 
            'pageSize': page_size, 
            'page': page, 
            'apiKey': api_key, 
            'language': 'en', 
            'sortBy': 'publishedAt' 
        } 
        response = requests.get(base_url, params=params) 
        data = response.json() 
         
        if response.status_code != 200 or not data.get('articles'): 
            print("Error or no more articles to fetch.") 
            break 
         
        articles = data['articles'] 
        all_articles.extend(articles) 
        print(f"Fetched {len(articles)} articles from page {page}") 
        page += 1 
         
        time.sleep(1)  # Sleep to avoid hitting the API rate limit 
  
    return all_articles 
  
# Function to perform sentiment analysis on articles 
def analyze_sentiment(articles): 
    for article in articles:
        text = article['title'] + ' ' + article['description']  # Combine title and description
        sentiment_score = sia.polarity_scores(text) 
        compound_score = sentiment_score['compound']

        # Categorize sentiment based on the compound score
        if compound_score >= 0.05:
            sentiment = 'Positive'
        elif compound_score <= -0.05:
            sentiment = 'Negative'
        else:
            sentiment = 'Neutral'
        
        # Calculate sentiment percentage (here, we consider compound score range as percentage)
        sentiment_percentage = round((compound_score + 1) * 50, 2)  # Normalize to 0-100 scale
        
        # Add sentiment and sentiment percentage to the article
        article['sentiment'] = sentiment
        article['sentiment_percentage'] = sentiment_percentage
    
    return articles 
  
# Function to save the data to an Excel file with naming convention
def save_to_excel(articles, cryptocurrency_name, start_year, end_year): 
    # Create the filename with the required convention
    filename = f"{cryptocurrency_name}_crypto_news_data_{start_year}_{end_year}_with_sentiment.xlsx"
    
    # Prepare data to be saved into Excel
    data = []
    for article in articles:
        # Extract necessary information
        cryptocurrency = cryptocurrency_name
        comments = article['title'] + ' ' + article['description']
        # Extract the year from the published date (in format '%Y-%m-%d')
        year = datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').year
        date_of_comment = article['publishedAt']
        sentiment = article['sentiment']
        sentiment_percentage = article['sentiment_percentage']
        
        # Append row to data list
        data.append([cryptocurrency, comments, year, date_of_comment, sentiment, sentiment_percentage])
    
    # Create a DataFrame and save to Excel
    df = pd.DataFrame(data, columns=['cryptocurrency_name', 'comments','year', 'date_of_comment', 'sentiment_analysis', 'sentiment_percentage'])
    df.to_excel(filename, index=False) 
    print(f"Data saved to {filename}") 
  
# Main function 
def main(): 
    api_key = '4bb96d8cba79431d814ce24607c72372'  # Replace with your News API key
    cryptocurrency_name = 'BTC'  # For example, Bitcoin
    start_year = 2023
    end_year = 2023
    
    # Collect the news articles
    articles = collect_news(api_key, query=cryptocurrency_name, max_articles=10000)
    
    # Analyze sentiment of articles
    articles_with_sentiment = analyze_sentiment(articles)
    
    # Save to Excel with the given file naming convention
    save_to_excel(articles_with_sentiment, cryptocurrency_name, start_year, end_year)
  
if __name__ == '__main__': 
    main()

 