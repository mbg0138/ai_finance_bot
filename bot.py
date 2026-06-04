import telebot
import sqlite3
import os
import logging
import json # NEW: The universal language bridge!
from dotenv import load_dotenv
from groq import Groq

# --- 1. SETUP LOGGER ---
logging.basicConfig(
    filename='finance_bot.log', 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# --- 2. LOAD ENVIRONMENT VARIABLES ---
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- 3. DATABASE ARCHITECTURE (SQLite) ---
def init_db():
    try:
        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                category TEXT,
                description TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Database initialization failed: {e}")

init_db()

# --- 4. AI DATA EXTRACTOR (Prompt Engineering) ---
def extract_expense_data(user_text):
    client = Groq(api_key=GROQ_API_KEY)
    
    # THE MAGIC PROMPT: Forcing the AI to be a strict machine
    system_prompt = """
    You are a backend data extraction API. 
    Your ONLY job is to extract financial expenses from the user's text and output them in a strict JSON format.
    Do NOT output any markdown blocks (like ```json).
    Do NOT output any greetings, explanations, or conversational text.
    ONLY output the raw JSON array.
    
    Expected JSON format:
    [
        {"amount": 350, "category": "Transport", "description": "taxi"},
        {"amount": 600, "category": "Food", "description": "dinner"}
    ]
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            temperature=0.1 # Low temperature means zero creativity, pure logic!
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Groq API Error: {e}")
        return None

# --- 5. BOT COMMANDS ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 **Welcome!** Just tell me your expenses naturally.")

# Catch all text messages
@bot.message_handler(func=lambda message: True)
def handle_expense(message):
    bot.reply_to(message, "⏳ AI is processing your expense...")
    
    # Step 1: Get raw JSON text from AI
    raw_ai_response = extract_expense_data(message.text)
    
    if not raw_ai_response:
        bot.reply_to(message, "❌ API connection failed.")
        return
        
    try:
        # Step 2: Convert AI string to Python Dictionary (json.loads)
        expenses_data = json.loads(raw_ai_response)
        
        # Step 3: Connect to DB and INSERT data
        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        
        reply_text = "✅ **Expenses Saved to Database!**\n\n"
        
        for expense in expenses_data:
            # SQL INSERT COMMAND
            cursor.execute('''
                INSERT INTO expenses (user_id, amount, category, description)
                VALUES (?, ?, ?, ?)
            ''', (message.chat.id, expense['amount'], expense['category'], expense['description']))
            
            reply_text += f"🔹 {expense['category']}: {expense['amount']} TL ({expense['description']})\n"
            
        conn.commit()
        conn.close()
        
        # Step 4: Show success message to user
        bot.reply_to(message, reply_text, parse_mode="Markdown")
        
    except json.JSONDecodeError:
        bot.reply_to(message, "⚠️ AI did not follow JSON rules. Check logs.")
        logging.error(f"JSON Error. Raw Output: {raw_ai_response}")
    except Exception as e:
        bot.reply_to(message, "❌ Database error occurred.")
        logging.error(f"DB Error: {e}")

print("[SYSTEM ACTIVE] AI Finance Assistant with JSON-SQL Pipeline is running...")
bot.infinity_polling()