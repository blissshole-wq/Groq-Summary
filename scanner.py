import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta 
import requests
import os

def send_telegram_alert(message):
    bot_token = os.environ.get("BOT_TOKEN") 
    chat_id = os.environ.get("CHAT_ID")
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}&parse_mode=Markdown"
    try:
        requests.get(url)
    except Exception as e:
        print("Telegram Error:", e)

def check_technical_setup(symbol):
    ticker = yf.Ticker(f"{symbol}.NS")
    df = ticker.history(period="3mo", interval="1d")
    
    if df.empty:
        return False, "Data not found"

    df['SMA_20'] = ta.sma(df['Close'], length=20)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    latest_close = df['Close'].iloc[-1]
    sma_20 = df['SMA_20'].iloc[-1]
    rsi = df['RSI'].iloc[-1]

    if latest_close > sma_20 and rsi < 60:
        return True, f"Price: ₹{latest_close:.2f} | RSI: {rsi:.2f}"
    else:
        return False, f"Failed Tech Check (RSI: {rsi:.2f})"

def run_confluence_scanner():
    print("Starting Confluence Scanner...")
    
    # இங்கே உங்களுக்கு தேவையான ஸ்டாக்ஸ் லிஸ்ட்டை மாத்திக்கோங்க
    fundamental_stocks = ["HAL", "TATAPOWER", "NMDC", "RELIANCE", "TCS"] 
    
    best_buy_picks = []
    
    for stock in fundamental_stocks:
        print(f"Checking {stock}...")
        is_tech_good, details = check_technical_setup(stock)
        
        if is_tech_good:
            best_buy_picks.append(f"✅ *{stock}*\nNews: Good | Chart: {details}")
            
    if best_buy_picks:
        alert_message = "🔥 *CONFLUENCE BUY ALERTS!* (News + Tech)\n\n" + "\n\n".join(best_buy_picks)
        send_telegram_alert(alert_message)
        print("Alerts sent to Telegram!")
    else:
        print("No Confluence setups found today.")

if __name__ == "__main__":
    run_confluence_scanner()
