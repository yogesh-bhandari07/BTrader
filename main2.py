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

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from selenium.common.exceptions import (
    StaleElementReferenceException,
    ElementClickInterceptedException,
    NoSuchElementException,
)



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
PROMPT = """Act as a professional NIFTY options trader and market strategist. Based strictly on today’s live market data (price action, OI, volume, momentum, VIX, and institutional activity), provide 1–2 high-probability intraday trades on the NIFTY index options. Only suggest trades with strong confluence of the following: 1. OI shift and unwinding at key strikes 2. Volume confirmation 3. Clear intraday price action (breakout, reversal, or retest pattern) 4. Support/resistance zones 5. Momentum alignment (RSI, MACD, VWAP, etc.) 6. Institutional flow (FIIs/DIIs), news, or macro cues 7. Avoid trades with low liquidity or weak conviction 8. Focus on ATM or 1-strike ITM options, preferably same-day expiry if Thursday, with strong delta and good liquidity. For each trade, provide: 1. Option Type (CE or PE) 2. Strike Price 3. Premium Entry Range 4. Target(s) 5. Stop Loss 6. Ideal Entry Time 7. Ideal Exit Time 8. Confidence Level (%) (based on confluence of data) 9. Key Technical + Derivative Factors (OI/PCR, support/resistance, trend, candle patterns, etc.) 10. Short Justification (why this setup is valid today) Only share trades with clean risk-reward, momentum confirmation, and derivative strength. Avoid directional bias unless validated by data.
"""



from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# CONFIG
CHROMEDRIVER_PATH = r"C:\Users\Acer\Downloads\chromedriver-win64 (1)\chromedriver-win64\chromedriver.exe"  # <-- Replace with your path
USER_DATA_DIR = r"C:\Users\Acer\AppData\Local\Google\Chrome\User Data\SeleniumProfile"
CHATGPT_URL = "https://chatgpt.com/c/6860f6df-544c-8007-849c-8c2a4dee1c33"


def handle_retry(driver):
    try:
        # Check if the error message is present
        error_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Something went wrong')]")
        if error_elements:
            print("⚠️ Detected 'Something went wrong' error. Trying to retry...")

            # Try clicking the Retry button
            retry_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Retry')]")
            if retry_buttons:
                retry_buttons[0].click()
                print("🔄 Clicked Retry button.")
                return True
            else:
                print("❌ Retry button not found even though error was detected.")
        return False
    except Exception as e:
        print(f"Retry handling error: {e}")
        return False


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
import time


def close_auth_popup(driver):
    """
    Closes ChatGPT's login/signup popups like 'Stay logged out', 'Continue', etc.,
    by clicking both <button> and <a> elements with common texts.
    """
    try:
        wait = WebDriverWait(driver, 5)
        elements = wait.until(
            EC.presence_of_all_elements_located(
                (
                    By.XPATH,
                    '//button[contains(translate(text(),"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz"), "stay logged out") '
                    'or contains(translate(text(),"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz"), "continue") '
                    'or contains(translate(text(),"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz"), "got it") '
                    'or contains(translate(text(),"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz"), "dismiss") '
                    'or contains(translate(text(),"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz"), "okay")]'
                    '| //a[contains(translate(text(),"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz"), "stay logged out") '
                    'or contains(translate(text(),"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz"), "continue") '
                    'or contains(translate(text(),"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz"), "got it") '
                    'or contains(translate(text(),"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz"), "dismiss") '
                    'or contains(translate(text(),"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz"), "okay")]'
                )
            )
        )
        for el in elements:
            try:
                el.click()
                print(f"🛑 Closed popup element: '{el.text.strip()}'")
            except Exception as e:
                print(f"⚠️ Could not click popup element: {e}")
    except Exception:
        # It's okay if no popup appeared
        pass


