from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
import pandas as pd
from fastapi import UploadFile, File
from fastapi.middleware.cors import CORSMiddleware



origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    # Read Excel into DataFrame (pandas + openpyxl)
    df = pd.read_excel(file.file)
    # Clear previous in-memory data
    counters.clear()
    service_counters.clear()
    recent_errors.clear()

    for _, row in df.iterrows():
        # parse each row (safe access & fallbacks)
        ts = pd.to_datetime(row.get('timestamp', pd.Timestamp.now())).timestamp()
        service = str(row.get('service', 'unknown'))
        level = str(row.get('level', 'ERROR'))
        message = str(row.get('message', ''))
        error_code = str(row.get('error_code', ''))
        category = classify_log(message, error_code)
        counters[category].append(ts)
        service_counters[f"{service}||{category}"].append(ts)
        recent_errors.appendleft({
            "timestamp": ts,
            "service": service,
            "level": level,
            "category": category,
            "message": message[:500]
        })
    return {"status": "uploaded", "rows": len(df)}
