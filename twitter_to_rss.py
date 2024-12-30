from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from feedgenerator import Rss201rev2Feed
from datetime import datetime
import time
import re

class TwitterToRSS:
    def __init__(self, username):
        self.username = username
        self.base_url = f"https://twitter.com/{username}"
        
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Initialize the driver
        self.driver = webdriver.Chrome(options=chrome_options)
        
    def fetch_tweets(self, limit=20):
        tweets = []
        try:
            print(f"Fetching tweets from {self.base_url}")
            self.driver.get(self.base_url)
            
            # Wait for tweets to load
            wait = WebDriverWait(self.driver, 10)
            tweet_elements = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-testid="tweet"]'))
            )
            
            # Scroll a bit to load more tweets
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Get tweets
            tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="tweet"]')[:limit]
            
            for element in tweet_elements:
                tweet = {}
                try:
                    # Get tweet text
                    text_element = element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                    tweet['content'] = text_element.text
                    
                    # Get tweet timestamp and link
                    time_element = element.find_element(By.CSS_SELECTOR, 'time')
                    tweet['date'] = time_element.get_attribute('datetime')
                    tweet['link'] = time_element.find_element(By.XPATH, '..').get_attribute('href')
                    
                    tweets.append(tweet)
                except Exception as e:
                    print(f"Error parsing tweet: {str(e)}")
                    continue
            
            return tweets
            
        except Exception as e:
            print(f"Error fetching tweets: {str(e)}")
            return []
        
        finally:
            self.driver.quit()

    def generate_rss(self, output_file='twitter_feed.xml'):
        try:
            tweets = self.fetch_tweets()
            
            if not tweets:
                print("No tweets were found. Creating empty RSS feed.")
            
            feed = Rss201rev2Feed(
                title=f"Twitter Feed for @{self.username}",
                link=self.base_url,
                description=f"Latest tweets from @{self.username}",
                language="en-us"
            )
            
            for tweet in tweets:
                try:
                    feed.add_item(
                        title=tweet['content'][:100] + "..." if len(tweet['content']) > 100 else tweet['content'],
                        link=tweet.get('link', ''),
                        description=tweet['content'],
                        pubdate=datetime.fromisoformat(tweet['date'].replace('Z', '+00:00'))
                    )
                except Exception as e:
                    print(f"Error adding tweet to RSS feed: {e}")
                    continue
            
            with open(output_file, 'w', encoding='utf-8') as f:
                feed.write(f, 'utf-8')
                print(f"RSS feed generated successfully: {output_file}")
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()

    def generate_rss_content(self):
        """Generate RSS content and return as string instead of saving to file"""
        try:
            tweets = self.fetch_tweets()
            
            if not tweets:
                print("No tweets were found. Creating empty RSS feed.")
            
            feed = Rss201rev2Feed(
                title=f"Twitter Feed for @{self.username}",
                link=self.base_url,
                description=f"Latest tweets from @{self.username}",
                language="en-us"
            )
            
            for tweet in tweets:
                try:
                    feed.add_item(
                        title=tweet['content'][:100] + "..." if len(tweet['content']) > 100 else tweet['content'],
                        link=tweet.get('link', ''),
                        description=tweet['content'],
                        pubdate=datetime.fromisoformat(tweet['date'].replace('Z', '+00:00'))
                    )
                except Exception as e:
                    print(f"Error adding tweet to RSS feed: {e}")
                    continue
            
            from io import StringIO
            output = StringIO()
            feed.write(output, 'utf-8')
            return output.getvalue()
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()

def main():
    username = input("Enter Twitter username (without @): ")
    converter = TwitterToRSS(username)
    converter.generate_rss()

if __name__ == "__main__":
    main() 