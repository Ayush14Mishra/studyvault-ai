# StudyVault AI

**A free, local-first RAG study assistant that answers questions from uploaded notes and shows the source page for every answer.**

![Stack](https://img.shields.io/badge/React-FastAPI-Ollama-17201c?style=flat-square)

## Why it exists

Students have notes but spend too much time searching them. StudyVault AI makes those notes searchable by question while preserving a crucial trust feature: each answer displays the document and page used.

## Features

- Upload PDF or TXT notes (up to 8 MB)
- Page-aware chunking and local retrieval
- Source excerpts and page citations with every answer
- **Free demo mode**: works without an API key or model download
- **Local AI mode**: uses Ollama on your machine; documents never need to leave it
- Docker-based startup for a consistent reviewer experience

## Architecture

```text
React interface → FastAPI → retrieve relevant note chunks → Ollama (optional) → cited answer
                              ↘ local JSON store / page metadata ↗
```

## Run it in two minutes

```bash
git clone https://github.com/YOUR_USERNAME/studyvault-ai.git
cd studyvault-ai
docker compose up --build
```

Open `http://localhost:5173`. It starts in demo retrieval mode, so no key, account, or paid API is required.

## Recruiter demo script

1. Upload a short PDF or TXT file containing class notes.
2. Ask a question whose answer is present in the file.
3. Open the listed source: it shows the exact document, page, and excerpt used to ground the answer.
4. Explain that this is intentionally local-first: note content stays on the user's machine in Ollama mode.

### Turn on local AI

1. Install [Ollama](https://ollama.com) and run `ollama pull llama3.2:3b`.
2. Copy `.env.example` to `.env` and change `DEMO_MODE=false`.
3. Run `docker compose up --build` again.

## Development

```bash
# API
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && uvicorn app.main:app --reload

# web (in another terminal)
cd frontend && npm install && npm run dev
```

Run backend tests with `cd backend && pytest`.

## Interview talking points

- A basic lexical retrieval implementation keeps the MVP transparent and free; its `retrieve()` boundary can be replaced with Chroma/pgvector embeddings as data grows.
- Pages remain attached to chunks so citations are meaningful rather than decorative.
- Demo mode makes the public interface reviewable without exposing a key or requiring the reviewer to run an LLM.
- The app falls back safely to retrieved text when Ollama is unavailable instead of inventing an answer.

## Roadmap

- Replace lexical ranking with local embeddings + Chroma
- Add user accounts and document ownership
- Generate flashcards and quizzes from selected documents
- Add evaluations for answer relevance and citation accuracy
