import os
import openai
import schedule
import time
import re
from telegram import Bot
from dotenv import load_dotenv
import datetime
import asyncio
import logging
from openai import OpenAI
logging.basicConfig(
    filename="nifty_bot.log",
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
)
# List of NSE trading holidays for 2025
NSE_HOLIDAYS_2025 = {
    "2025-02-26", 
    "2025-03-14", 
    "2025-03-31", 
    "2025-04-10", 
    "2025-04-14", 
    "2025-04-18", 
    "2025-05-01", 
    "2025-08-15", 
    "2025-08-27", 
    "2025-10-02", 
    "2025-10-21", 
    "2025-10-22", 
    "2025-11-05", 
    "2025-12-25", 
}

def is_market_closed_today():
    today = datetime.date.today()
    weekday = today.weekday()  # Monday=0, Sunday=6
    is_weekend = weekday >= 5  # Saturday=5, Sunday=6
    is_holiday = today.isoformat() in NSE_HOLIDAYS_2025
    return is_weekend or is_holiday

# Load environment variables
load_dotenv()

# Config values
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# The prompt to submit every 15 minutes
PROMPT = """Act as a professional NIFTY options trader and market analyst. Based on current market conditions (today’s data), give me the best intraday options trade on NIFTY index. Include only 1–2 high-probability trades.
For each option trade, include the following:
1. Option Type (CE or PE)
2. Strike Price
3. Premium Entry Range
4. Target(s)
5. Stop Loss
6. Ideal Entry Time
7. Ideal Exit Time
8. Confidence Level in % (based on OI, volume, trend, VIX, price action, etc.)
9. Key Factors (OI analysis, PCR, trend, support/resistance, candle patterns, news flow, etc.)
10. Short Reason Why this trade setup is good today
Only include trades with strong confirmation from price action + OI shift + volume + momentum indicators. Prefer same day expiry (if Thursday), and ATM/1 strike ITM trades with good liquidity. Be concise, practical and avoid risky trades."""
def ask_chatgpt(prompt):
    try:
        logging.info(f"Sending prompt to ChatGPT:\n{prompt}")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # or "gpt-4"
            messages=[
                {"role": "system", "content": "Act as a professional NIFTY options trader and market analyst."},
                {"role": "user", "content": prompt}
            ]
        )
        if not response or not response.choices:
            raise ValueError("No valid response from ChatGPT")

        chatgpt_response = response.choices[0].message.content.strip()
        logging.info("ChatGPT Response:\n%s", chatgpt_response)
        return chatgpt_response

    except Exception as e:
        logging.error("ChatGPT Error: %s", str(e))
        return f"ChatGPT Error: {e}"

def extract_trades(text):
    trades = []
    pattern = re.compile(
        r"Option Type:\s*(?P<type>CE|PE).*?"
        r"Strike Price:\s*(?P<strike>[\d,]+).*?"
        r"Premium Entry Range:\s*(?P<entry>₹?[\d–\-to ]+).*?"
        r"Target\(s\):\s*(?P<target>₹?[\d–\-to ]+).*?"
        r"Stop Loss:\s*(?P<sl>₹?[\d–\-to ]+).*?"
        r"Ideal Entry Time:\s*(?P<entry_time>[\d:–to ]+).*?"
        r"Ideal Exit Time:\s*(?P<exit_time>[\d:–to ]+).*?"
        r"Confidence Level:\s*(?P<confidence>\d+)%.*?"
        r"Key Factors:\s*(?P<keyfactors>.*?)(?=Short Reason:|$).*?"
        r"Short Reason:\s*(?P<reason>.*?)(?=\n\d|$)",
        re.DOTALL
    )
    for match in pattern.finditer(text):
        trades.append({
            "Option Type": match.group("type").strip(),
            "Strike Price": match.group("strike").strip(),
            "Premium Entry Range": match.group("entry").strip(),
            "Target(s)": match.group("target").strip(),
            "Stop Loss": match.group("sl").strip(),
            "Ideal Entry Time": match.group("entry_time").strip(),
            "Ideal Exit Time": match.group("exit_time").strip(),
            "Confidence Level": match.group("confidence").strip(),
            "Volume Surge: ": "",  # optional to extract
            "VIX:": "",            # optional to extract
            "Price Action": "",    # optional to extract
            "Momentum": "",        # optional to extract
            "reason": match.group("reason").strip()
        })
    return trades

def select_highest_confidence(trades):
    if not trades:
        return None
    return max(trades, key=lambda x: int(x["Confidence Level"]))

async def async_send_message(message):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        print(f"Telegram Error: {e}")



def send_to_telegram(message):
    asyncio.run(async_send_message(message))

def run_task():
    print("Running scheduled job...")
    if is_market_closed_today():
        return
    raw_response = ask_chatgpt(PROMPT)
    trades = extract_trades(raw_response)
    best_trade = select_highest_confidence(trades)
    
    if best_trade:
        formatted = "\n".join([f"{k}: {v}" for k, v in best_trade.items()])
        send_to_telegram("🔔 *NIFTY Trade Alert (Highest Confidence)*\n\n" + formatted)
    else:
        send_to_telegram("No valid trade found in the ChatGPT response.")

# Schedule every 15 minutes
schedule.every(30).seconds.do(run_task)

print("Running NIFTY Options Alert Bot...")
while True:
    schedule.run_pending()
    time.sleep(1)
