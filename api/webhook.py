from flask import Flask, request, abort
import telebot
import os
import sys

# Add parent directory to sys.path so we can import from the root directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram_bot import bot

app = Flask(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        abort(403)

@app.route('/')
def index():
    return 'ClearLink-PDF Bot is running!', 200

@app.route('/setup')
def setup_webhook():
    if not BOT_TOKEN:
        return 'BOT_TOKEN environment variable is missing', 500
    
    # Get the URL of the Vercel deployment automatically
    host = request.headers.get('Host')
    webhook_url = f"https://{host}/"
    
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    
    return f"Webhook successfully set to {webhook_url}", 200

# Vercel requires the app variable to be named `app`
if __name__ == '__main__':
    app.run(debug=True)
