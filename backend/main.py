# from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
# import pandas as pd
# from fastapi import UploadFile, File
# from fastapi.middleware.cors import CORSMiddleware

# app = FastAPI()

# origins = [
#     "http://localhost:5173",
#     "http://127.0.0.1:5173",
# ]
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )



# @app.post("/upload")
# async def upload_excel(file: UploadFile = File(...)):
#     # Read Excel into DataFrame (pandas + openpyxl)
#     df = pd.read_excel(file.file)
#     # Clear previous in-memory data
#     counters.clear()
#     service_counters.clear()
#     recent_errors.clear()

#     for _, row in df.iterrows():
#         # parse each row (safe access & fallbacks)
#         ts = pd.to_datetime(row.get('timestamp', pd.Timestamp.now())).timestamp()
#         service = str(row.get('service', 'unknown'))
#         level = str(row.get('level', 'ERROR'))
#         message = str(row.get('message', ''))
#         error_code = str(row.get('error_code', ''))
#         category = classify_log(message, error_code)
#         counters[category].append(ts)
#         service_counters[f"{service}||{category}"].append(ts)
#         recent_errors.appendleft({
#             "timestamp": ts,
#             "service": service,
#             "level": level,
#             "category": category,
#             "message": message[:500]
#         })
#     return {"status": "uploaded", "rows": len(df)}




from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict, deque
import pandas as pd
import asyncio
import time

# ----------------------
# Global in-memory data
# ----------------------
counters = defaultdict(list)          # category -> list of timestamps
service_counters = defaultdict(list)  # service||category -> list of timestamps
recent_errors = deque(maxlen=100)     # store last 100 logs

# ----------------------
# FastAPI app
# ----------------------
app = FastAPI(title="Log Error Monitoring API")

# CORS for frontend
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------
# Helper function
# ----------------------
def classify_log(message, error_code):
    message_lower = message.lower()
    if "timeout" in message_lower:
        return "Timeout"
    elif "fail" in message_lower:
        return "Failure"
    elif "error" in message_lower or "exception" in message_lower:
        return "Error"
    else:
        return "Other"

# ----------------------
# Upload Excel endpoint
# ----------------------
@app.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    df = pd.read_excel(file.file)

    # Clear previous data
    counters.clear()
    service_counters.clear()
    recent_errors.clear()

    for _, row in df.iterrows():
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

# ----------------------
# WebSocket endpoint
# ----------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/stats")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Prepare metrics snapshot
            data = {
                "counts": {k: len(v) for k,v in counters.items()},
                "per_service": {},
                "recent_errors": list(recent_errors),
                "timestamp": time.time(),
                "window_seconds": 60
            }

            # Per-service metrics
            per_svc = defaultdict(dict)
            for key, val in service_counters.items():
                svc, cat = key.split("||")
                per_svc[svc][cat] = len(val)
            data["per_service"] = per_svc

            await websocket.send_json({"type":"metrics","data":data})
            await asyncio.sleep(2)  # update every 2 seconds
    except WebSocketDisconnect:
        manager.disconnect(websocket)
