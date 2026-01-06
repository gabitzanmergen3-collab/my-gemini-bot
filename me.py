import os
import logging
import requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters

# --- ВСТАВЬ СВОИ ДАННЫЕ СЮДА ---
TELEGRAM_TOKEN = "8152914738:AAFFWy_i478GceXKqatLDFa2C3f-kaKGkXg"
GEMINI_API_KEY = "AIzaSyAWbeyaPRHeXlsaobOarRTsPl7-IxAvREU"

# 1. Веб-сервер (обманка для Render)
app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run_web():
    # Render дает порт
через переменную окружения, мы должны её поймать
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# 2. Логика бота
user_memory = {}

async def get_ai_answer(user_id, text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

    if user_id not in user_memory: user_memory[user_id] = []
    user_memory[user_id].append({"role": "user", "parts": [{"text": text}]})
    if len(user_memory[user_id]) > 10: user_memory[user_id] = user_memory[user_id][-10:]

    payload = {"contents": user_memory[user_id]}

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            ai_text = response.json()['candidates'][0]['content']['parts'][0]['text']
            user_memory[user_id].append({"role": "model", "parts": [{"text": ai_text}]})
            return ai_text
        return "Ошибка Google"
    except:
        return "Ошибка сети"

async def handle_message(update: Update, context):
    if not update.message or not update.message.text: return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    ans = await get_ai_answer(update.effective_user.id, update.message.text)
    await update.message.reply_text(ans)

if __name__ == '__main__':
    # Сначала запускаем сервер в фоне
    t = Thread(target=run_web)
    t.start()

    # Потом запускаем бота
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.run_polling()
