import telebot
from google import genai
from google.genai import types
from collections import defaultdict
import os
from flask import Flask

# ================== CREDENTIALS FROM RAILWAY ==================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")   
ADMIN_ID = os.environ.get("ADMIN_ID")
# ==============================================================

# Initialize Gemini 2.0 Flash
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = 'gemini-2.5-flash-lite'

# Initialize Telegram bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Chat history storage for each user
chat_history = defaultdict(list)

# ========== Load your info from aboutme.txt once at startup ==========
MY_INFO = ""
if os.path.exists('aboutme.txt'):
    with open('aboutme.txt', 'r', encoding='utf-8') as f:
        MY_INFO = f.read()
else:
    MY_INFO = "aboutme.txt file not found. Please add your info inside it."

# Portfolio URLs
PORTFOLIO_URL = "https://sparkly-kashata-69f510.netlify.app/"
PORTFOLIO_URL2 = "https://incredible-tarsier-1d356b.netlify.app/"
# ==============================================================

def split_and_send(chat_id, text, reply_to_message=None, markup=None):
    max_length = 4000
    for i in range(0, len(text), max_length):
        chunk = text[i:i+max_length]
        if i == 0 and reply_to_message:
            bot.reply_to(reply_to_message, chunk, reply_markup=markup)
        else:
            bot.send_message(chat_id, chunk, reply_markup=markup if i+max_length >= len(text) else None)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    btn_portfolio1 = telebot.types.InlineKeyboardButton(text='Portfolio 1', web_app=telebot.types.WebAppInfo(url=PORTFOLIO_URL))
    btn_portfolio2 = telebot.types.InlineKeyboardButton(text='Portfolio 2', web_app=telebot.types.WebAppInfo(url=PORTFOLIO_URL2))
    btn_presentation = telebot.types.InlineKeyboardButton(text='Show Presentation', callback_data='show_presentation')
    markup.add(btn_portfolio1, btn_portfolio2, btn_presentation)
    
    welcome_msg = """Hello! I am Gemini 2.0 AI Bot 🤖

Send me any question and I will answer you.

Available commands:
/clear - Clear chat history and start fresh
/help - Show this help message"""
    
    bot.send_message(message.chat.id, welcome_msg, reply_markup=markup)

@bot.message_handler(commands=['clear', 'مسح'])
def clear_history(message):
    chat_id = message.chat.id
    chat_history[chat_id] = []
    bot.reply_to(message, "Chat history cleared. Starting fresh 👌")

@bot.callback_query_handler(func=lambda call: call.data == 'show_presentation')
def send_presentation(call):
    chat_id = call.message.chat.id
    try:
        bot.send_chat_action(chat_id, 'upload_video')
        with open('pressentationm1.mp4', 'rb') as video:
            bot.send_video(chat_id, video, caption='Here is my presentation 🎬')
    except FileNotFoundError:
        bot.send_message(chat_id, "pressentationm1.mp4 file not found")
    except Exception as e:
        bot.send_message(chat_id, f"Error sending video: {e}")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    user_text = message.text
    
    if user_text.startswith('/'):
        return
    
    keywords = ['mohamed', 'mohammed', 'who are you', 'tell me about you', 'skills', 'experience', 'cv']
    if any(k in user_text.lower() for k in keywords) and MY_INFO:
        try:
            bot.send_chat_action(chat_id, 'typing')
            summary_prompt = f"""You are Mohamed's portfolio bot.
Use ONLY this info about Mohamed: {MY_INFO}

User question: {user_text}

Rules:
1. Answer in max 2000 characters
2. Make it a short professional summary
3. Use Arabic if user writes Arabic, English if English
4. Focus on skills, experience, and achievements"""
            
            response = client.models.generate_content(model=MODEL_NAME, contents=[types.Content(role="user", parts=[types.Part(text=summary_prompt)])])
            bot_reply = response.text
            split_and_send(chat_id, bot_reply, reply_to_message=message)
            return
        except Exception as e:
            print(f"Summarization Error: {e}")
            bot.reply_to(message, "Error summarizing info. Try again.")
            return
    
    try:
        bot.send_chat_action(chat_id, 'typing')
        chat_history[chat_id].append(types.Content(role="user", parts=[types.Part(text=user_text)]))
        
        response = client.models.generate_content(model=MODEL_NAME, contents=chat_history[chat_id])
        
        bot_reply = response.text
        chat_history[chat_id].append(types.Content(role="model", parts=[types.Part(text=bot_reply)]))
        
        if len(chat_history[chat_id]) > 20:
            chat_history[chat_id] = chat_history[chat_id][-20:]
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        btn_portfolio1 = telebot.types.InlineKeyboardButton(text='Portfolio 1', web_app=telebot.types.WebAppInfo(url=PORTFOLIO_URL))
        btn_portfolio2 = telebot.types.InlineKeyboardButton(text='Portfolio 2', web_app=telebot.types.WebAppInfo(url=PORTFOLIO_URL2))
        btn_presentation = telebot.types.InlineKeyboardButton(text='Show Presentation', callback_data='show_presentation')
        markup.add(btn_portfolio1, btn_portfolio2, btn_presentation)
        
        split_and_send(chat_id, bot_reply, reply_to_message=message, markup=markup)
        
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "An error occurred 😅 Try /clear and start again")

# ========== Flask App for Railway ==========
app = Flask(__name__)

@app.route('/')
def home(): 
    return "Bot is alive on Railway ✅"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
