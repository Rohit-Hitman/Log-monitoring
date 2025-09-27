from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
import pandas as pd

@app.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    # Read Excel into DataFrame
    df = pd.read_excel(file.file)
    # Expected columns: timestamp, service, level, message, error_code
    now = time.time()
    # Clear previous data
    counters.clear()
    service_counters.clear()
    recent_errors.clear()

    for _, row in df.iterrows():
        try:
            ts = pd.to_datetime(row.get('timestamp', now)).timestamp()
            service = str(row.get('service', 'unknown'))
            level = str(row.get('level', 'ERROR'))
            message = str(row.get('message', ''))
            error_code = str(row.get('error_code', ''))
            category = classify_log(message, error_code)
            counters[category].append(ts)
            service_key = f"{service}||{category}"
            service_counters[service_key].append(ts)
            recent_errors.appendleft({
                "timestamp": ts,
                "service": service,
                "level": level,
                "category": category,
                "message": message[:500]
            })
        except Exception as e:
            print(f"Row skipped: {e}")


    return {"status": "uploaded", "rows": len(df)}
