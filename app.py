import logging
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from twitter_to_rss import TwitterToRSS
from supabase import create_client
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')

# Initialize Supabase client using environment variables
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_KEY')
supabase = create_client(supabase_url, supabase_key)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username')
        if not username:
            flash('Please enter a username', 'error')
            return redirect(url_for('index'))
            
        try:
            logger.info(f"Starting RSS generation for user: {username}")
            converter = TwitterToRSS(username)
            rss_content = converter.generate_rss_content()
            
            if not isinstance(rss_content, str):
                logger.error(f"RSS content is not a string: {type(rss_content)}")
                raise ValueError("Failed to generate RSS content")
            
            logger.info(f"RSS content generated successfully for {username}")
            
            # Upload to Supabase Storage
            file_name = f'{username}_feed.xml'
            try:
                # First, try to create the bucket if it doesn't exist
                try:
                    logger.info("Attempting to create bucket 'my_x_rss'")
                    supabase.storage.create_bucket('my_x_rss', {'public': True})
                    logger.info("Bucket created successfully")
                except Exception as bucket_error:
                    logger.info(f"Bucket creation skipped (might already exist): {str(bucket_error)}")
                
                # List buckets to verify
                buckets = supabase.storage.list_buckets()
                logger.info(f"Available buckets: {buckets}")
                
                # Try to upload the file
                logger.info(f"Attempting to upload file: {file_name}")
                
                # Delete the file if it exists (to avoid conflicts)
                try:
                    supabase.storage.from_('my_x_rss').remove([file_name])
                    logger.info("Removed existing file")
                except Exception as remove_error:
                    logger.info(f"No existing file to remove: {str(remove_error)}")
                
                # Upload new file
                storage_response = supabase.storage.from_('my_x_rss').upload(
                    path=file_name,
                    file=rss_content.encode('utf-8'),
                    file_options={"contentType": "application/xml"}
                )
                logger.info(f"Upload response: {storage_response}")
                
            except Exception as storage_error:
                error_msg = f"Storage error: {str(storage_error)}"
                logger.error(error_msg)
                flash(f'Error saving RSS feed to storage: {error_msg}', 'error')
                return redirect(url_for('index'))
            
            # Get public URL
            public_url = f"https://vyfeecfsnvjanhzaojvq.supabase.co/storage/v1/object/public/my_x_rss/{file_name}"
            logger.info(f"Generated public URL: {public_url}")
            
            try:
                # Save to Supabase database
                feed_data = {
                    'username': username,
                    'feed_url': public_url,
                    'created_at': datetime.now().isoformat()
                }
                db_response = supabase.table('my_x_rss').insert(feed_data).execute()
                logger.info(f"Database insert response: {db_response}")
            except Exception as db_error:
                error_msg = f"Database error: {str(db_error)}"
                logger.error(error_msg)
                flash(f'Error saving feed information: {error_msg}', 'error')
                return redirect(url_for('index'))
            
            return redirect(url_for('download', username=username))
            
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            logger.error(error_msg)
            flash(f'Error: Unable to generate RSS feed: {error_msg}', 'error')
            return redirect(url_for('index'))
            
    return render_template('index.html')

@app.route('/download/<username>')
def download(username):
    try:
        logger.info(f"Fetching feed URL for username: {username}")
        response = supabase.table('my_x_rss').select('feed_url').eq('username', username).execute()
        if response.data:
            feed_url = response.data[0]['feed_url']
            logger.info(f"Found feed URL: {feed_url}")
            return render_template('download.html', username=username, feed_url=feed_url)
        logger.error(f"No feed found for username: {username}")
        flash('Feed not found', 'error')
    except Exception as e:
        error_msg = f"Error retrieving feed: {str(e)}"
        logger.error(error_msg)
        flash(f'Error: {error_msg}', 'error')
    return redirect(url_for('index'))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 