from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from twitter_to_rss import TwitterToRSS
from supabase import create_client
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Replace with a real secret key

# Initialize Supabase client
supabase_url = 'https://vyfeecfsnvjanhzaojvq.supabase.co'  # Your project URL
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ5ZmVlY2ZzbnZqYW5oemFvanZxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNDM0MDExNywiZXhwIjoyMDQ5OTE2MTE3fQ.cBjja9V92dT0-QYmNfIXEgCU00vE91ZXEetTyc-dmBM'  # Your API key
supabase = create_client(supabase_url, supabase_key)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username')
        if username:
            try:
                converter = TwitterToRSS(username)
                # Generate RSS content in memory
                rss_content = converter.generate_rss_content()
                
                # Upload to Supabase Storage
                file_name = f'{username}_feed.xml'
                storage_response = supabase.storage.from_('my_x_rss').upload(
                    file_name,
                    rss_content.encode()
                )
                
                # Get public URL
                public_url = supabase.storage.from_('my_x_rss').get_public_url(file_name)
                
                # Save to Supabase database
                feed_data = {
                    'username': username,
                    'feed_url': public_url,
                    'created_at': datetime.now().isoformat()
                }
                supabase.table('my_x_rss').insert(feed_data).execute()
                
                return redirect(url_for('download', username=username))
            except Exception as e:
                flash(f'Error: {str(e)}', 'error')
                return redirect(url_for('index'))
    return render_template('index.html')

@app.route('/download/<username>')
def download(username):
    try:
        # Get feed URL from Supabase database
        response = supabase.table('my_x_rss').select('feed_url').eq('username', username).execute()
        if response.data:
            feed_url = response.data[0]['feed_url']
            return render_template('download.html', username=username, feed_url=feed_url)
        flash('Feed not found', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) 