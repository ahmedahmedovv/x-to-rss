from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from twitter_to_rss import TwitterToRSS
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Replace with a real secret key

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username')
        if username:
            try:
                converter = TwitterToRSS(username)
                output_file = f'static/feeds/{username}_feed.xml'
                os.makedirs('static/feeds', exist_ok=True)
                converter.generate_rss(output_file)
                return redirect(url_for('download', username=username))
            except Exception as e:
                flash(f'Error: {str(e)}', 'error')
                return redirect(url_for('index'))
    return render_template('index.html')

@app.route('/download/<username>')
def download(username):
    feed_file = f'static/feeds/{username}_feed.xml'
    if os.path.exists(feed_file):
        return render_template('download.html', username=username, feed_url=feed_file)
    flash('Feed not found', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) 