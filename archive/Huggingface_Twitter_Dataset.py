#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec  8 08:50:26 2024

@author: komalwavhal
"""

# import pandas as pd
# Twitter Data:( https://huggingface.co/datasets/StephanAkkerman/financial-tweets-crypto , https://huggingface.co/datasets/tmotagam/Cryptocurrencies-sentiment-from-X/tree/main ) 


# ========== twitter data from huggingface==============
# https://huggingface.co/datasets/StephanAkkerman/financial-tweets-crypto 
# df = pd.read_csv("hf://datasets/StephanAkkerman/financial-tweets-crypto/crypto.csv")
# print(f"Dataset loaded with {len(df)} rows.")
# return df


# from datasets import load_dataset
# https://huggingface.co/datasets/SahandNZ/cryptonews-articles-with-price-momentum-labels 
# splits = {'train': 'train.csv', 'validation': 'validation.csv', 'test': 'test.csv'}
# df = pd.read_csv("hf://datasets/SahandNZ/cryptonews-articles-with-price-momentum-labels/" + splits["train"])




import pandas as pd
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
# from datasets import load_dataset
from openpyxl import Workbook

# Download the VADER lexicon if not already downloaded
nltk.download('vader_lexicon')

# Initialize Sentiment Intensity Analyzer
sia = SentimentIntensityAnalyzer()

# Load the Hugging Face dataset
def load_data():
        
    df = pd.read_csv("hf://datasets/StephanAkkerman/financial-tweets-crypto/crypto.csv")
     
    print(f"Dataset loaded with {len(df)} rows.")
    return df

def analyze_sentiment(df):
    sentiments = []
    sentiment_percentages = []

    # Iterate over the comments
    for comment in df['description']:
        if isinstance(comment, str):  # Only process if the comment is a string
            sentiment_score = sia.polarity_scores(comment)
            compound_score = sentiment_score['compound']

            # Categorize sentiment based on the compound score
            if compound_score >= 0.05:
                sentiment = 'Positive'
            elif compound_score <= -0.05:
                sentiment = 'Negative'
            else:
                sentiment = 'Neutral'

            # Calculate sentiment percentage (normalize to 0-100 scale)
            sentiment_percentage = round((compound_score + 1) * 50, 2)

            sentiments.append(sentiment)
            sentiment_percentages.append(sentiment_percentage)
        else:
            # If the comment is not a string (e.g., NaN or float), append 'Unknown' and 0%
            sentiments.append('Unknown')
            sentiment_percentages.append(0.0)

    # After the loop, assign the lists to the DataFrame columns
    df['sentiment_analysis'] = sentiments
    df['sentiment_percentage'] = sentiment_percentages



    # List of columns to delete (remove unwanted columns from the DataFrame)
    columns_to_delete = ['image_url', 'proxy_image_url', 'image_dimensions', 
                         'thumbnail_url', 'proxy_thumbnail_url', 'thumbnail_dimensions',
                         'url', 'embed_title', 'tweet_type', 'sentiment']
    
    # Drop the unwanted columns
    df.drop(columns=columns_to_delete, inplace=True)
    
    
    return( df)


# Save the DataFrame to an Excel file
def save_to_excel(df, filename="crypto_comments_with_sentiment.xlsx"):
    # df.to_excel(filename, index=False)

    # Select only the desired columns
    df_filtered = df[['timestamp', 'description', 'financial_info', 'sentiment_analysis', 'sentiment_percentage']]
    
    # Save the filtered DataFrame to an Excel file
    df_filtered.to_excel(filename, index=False)
    
    
    
    print(f"Data saved to {filename}")

# Main function
def main():
    # Step 1: Load the dataset
    df = load_data()
    print(df.columns.tolist())
    # Dataset loaded with 57935 rows.
    # ['image_url', 'proxy_image_url', 'image_dimensions', 'thumbnail_url', 'proxy_thumbnail_url', 'thumbnail_dimensions', 'timestamp', 'description', 'url', 'embed_title', 'tweet_type', 'financial_info', 'sentiment']
    
    # # Step 2: Extract relevant columns 
    
    # Step 3: Perform sentiment analysis
    df_with_sentiment = analyze_sentiment(df)
    
    # Step 4: Save the result to an Excel file
    save_to_excel(df_with_sentiment)

if __name__ == "__main__":
    main()











import pandas as pd

splits = {'train': 'train.csv', 'validation': 'validation.csv', 'test': 'test.csv'}
df = pd.read_csv("hf://datasets/SahandNZ/cryptonews-articles-with-price-momentum-labels/" + splits["train"])

 
print(df.columns.tolist())

# ['datetime', 'text', 'url', 'label']
### url has name of cryptocurrency
# text is comments







