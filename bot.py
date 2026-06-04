import telebot
import sqlite3
import os
import logging
from dotenv import load_dotenv

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
    """Initializes the database and creates the expenses table if it doesn't exist."""
    try:
        # Connects to the database file (creates it if not exists)
        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        
        # Create Table (SQL Code)
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
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Database initialization failed: {e}")

# Run database setup on startup
init_db()

# --- 4. BOT COMMANDS ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 **Welcome to your AI Financial CFO!**\n\n"
        "Just tell me what you spent money on naturally.\n"
        "Example: *'I spent 350 TL on a taxi and 600 TL for dinner.'*\n\n"
        "I will extract the data, categorize it, and save it to the database automatically."
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

print("[SYSTEM ACTIVE] Finance Bot and Database are ready...")
bot.infinity_polling()