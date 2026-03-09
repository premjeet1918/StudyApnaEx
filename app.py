import os
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Running"

def run():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# Flask server start
Thread(target=run).start()

# ---- Telegram Bot Code ----
from pyrogram import Client

bot = Client("mybot")

bot.start()
print("Bot Started")

bot.idle()
