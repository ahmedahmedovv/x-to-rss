import os
from twitter_to_rss import TwitterToRSS
import xml.etree.ElementTree as ET
import glob

def get_existing_usernames():
    """Get usernames from existing RSS files in the feeds directory"""
    feed_files = glob.glob('static/feeds/*_feed.xml')
    usernames = []
    
    for file in feed_files:
        try:
            # Extract username from filename (username_feed.xml)
            username = os.path.basename(file).replace('_feed.xml', '')
            usernames.append(username)
        except Exception as e:
            print(f"Error processing file {file}: {e}")
            continue
            
    return usernames

def update_feeds():
    """Update RSS feeds for all existing users"""
    print("Starting RSS feed updates...")
    
    # Ensure feeds directory exists
    os.makedirs('static/feeds', exist_ok=True)
    
    # Get list of usernames from existing feeds
    usernames = get_existing_usernames()
    
    if not usernames:
        print("No existing feeds found.")
        return
    
    print(f"Found {len(usernames)} feeds to update")
    
    # Update each feed
    for username in usernames:
        try:
            print(f"Updating feed for @{username}")
            converter = TwitterToRSS(username)
            output_file = f'static/feeds/{username}_feed.xml'
            converter.generate_rss(output_file)
            print(f"Successfully updated feed for @{username}")
        except Exception as e:
            print(f"Error updating feed for @{username}: {e}")
            continue

if __name__ == "__main__":
    update_feeds() 