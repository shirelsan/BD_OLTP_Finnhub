import json
import time
import tracemalloc
import math

H10 = 10.0
H50 = 50.0
INPUT_FILE = "console.finnhub.txt"

def run_offline_validation():
    print("Starting Offline Validation (Batch Processing)...")
    
    # הפעלת מעקב אחרי צריכת זיכרון וזמן
    tracemalloc.start()
    start_time = time.time()

    # שלב 1: טעינת כל הנתונים לזיכרון (מה שאסור לעשות בזמן אמת)
    symbol_data = {}
    
    def extract_json(line):
        start_idx = line.find('{"data"')
        if start_idx != -1:
            end_idx = line.rfind('}')
            if end_idx != -1:
                return line[start_idx:end_idx+1]
        return None

    with open(INPUT_FILE, "r") as f:
        for line in f:
            if not line.strip():
                continue
                
            json_str = extract_json(line)
            if json_str:
                try:
                    message = json.loads(json_str)
                    if message.get("type") == "trade":
                        for trade in message["data"]:
                            sym = trade['s']
                            if sym not in symbol_data:
                                symbol_data[sym] = []
                            symbol_data[sym].append(trade)
                except json.JSONDecodeError:
                    pass

    # שלב 2: חישוב אומדים בדיעבד על כל המערך
    results = {}
    for sym, trades in symbol_data.items():
        prices = [t['p'] for t in trades]
        count = len(prices)
        if count == 0:
            continue
            
        # --- חישוב שונות אוכלוסייה רגיל (לא אינקרמנטלי) ---
        mean = sum(prices) / count
        # חישוב סכום ריבועי הסטיות חלקי מספר הדגימות
        var_offline = sum((p - mean) ** 2 for p in prices) / count 
        
        # --- חישוב EMA לא-מקוון ---
        ema10 = prices[0]
        ema50 = prices[0]
        last_time_ms = trades[0]['t']
        
        for i in range(1, count):
            p = prices[i]
            t = trades[i]['t']
            dt_minutes = max(0, (t - last_time_ms) / 60000.0)
            
            if dt_minutes > 0:
                alpha10 = 1.0 - math.exp(math.log(0.5) * (dt_minutes / H10))
                alpha50 = 1.0 - math.exp(math.log(0.5) * (dt_minutes / H50))
                
                ema10 = alpha10 * p + (1.0 - alpha10) * ema10
                ema50 = alpha50 * p + (1.0 - alpha50) * ema50
                
            last_time_ms = t
            
        results[sym] = {
            'count': count,
            'ema10': ema10,
            'ema50': ema50,
            'var': var_offline
        }

    # סיום המעקב
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    total_time_seconds = end_time - start_time
    peak_memory_mb = peak / (1024 * 1024)

    # הדפסת התוצאות לניתוח
    print(f"\n=== Offline Validation Results ===")
    print(f"Total Runtime: {total_time_seconds:.4f} seconds")
    print(f"Peak Memory Usage: {peak_memory_mb:.4f} MB")
    print("-----------------------------------")
    for sym, stats in results.items():
        print(f"[{sym}] Updates: {stats['count']} | EMA10: {stats['ema10']:.4f} | EMA50: {stats['ema50']:.4f} | Var: {stats['var']:.8f}")

if __name__ == "__main__":
    run_offline_validation()