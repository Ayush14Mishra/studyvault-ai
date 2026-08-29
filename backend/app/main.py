import os
import re
import uuid
from collections import Counter
from pathlib import Path

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pypdf import PdfReader

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
MAX_FILE_SIZE = 8 * 1024 * 1024
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

app = FastAPI(title="StudyVault AI API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Source(BaseModel):
    document_id: str
    title: str
    page: int
    excerpt: str
    score: float


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    document_ids: list[str] | None = None


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    mode: str


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]{2,}", text.lower())


def chunk_text(text: str, page: int, chunk_size: int = 900, overlap: int = 140) -> list[dict]:
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []
    chunks = []
    start = 0
    while start < len(clean):
        end = min(start + chunk_size, len(clean))
        if end < len(clean):
            boundary = clean.rfind(". ", start, end)
            if boundary > start + chunk_size // 2:
                end = boundary + 1
        chunks.append({"page": page, "text": clean[start:end]})
        if end == len(clean):
            break
        start = max(end - overlap, start + 1)
    return chunks


def score(query: str, text: str) -> float:
    q = Counter(tokenize(query))
    d = Counter(tokenize(text))
    if not q or not d:
        return 0.0
    return sum(min(q[token], d[token]) for token in q) / sum(q.values())


def document_path(document_id: str) -> Path:
    return DATA_DIR / f"{document_id}.json"


def read_documents() -> list[dict]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    documents = []
    for path in DATA_DIR.glob("*.json"):
        import json
        documents.append(json.loads(path.read_text()))
    return documents


def retrieve(question: str, allowed_ids: list[str] | None = None, limit: int = 4) -> list[dict]:
    candidates = []
    for document in read_documents():
        if allowed_ids and document["id"] not in allowed_ids:
            continue
        for chunk in document["chunks"]:
            item_score = score(question, chunk["text"])
            if item_score:
                candidates.append({**chunk, "document_id": document["id"], "title": document["title"], "score": item_score})
    return sorted(candidates, key=lambda item: item["score"], reverse=True)[:limit]


async def ollama_answer(question: str, matches: list[dict]) -> str:
    context = "\n\n".join(f"[Source {index + 1}] {item['text']}" for index, item in enumerate(matches))
    prompt = (
        "Answer only from the supplied study material. Be concise, explain clearly, and say when the material does not contain the answer. "
        "Cite source numbers in square brackets.\n\n"
        f"Study material:\n{context}\n\nQuestion: {question}"
    )
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        )
        response.raise_for_status()
        return response.json()["response"].strip()


def fallback_answer(question: str, matches: list[dict]) -> str:
    if not matches:
        return "I could not find that in the documents you uploaded. Try a more specific question or upload relevant notes."
    sentences = re.split(r"(?<=[.!?])\s+", matches[0]["text"])
    relevant = [sentence for sentence in sentences if set(tokenize(question)) & set(tokenize(sentence))]
    chosen = " ".join(relevant[:3]) or sentences[0]
    return f"Based on your notes: {chosen} [1]"


@app.get("/health")
def health():
    return {"status": "ok", "demo_mode": DEMO_MODE, "documents": len(read_documents())}


@app.get("/documents")
def list_documents():
    return [{"id": doc["id"], "title": doc["title"], "pages": doc["pages"], "chunks": len(doc["chunks"])} for doc in read_documents()]


@app.post("/documents", status_code=201)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(400, "Please upload a PDF or TXT file.")
    raw = await file.read()
    if len(raw) > MAX_FILE_SIZE:
        raise HTTPException(400, "File must be 8 MB or smaller.")
    if file.filename.lower().endswith(".pdf"):
        from io import BytesIO
        reader = PdfReader(BytesIO(raw))
        pages = [page.extract_text() or "" for page in reader.pages]
    else:
        pages = [raw.decode("utf-8", errors="ignore")]
    chunks = [chunk for page_no, text in enumerate(pages, start=1) for chunk in chunk_text(text, page_no)]
    if not chunks:
        raise HTTPException(400, "No readable text was found in this file.")
    document = {"id": str(uuid.uuid4()), "title": file.filename, "pages": len(pages), "chunks": chunks}
    import json
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    document_path(document["id"]).write_text(json.dumps(document))
    return {"id": document["id"], "title": document["title"], "pages": document["pages"], "chunks": len(chunks)}


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    matches = retrieve(request.question, request.document_ids)
    sources = [Source(document_id=item["document_id"], title=item["title"], page=item["page"], excerpt=item["text"][:220], score=round(item["score"], 2)) for item in matches]
    if DEMO_MODE:
        return AskResponse(answer=fallback_answer(request.question, matches), sources=sources, mode="demo retrieval")
    try:
        answer = await ollama_answer(request.question, matches)
        return AskResponse(answer=answer, sources=sources, mode=f"Ollama · {OLLAMA_MODEL}")
    except (httpx.HTTPError, KeyError):
        return AskResponse(answer=fallback_answer(request.question, matches), sources=sources, mode="fallback retrieval (Ollama unavailable)")
