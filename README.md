# Secure RAG for Cloud Assistants

Prototipo sperimentale per lo studio della sicurezza in sistemi RAG applicati
a contesti cloud. Sviluppato nell'ambito di una tesi di laurea.

## Stack

- Python 3.11
- LlamaIndex (framework RAG)
- ChromaDB (vector store)
- Ollama + Llama 3.1 8B (LLM locale)
- HuggingFace BGE-small (embeddings)
- FastAPI (API HTTP)

## Status

In sviluppo — Fase 1 (pipeline baseline).

## Setup rapido

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ollama pull llama3.1:8b
python -m src.ingest
```