import json
import math
import datetime

H10 = 10.0
H50 = 50.0

tickers_state = {}
OUTPUT_FILE = "console.process_stream.txt"

def process_trade(trade, raw_line, log_file):
    symbol = trade.get('s')
    price = trade.get('p')
    timestamp_ms = trade.get('t')
    
    if symbol is None or price is None or timestamp_ms is None:
        return

    if symbol not in tickers_state:
        tickers_state[symbol] = {
            'count': 0,
            'mean': 0.0,
            'ss': 0.0, 
            'var': 0.0,
            'min': price,
            'max': price,
            'ema10': price,
            'ema50': price,
            'last_time_ms': timestamp_ms,
            'messages_since_last_print': 0
        }
        
    state = tickers_state[symbol]
    
    dt_ms = timestamp_ms - state['last_time_ms']
    dt_minutes = max(0, dt_ms / 60000.0) 
    
    if dt_minutes > 0:
        alpha10 = 1.0 - math.exp(math.log(0.5) * (dt_minutes / H10))
        alpha50 = 1.0 - math.exp(math.log(0.5) * (dt_minutes / H50))
        
        state['ema10'] = alpha10 * price + (1.0 - alpha10) * state['ema10']
        state['ema50'] = alpha50 * price + (1.0 - alpha50) * state['ema50']
        
    # אלגוריתם Welford מצטבר (ללא שמירה בזיכרון, כפי שנדרש באילוצים)
    state['count'] += 1
    delta = price - state['mean']
    state['mean'] += (delta / state['count'])
    delta2 = price - state['mean']
    state['ss'] += (delta * delta2)
    
    if state['count'] > 1:
        state['var'] = state['ss'] / state['count'] 
        
    if price < state['min']: state['min'] = price
    if price > state['max']: state['max'] = price
        
    state['last_time_ms'] = timestamp_ms
    state['messages_since_last_print'] += 1
    
    # הדפסה בכל 100 הודעות, כולל שורת ה-JSON הגולמית והפורמט המדויק
    if state['messages_since_last_print'] >= 100:
        now_str = datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Y")
        data_time_str = datetime.datetime.fromtimestamp(timestamp_ms/1000.0).strftime("%a %b %d %H:%M:%S %Y.%f")[:-3]
        
        # הדפסת ה-JSON המקורי שמחקנו ממנו רווחים עודפים ומיד לאחריו הבלוק המסודר
        output_text = (
            f"{raw_line.strip()}\n"
            f"===================================\n"
            f"symbol = {symbol};\n"
            f"data time = {data_time_str}\n"
            f"now = {now_str}\n"
            f"EMA10 = {state['ema10']:.4f}\n"
            f"var10 = {state['var']}\n"
            f"ss10 = {state['ss']}\n"
            f"count10 = {state['count']}\n"
            f"EMA50 = {state['ema50']:.4f}\n"
            f"var50 = {state['var']}\n"
            f"ss50 = {state['ss']}\n"
            f"count50 = {state['count']}\n"
            f"min = {state['min']}\n"
            f"max = {state['max']}\n"
            f"close = {price}\n"
            f"===================================\n"
        )
        
        log_file.write(output_text)
        log_file.flush()
        print(f"[{symbol}] Window threshold reached. Formatted block written.")
        state['messages_since_last_print'] = 0

def extract_json(line):
    # פונקציית עזר לחלץ JSON מתוך שורות ה-Trace
    start_idx = line.find('{"data"')
    if start_idx != -1:
        end_idx = line.rfind('}')
        if end_idx != -1:
            return line[start_idx:end_idx+1]
    return None

def run_processor(input_filename="console.finnhub.txt", output_filename=OUTPUT_FILE):
    print(f"Starting Stream Processor... Saving results to {output_filename}")
    
    with open(input_filename, "r") as infile, open(output_filename, "w") as outfile:
        for line in infile:
            if not line.strip():
                continue
                
            json_str = extract_json(line)
            if json_str:
                try:
                    message = json.loads(json_str)
                    if message.get("type") == "trade":
                        for trade in message["data"]:
                            process_trade(trade, json_str, outfile)
                except json.JSONDecodeError:
                    pass
                
    print(f"Processing complete. Check {output_filename} for results.")

if __name__ == "__main__":
    run_processor()