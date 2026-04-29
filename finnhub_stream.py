import websocket
import json
import logging

API_KEY = "d7p31ihr01qr68pbh6fgd7p31ihr01qr68pbh6g0" 

TICKERS = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "NFLX", "INTC", "AMD"]
OUTPUT_FILE = "console.finnhub.txt"

def on_message(ws, message):
    # כתיבת הודעות ה-JSON נטו לקובץ
    with open(OUTPUT_FILE, "a") as f:
        f.write(message + "\n")
    print("Received JSON message, saved to file.")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("### Connection Closed ###")

def on_open(ws):
    print("Connection Opened. Subscribing to tickers...")
    
    with open(OUTPUT_FILE, "a") as f:
        f.write("Websocket connected\n")
        
    for ticker in TICKERS:
        subscribe_msg = {"type": "subscribe", "symbol": ticker}
        ws.send(json.dumps(subscribe_msg))

if __name__ == "__main__":
    logger = logging.getLogger('websocket')
    logger.setLevel(logging.DEBUG)
    
    # שימוש ב-mode='w' כדי למחוק את הנתונים הישנים ולהתחיל קובץ חדש ונקי בכל הרצה
    fh = logging.FileHandler(OUTPUT_FILE, mode='w') 
    fh.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(fh)
    
    # הדלקת ה-Trace והפנייתו לקובץ שלנו
    websocket.enableTrace(True, handler=fh)
    
    ws = websocket.WebSocketApp(f"wss://ws.finnhub.io?token={API_KEY}",
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()
