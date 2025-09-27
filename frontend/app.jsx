
function UploadForm() {
    const [file, setFile] = useState(null);
    const handleChange = (e) => setFile(e.target.files[0]);
    const handleUpload = async () => {
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);
        await fetch('http://localhost:8000/upload', { method: 'POST', body: formData });
};
return (
    <div style={{marginBottom:20}}>
        <input type="file" accept=".xlsx" onChange={handleChange} />
        <button onClick={handleUpload}>Upload Excel</button>
    </div>
    );
}