def ask_chatgpt_via_selenium(prompt: str) -> str:
    """
    Opens ChatGPT web with Selenium, closes popups, sends prompt, waits for response, and returns text.
    """
    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=chrome_options)

    try:
        driver.get(CHATGPT_URL)
        wait = WebDriverWait(driver, 120)

        # Check redirect
        if "chatgpt" not in driver.current_url:
            print(f"🚨 Unexpected redirect detected: {driver.current_url}", flush=True)
            return "Error: Redirected from ChatGPT page. Please log in manually."

        print("🌐 ChatGPT page loaded. Closing popups if any...", flush=True)
        time.sleep(2)  # wait for page to stabilize
        close_auth_popup(driver)

        # Wait for prompt box
        prompt_box = wait.until(EC.element_to_be_clickable((By.ID, "prompt-textarea")))
        time.sleep(1.5)
        prompt_box.click()
        prompt_box.send_keys(prompt)

        send_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@aria-label='Send message']")
            )
        )
        print("🚀 Prompt sent, waiting for response...", flush=True)
        send_button.click()

        last_text = ""
        stable_count = 0
        start_time = time.time()
        timeout = 300  # 5 minutes max
        print("🔍 Checking for response...", flush=True)

        while stable_count < 5 and (time.time() - start_time) < timeout:
            if "verify" in driver.page_source.lower() or "cloudflare" in driver.page_source.lower():
                print("🚨 Cloudflare challenge detected. Solve it manually in the opened browser window.", flush=True)
                time.sleep(10)
                continue

            print("🔍 Checking for response...", flush=True)
            time.sleep(5)
            try:
                response_divs = driver.find_elements(
                    By.XPATH, "//div[contains(@class, 'markdown') and contains(@class, 'prose')]"
                )

                print(f"🔍 Found {len(response_divs)} response divs.", flush=True)
                if response_divs:
                    latest_div = response_divs[-1]
                    combined_response = latest_div.text.strip()

                    if combined_response and combined_response != last_text:
                        last_text = combined_response
                        stable_count = 0
                        print(f"⏳ Response updating: {len(combined_response)} chars", flush=True)
                    elif combined_response:
                        stable_count += 1
                    else:
                        stable_count = 0
                else:
                    stable_count = 0
            except Exception as e:
                print(f"⚠️ Error reading response: {e}", flush=True)
                stable_count = 0

            time.sleep(1)

        if last_text:
            print("✅ Response received!", flush=True)
            print("🔎 Final response:\n", flush=True)
            print(last_text, flush=True)
            return last_text
        else:
            print("❌ No response received.", flush=True)
            return "No response received."

    except WebDriverException as e:
        print(f"❌ WebDriver error during ChatGPT interaction: {e}", flush=True)
        return f"WebDriver error: {e}"
    except Exception as e:
        print(f"❌ General error during ChatGPT interaction: {e}", flush=True)
        return f"Error: {e}"

    finally:
        driver.quit()
import re
from typing import List, Dict

def extract_trades(text: str) -> List[Dict[str, str]]:
    """
    Extracts trade details from the input text and returns them as a list of dictionaries.
    Each dictionary follows the specified format.
    """
    # 1. Split text into trades based on Trade #1, Trade #2 markers:
    trade_blocks = re.split(r"(?:📈|📉)\s*Trade\s*#\d+:", text)[1:]  # first split is empty before Trade #1
    
    extracted_trades = []

    for raw_block in trade_blocks:
        # Extract individual fields separately — robust even if text order changes:
        trade_data = {}

        # Option Type
        match = re.search(r"Option\s*Type:\s*(.+)", raw_block)
        trade_data["Option Type"] = match.group(1).strip() if match else ""

        # Strike
        match = re.search(r"Strike:\s*(.+)", raw_block)
        trade_data["Strike Price"] = match.group(1).strip() if match else ""

        # Entry Premium
        match = re.search(r"Entry\s*Premium:\s*(.+)", raw_block)
        trade_data["Premium Entry Range"] = match.group(1).strip() if match else ""

        # Target
        match = re.search(r"Target:\s*(.+)", raw_block)
        trade_data["Target(s)"] = match.group(1).strip() if match else ""

        # Stop Loss
        match = re.search(r"Stop\s*Loss:\s*(.+)", raw_block)
        trade_data["Stop Loss"] = match.group(1).strip() if match else ""

        # Ideal Entry Time
        match = re.search(r"Ideal\s*Entry\s*Time:\s*(.+)", raw_block)
        trade_data["Ideal Entry Time"] = match.group(1).strip() if match else ""

        # Ideal Exit Time
        match = re.search(r"Ideal\s*Exit\s*Time:\s*(.+)", raw_block)
        trade_data["Ideal Exit Time"] = match.group(1).strip() if match else ""

        # Confidence
        match = re.search(r"Confidence:\s*(.+)", raw_block)
        trade_data["Confidence Level"] = match.group(1).strip() if match else ""

        # Justification/Reason: from 'Justification' until end of block
        match = re.search(r"Justification\s*(.+)", raw_block, re.DOTALL)
        trade_data["reason"] = match.group(1).strip().replace("\n", " ") if match else ""

        # Optional fields: leave blank for now
        trade_data["Volume Surge"] = ""
        trade_data["VIX"] = ""
        trade_data["Price Action"] = ""
        trade_data["Momentum"] = ""

        extracted_trades.append(trade_data)

    return extracted_trades


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
    # if is_market_closed_today():
    #     return
    raw_response = ask_chatgpt_via_selenium(PROMPT)
    trades = extract_trades(raw_response)
    best_trade = select_highest_confidence(trades)
    
    if best_trade:
        formatted = "\n".join([f"{k}: {v}" for k, v in best_trade.items()])
        send_to_telegram("🔔 *NIFTY Trade Alert (Highest Confidence)*\n\n" + formatted)
    else:
        send_to_telegram("No valid trade found in the ChatGPT response.")

# Schedule every 15 minutes
# schedule.every(30).seconds.do(run_task)

print("Running NIFTY Options Alert Bot...")
run_task()  # Run immediately on startup

# while True:
#     run_pending()
#     time.sleep(1)
