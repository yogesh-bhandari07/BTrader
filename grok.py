import os
import schedule
import time
import re
from telegram import Bot
from dotenv import load_dotenv
import datetime
import asyncio
import logging
import requests

logging.basicConfig(
    filename="nifty_bot.log",
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
)

# List of NSE trading holidays for 2025
NSE_HOLIDAYS_2025 = {
    "2025-02-26", "2025-03-14", "2025-03-31", "2025-04-10", "2025-04-14",
    "2025-04-18", "2025-05-01", "2025-08-15", "2025-08-27", "2025-10-02",
    "2025-10-21", "2025-10-22", "2025-11-05", "2025-12-25",
}

def is_market_closed_today():
    today = datetime.date.today()
    weekday = today.weekday()  # Monday=0, Sunday=6
    is_weekend = weekday >= 5
    is_holiday = today.isoformat() in NSE_HOLIDAYS_2025
    return is_weekend or is_holiday

# Load environment variables
load_dotenv()

# Config values
XAI_API_KEY = os.getenv("XAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TELEGRAM_BOT_TOKEN)

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


def ask_grok(prompt):
    try:
        logging.info(f"Sending prompt to Grok:\n{prompt}")
        headers = {
            "Authorization": f"Bearer {XAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "grok-3",  # Assuming Grok 3 is the model name
            "messages": [
                {"role": "system", "content": "Act as a professional NIFTY options trader and market analyst."},
                {"role": "user", "content": prompt}
            ]
        }
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",  # Replace with actual xAI API endpoint if different
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        response_data = response.json()

        if not response_data or not response_data.get("choices"):
            raise ValueError("No valid response from Grok")

        grok_response = response_data["choices"][0]["message"]["content"].strip()
        logging.info("Grok Response:\n%s", grok_response)
        return grok_response

    except Exception as e:
        logging.error("Grok Error: %s", str(e))
        return f"Grok Error: {e}"

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
            "Volume Surge: ": "",
            "VIX:": "",
            "Price Action": "",
            "Momentum": "",
            "reason": match.group("reason").strip()
        })
    return trades

def select_highest_confidence(trades):
    if not trades:
        return None
    return max(trades, key=lambda x: int(x["Confidence Level"]))

async def async_send_message(message):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
    except Exception as e:
        print(f"Telegram Error: {e}")

def send_to_telegram(message):
    asyncio.run(async_send_message(message))

def run_task():
    print("Running scheduled job...")
    if is_market_closed_today():
        logging.info("Market closed today. Skipping job.")
        return
    raw_response = ask_grok(PROMPT)
    trades = extract_trades(raw_response)
    best_trade = select_highest_confidence(trades)

    if best_trade:
        formatted = "\n".join([f"*{k}* {v}" for k, v in best_trade.items()])
        send_to_telegram(f"*NIFTY Trade Alert (Highest Confidence)*\n\n{formatted}")
    else:
        send_to_telegram("No valid trade found in the Grok response.")

# Run every 30 seconds (for testing); change to every 15 minutes for production
schedule.every(30).seconds.do(run_task)

print("Running NIFTY Options Alert Bot...")
while True:
    schedule.run_pending()
    time.sleep(1)