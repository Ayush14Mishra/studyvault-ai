import { useCallback, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

function App() {
  const [documents, setDocuments] = useState([]);
  const [file, setFile] = useState();
  const [question, setQuestion] = useState("Explain overfitting in simple words.");
  const [result, setResult] = useState();
  const [status, setStatus] = useState("");
  const refresh = useCallback(() => fetch(`${API}/documents`).then((r) => r.json()).then(setDocuments), []);
  useEffect(() => { refresh().catch(() => setStatus("The API is not running yet.")); }, [refresh]);

  async function upload(event) {
    event.preventDefault();
    if (!file) return;
    setStatus("Reading and indexing your document…");
    const data = new FormData(); data.append("file", file);
    const response = await fetch(`${API}/documents`, { method: "POST", body: data });
    const body = await response.json();
    setStatus(response.ok ? `Added ${body.title}` : body.detail);
    if (response.ok) refresh();
  }
  async function ask(event) {
    event.preventDefault(); setStatus("Finding relevant notes…"); setResult();
    const response = await fetch(`${API}/ask`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question }) });
    const body = await response.json(); setResult(body); setStatus("");
  }
  return <main><header><span className="mark">SV</span><div><h1>StudyVault AI</h1><p>Ask questions about your notes. Every answer shows its source.</p></div><span className="badge">Free local AI</span></header>
    <section className="grid"><aside><h2>Your library</h2><form onSubmit={upload}><label className="drop"><input type="file" accept=".pdf,.txt" onChange={(e) => setFile(e.target.files[0])}/><b>{file ? file.name : "Choose PDF or TXT"}</b><small>Up to 8 MB</small></label><button>Upload & index</button></form><div className="docs">{documents.length ? documents.map((doc) => <article key={doc.id}><b>{doc.title}</b><small>{doc.pages} page(s) · {doc.chunks} chunks</small></article>) : <p>No documents yet. Upload your notes to begin.</p>}</div></aside>
      <section className="chat"><div className="eyebrow">RETRIEVAL-AUGMENTED GENERATION</div><h2>Learn from your material, not made-up answers.</h2><form onSubmit={ask}><textarea value={question} onChange={(e) => setQuestion(e.target.value)} /><button>Ask StudyVault AI <span>→</span></button></form>{status && <p className="status">{status}</p>}{result && <div className="answer"><div className="answer-head"><b>Answer</b><span>{result.mode}</span></div><p>{result.answer}</p><h3>Sources used</h3>{result.sources.length ? result.sources.map((source, index) => <div className="source" key={`${source.document_id}-${source.page}`}><b>[{index + 1}] {source.title} · page {source.page}</b><p>{source.excerpt}…</p></div>) : <p>No matching source found.</p>}</div>}</section></section>
  </main>;
}
createRoot(document.getElementById("root")).render(<App />);
