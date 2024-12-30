import os
from twitter_to_rss import TwitterToRSS
from supabase import create_client
from datetime import datetime
from dotenv import load_dotenv
import tempfile

# Load environment variables
load_dotenv()

# Initialize Supabase client using environment variables
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_KEY')

if not supabase_url or not supabase_key:
    raise ValueError("Missing required environment variables: SUPABASE_URL and SUPABASE_KEY")

supabase = create_client(supabase_url, supabase_key)

def get_existing_usernames():
    """Get usernames from Supabase database"""
    response = supabase.table('my_x_rss').select('username').execute()
    return [record['username'] for record in response.data]

def update_feeds():
    """Update RSS feeds for all existing users"""
    print("Starting RSS feed updates...")
    
    usernames = get_existing_usernames()
    
    if not usernames:
        print("No existing feeds found.")
        return
    
    print(f"Found {len(usernames)} feeds to update")
    
    for username in usernames:
        try:
            print(f"Updating feed for @{username}")
            converter = TwitterToRSS(username)
            rss_content = converter.generate_rss_content()
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.xml', delete=False) as temp_file:
                temp_file.write(rss_content)
                temp_file.flush()
                temp_path = temp_file.name
            
            try:
                # Upload to Supabase Storage
                file_name = f'{username}_feed.xml'
                
                # First try to remove existing file (ignore errors if it doesn't exist)
                try:
                    supabase.storage.from_('my_x_rss').remove([file_name])
                except:
                    pass
                
                # Upload new file
                with open(temp_path, 'rb') as f:
                    storage_response = supabase.storage.from_('my_x_rss').upload(
                        path=file_name,
                        file=f,
                        file_options={"content-type": "application/xml"}
                    )
                
                # Update timestamp in database
                supabase.table('my_x_rss').update({
                    'updated_at': datetime.now().isoformat()
                }).eq('username', username).execute()
                
                print(f"Successfully updated feed for @{username}")
            
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
                
        except Exception as e:
            print(f"Error updating feed for @{username}: {e}")
            continue

if __name__ == "__main__":
    update_feeds() 