start frontend:

uvicorn main:app --reload --host 0.0.0.0 --port 8000

start frontend:
    cd ../frontend
    npm install
    npm run dev -- --host

Endpoints:

    POST /upload — upload Excel file (multipart form field name file)

    GET /stats — snapshot JSON of current metrics

    POST /ingest — (existing single-log ingestion API, still present)

    ws://localhost:8000/ws/stats — websocket for real-time updates

