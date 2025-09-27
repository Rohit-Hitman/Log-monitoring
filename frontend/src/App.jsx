import { useState, useEffect, useRef } from "react";

function UploadForm({ onUploaded }) {
  const [file, setFile] = useState(null);

  const handleChange = (e) => setFile(e.target.files[0]);

  const handleUpload = async () => {
    if (!file) return alert("Select a file first!");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const resp = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });
      const data = await resp.json();
      alert(`Uploaded ${data.rows} rows`);
      onUploaded?.();
    } catch (err) {
      console.error(err);
      alert("Upload failed");
    }
  };

  return (
    <div className="mb-4">
      <input type="file" accept=".xlsx" onChange={handleChange} />
      <button
        onClick={handleUpload}
        className="ml-2 px-3 py-1 bg-blue-500 text-white rounded"
      >
        Upload Excel
      </button>
    </div>
  );
}

export default function App() {
  const [metrics, setMetrics] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/stats");
    ws.onopen = () => console.log("WebSocket connected");
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.type === "metrics") setMetrics(msg.data);
      } catch (err) {
        console.error(err);
      }
    };
    ws.onclose = () => console.log("WebSocket closed");
    wsRef.current = ws;
    return () => ws.close();
  }, []);

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Real-time Error Monitor</h1>
      <UploadForm />
      {!metrics && <p>Waiting for metrics...</p>}
      {metrics && (
        <>
          <p>
            Window: {metrics.window_seconds}s — updated at{" "}
            {new Date(metrics.timestamp * 1000).toLocaleTimeString()}
          </p>

          <h2 className="mt-4 text-xl font-semibold">Counts by category</h2>
          <ul className="list-disc ml-6">
            {Object.entries(metrics.counts).map(([cat, cnt]) => (
              <li key={cat}>
                {cat}: {cnt}
              </li>
            ))}
          </ul>

          <h2 className="mt-4 text-xl font-semibold">Per service</h2>
          {Object.entries(metrics.per_service).map(([svc, cats]) => (
            <div key={svc} className="ml-2 mt-2">
              <strong>{svc}</strong>
              <ul className="list-disc ml-6">
                {Object.entries(cats).map(([c, n]) => (
                  <li key={c}>
                    {c}: {n}
                  </li>
                ))}
              </ul>
            </div>
          ))}

          <h2 className="mt-4 text-xl font-semibold">Recent errors</h2>
          <ol className="list-decimal ml-6">
            {metrics.recent_errors.slice(0, 10).map((e, idx) => (
              <li key={idx}>
                <strong>{e.service}</strong> [{e.category}] — {e.message}
              </li>
            ))}
          </ol>
        </>
      )}
    </div>
  );
}
