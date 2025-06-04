#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec  8 05:56:49 2024

@author: komalwavhal
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import pandas as pd
import time
import random 
import calendar
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class CryptoData_Google_News( ):
    

    # Function to scrape Google News dynamically for a specific cryptocurrency
    def get_GoogleNews_Data(self, crypto_name, start_year, end_year):
        query = crypto_name
        print(f"Running Google News crypto data download for {crypto_name} from {start_year} to {end_year}")

        # Initialize the WebDriver
        options = webdriver.ChromeOptions()
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        all_news_data = []

        # Set zoom level to 25%
        driver.get('about:blank')  # Go to a blank page first
        driver.execute_script("document.body.style.zoom='25%'")  # Set zoom to 25%

        def days_in_month(year, month):
            return calendar.monthrange(year, month)[1]

        # Scrape data for the given year range
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):  # Scrape by month
                start_date = f"{year}-{month:02d}-01"
                end_date = f"{year}-{month:02d}-{days_in_month(year, month)}"
                url = f'https://news.google.com/search?q={query.replace(" ", "+")}+after%3A{start_date}+before%3A{end_date}&hl=en-US&gl=US&ceid=US:en'
                print(f"Fetching news for {crypto_name} from {start_date} to {end_date}")

                # Navigate to URL
                driver.get(url)
                time.sleep(random.uniform(2, 4))  # Add randomness to delay to avoid detection
                 
                
                # Collect news articles for the given month
                news_data = []
                articles = driver.find_elements(By.CSS_SELECTOR, 'article')
                for article in articles:
                    try:
                        title_element = article.find_element(By.CSS_SELECTOR, 'a.JtKRv')
                        title = title_element.text
                        raw_date = article.find_element(By.CSS_SELECTOR, 'time').get_attribute('datetime')
                        date = datetime.strptime(raw_date, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
                        # Create a row with Cryptocurrency Name, Comments (Title), and Year and Date
                        news_data.append({'Cryptocurrency Name': query, 'Comments': title, 'Year and Date': date})
                    except Exception as e:
                        print(f"Error extracting article data: {e}")
                        continue

                # Add collected data to all_news_data
                if news_data:
                    all_news_data.append(pd.DataFrame(news_data))

        # Close the driver after scraping
        driver.quit()
        
        # Return the consolidated data as a DataFrame
        return pd.concat(all_news_data, ignore_index=True) if all_news_data else pd.DataFrame()

    # Function to perform sentiment analysis on the comments (titles)
    def perform_sentiment_analysis(self, df):
        
        """
        1. VADER Sentiment Analysis (Valence Aware Dictionary and sEntiment Reasoner)
        Best for: Social media, news articles, and short text.
        Pros:
        Very fast and efficient.
        Works well on short text, such as tweets, product reviews, and news headlines.
        Pre-trained model, easy to use without requiring extensive customization.
        Handles emojis and slang well.
        Cons:
        Less accurate on longer, more complex texts (e.g., detailed articles or nuanced opinions).

        """
        
        
        
        analyzer = SentimentIntensityAnalyzer()

        # Perform sentiment analysis for each comment (news title)
        df['Sentiment Analysis'] = df['Comments'].apply(lambda x: 'positive' if analyzer.polarity_scores(x)['compound'] >= 0.05
                                                       else 'negative' if analyzer.polarity_scores(x)['compound'] <= -0.05
                                                       else 'neutral')

        # Add the sentiment score (compound score)
        df['Score'] = df['Comments'].apply(lambda x: analyzer.polarity_scores(x)['compound'])

        return df

    def GoogleNews_Data(self, crypto_name, start_year, end_year):
        print(f"Starting Google News data scraping for {crypto_name} from {start_year} to {end_year}")
        
        # Fetch the data
        df = self.get_GoogleNews_Data(crypto_name, start_year, end_year)
        
        if not df.empty:
            print(f"Data scraped successfully for {crypto_name} from {start_year} to {end_year}.")
            
            # Perform sentiment analysis on the scraped data
            df = self.perform_sentiment_analysis(df)
            
            # Save the data to an Excel file
            filename = f'{crypto_name}_crypto_news_data_{start_year}_{end_year}_with_sentiment.xlsx'
            df.to_excel(filename, index=False)
            print(f"All data scraped, sentiment analysis performed, and saved to '{filename}'.")
        else:
            print(f"No data found for {crypto_name} from {start_year} to {end_year}.")


 
        
        
        
    
    
    
    
    
    
    
    