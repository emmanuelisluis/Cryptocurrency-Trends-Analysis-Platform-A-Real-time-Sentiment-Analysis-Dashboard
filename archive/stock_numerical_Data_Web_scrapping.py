#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec  8 13:32:54 2024

@author: komalwavhal
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import pandas as pd

def getStocks(page_url):
    
    driver = webdriver.Chrome()  
    driver.get(page_url)

    stocks = []  

    while True:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody"))
        )

        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")  # Adjust the selector as necessary
        print(f"Found {len(rows)} rows on this page.")

        for row in rows:
            # Extract desired data from each row
            cells = row.find_elements(By.TAG_NAME, "td")  # Adjust if necessary
            row_data = [cell.text for cell in cells]
            stocks.append(row_data) 

        # Check if there is a "Next" button or link to navigate to the next page
        try:
            next_button = driver.find_element(By.LINK_TEXT, "Next")  # Adjust if necessary
            next_button.click()
            WebDriverWait(driver, 10).until(
                EC.staleness_of(rows[0])  # Wait until the old rows are gone
            )
        except NoSuchElementException:
            print("No more pages to scrape.")
            break  # Exit loop if no next button is found

    driver.quit()  
    return stocks


if __name__ == "__main__":
    crypto_to_scrape = {
                    'BTC' : 'https://finance.yahoo.com/quote/BTC-USD/history/?period1=1410912000&period2=1730509639',
                    'ETH' : 'https://finance.yahoo.com/quote/ETH-USD/history/?period1=1510185600&period2=1730520709', 
                    'USDT' : 'https://finance.yahoo.com/quote/USDT-USD/history/?period1=1510185600&period2=1730520738',
                    'BNB' : 'https://finance.yahoo.com/quote/BNB-USD/history/?period1=1510185600&period2=1730520774',
                    'SOL' : 'https://finance.yahoo.com/quote/SOL-USD/history/?period1=1586476800&period2=1730520797',
                    'USDC' : 'https://finance.yahoo.com/quote/USDC-USD/history/?period1=1538956800&period2=1730520819',
                    'XRP' : 'https://finance.yahoo.com/quote/XRP-USD/history/?period1=1510185600&period2=1730520841',
                    'STETH' : 'https://finance.yahoo.com/quote/STETH-USD/history/?period1=1608681600&period2=1730520879',
                    'DOGE' : 'https://finance.yahoo.com/quote/DOGE-USD/history/?period1=1510185600&period2=1730520898',
                    'TRX' : 'https://finance.yahoo.com/quote/TRX-USD/history/?period1=1510185600&period2=1730520957'
    }


    for c in crypto_to_scrape.keys():
        reviews_data = getStocks(crypto_to_scrape[c])
        df = pd.DataFrame(reviews_data, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])
        df.to_csv(f"./StocksData/{c}_Stocks_Scrapped.csv")
