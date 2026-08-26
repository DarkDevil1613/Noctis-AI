from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter()

# ── Request models ──────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    mode: Optional[str] = "chat"

class NoteRequest(BaseModel):
    title: str
    content: str

class IngestRequest(BaseModel):
    path: str

# ── Chat ────────────────────────────────────────────────────────
@router.post("/chat")
async def chat(req: ChatRequest):
    from api.server import noctis
    if noctis is None:
        raise HTTPException(status_code=503, detail="Noctis core not initialized")
    try:
        response = await asyncio.to_thread(noctis.chat, req.message, False)
        return {"response": response, "mode": req.mode}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── System stats ────────────────────────────────────────────────
@router.get("/system")
async def system_stats():
    try:
        from tools.system_control import SystemControl
        sc = SystemControl()
        stats = sc.get_system_stats()
        return {"stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Memory ──────────────────────────────────────────────────────
@router.get("/memory/facts")
async def get_facts():
    try:
        from memory.db import get_all_facts
        facts = get_all_facts()
        return {"facts": facts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory/preferences")
async def get_preferences():
    try:
        from memory.db import get_all_preferences
        prefs = get_all_preferences()
        return {"preferences": prefs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Notes ───────────────────────────────────────────────────────
@router.post("/notes")
async def save_note(req: NoteRequest):
    try:
        notes_dir = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "memory", "notes")
        os.makedirs(notes_dir, exist_ok=True)
        filename = req.title.replace(" ", "_").lower() + ".md"
        filepath = os.path.join(notes_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {req.title}\n\n{req.content}")
        return {"status": "saved", "file": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notes")
async def list_notes():
    try:
        notes_dir = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "memory", "notes")
        os.makedirs(notes_dir, exist_ok=True)
        files = [f for f in os.listdir(notes_dir) if f.endswith(".md")]
        return {"notes": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notes/{filename}")
async def read_note(filename: str):
    try:
        notes_dir = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "memory", "notes")
        filepath = os.path.join(notes_dir, filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Note not found")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return {"filename": filename, "content": content}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Knowledge Base ──────────────────────────────────────────────
@router.post("/kb/ingest")
async def ingest_file(req: IngestRequest):
    try:
        from tools.file_reader import read_file
        from memory.vector_store import NoctisVectorStore
        if not os.path.exists(req.path):
            raise HTTPException(status_code=404, detail="File not found")
        content = read_file(req.path)
        vs = NoctisVectorStore()
        filename = os.path.basename(req.path)
        chunks = [content[i:i+500] for i in range(0, len(content), 500)]
        for i, chunk in enumerate(chunks):
            if chunk.strip():
                vs.add(chunk.strip(), metadata={
                    "source": "kb",
                    "file": filename,
                    "chunk": i
                })
        return {"status": "ingested", "file": filename, "chunks": len(chunks)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/kb/search")
async def search_kb(query: str):
    try:
        from memory.vector_store import NoctisVectorStore
        vs = NoctisVectorStore()
        results = vs.search(query, top_k=3)
        return {"query": query, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── PDF / File Summarizer ───────────────────────────────────────
class SummarizeRequest(BaseModel):
    path: str
    style: Optional[str] = "default"

@router.post("/summarize")
async def summarize_file(req: SummarizeRequest):
    from api.server import noctis
    if noctis is None:
        raise HTTPException(status_code=503, detail="Noctis core not initialized")
    try:
        from tools.file_reader import read_file
        if not os.path.exists(req.path):
            raise HTTPException(status_code=404, detail="File not found")
        content = read_file(req.path)
        if not content or not content.strip():
            raise HTTPException(status_code=400, detail="File is empty or unreadable")
        filename = os.path.basename(req.path)

        max_chars = 3000
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n[Content truncated for summarization]"

        if req.style == "bullet":
            prompt = (
                f"Summarize this document in bullet points. "
                f"Be concise and precise. No filler.\n\nDocument: {filename}\n\n{content}"
            )
        elif req.style == "technical":
            prompt = (
                f"Give a technical summary of this document. "
                f"Focus on key concepts, methods, and findings.\n\nDocument: {filename}\n\n{content}"
            )
        else:
            prompt = (
                f"Summarize this document in 3-5 sentences. "
                f"Be direct and precise.\n\nDocument: {filename}\n\n{content}"
            )

        summary = await asyncio.to_thread(noctis.chat, prompt, False)
        return {
            "file": filename,
            "style": req.style,
            "summary": summary,
            "chars_processed": len(content)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Study Companion ─────────────────────────────────────────────
class StudyRequest(BaseModel):
    topic: Optional[str] = None
    path: Optional[str] = None
    mode: Optional[str] = "summarize"

@router.post("/study")
async def study(req: StudyRequest):
    from api.server import noctis
    if noctis is None:
        raise HTTPException(status_code=503, detail="Noctis core not initialized")
    try:
        content = ""
        source = ""

        if req.path:
            from tools.file_reader import read_file
            if not os.path.exists(req.path):
                raise HTTPException(status_code=404, detail="File not found")
            content = read_file(req.path)
            source = os.path.basename(req.path)
            if len(content) > 3000:
                content = content[:3000] + "\n\n[Truncated]"
        elif req.topic:
            content = req.topic
            source = "topic"
        else:
            raise HTTPException(status_code=400, detail="Provide topic or path")

        if req.mode == "summarize":
            prompt = (
                f"Summarize this material clearly and concisely. "
                f"Extract the most important concepts.\n\nSource: {source}\n\n{content}"
            )
        elif req.mode == "quiz":
            prompt = (
                f"Generate 5 quiz questions with answers based on this material. "
                f"Format: Q: question / A: answer. Be precise.\n\nSource: {source}\n\n{content}"
            )
        elif req.mode == "explain":
            prompt = (
                f"Explain this material in depth. Break down complex concepts. "
                f"Use examples where helpful.\n\nSource: {source}\n\n{content}"
            )
        elif req.mode == "flashcard":
            prompt = (
                f"Generate 5 flashcards from this material. "
                f"Format: TERM: definition. One per line. Be concise.\n\nSource: {source}\n\n{content}"
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid mode. Use: summarize | quiz | explain | flashcard")

        response = await asyncio.to_thread(noctis.chat, prompt, False)
        return {
            "source": source,
            "mode": req.mode,
            "response": response
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Cybersecurity Assistant ─────────────────────────────────────
class CybersecRequest(BaseModel):
    query: str

@router.post("/cybersec")
async def cybersec(req: CybersecRequest):
    from api.server import noctis
    if noctis is None:
        raise HTTPException(status_code=503, detail="Noctis core not initialized")
    try:
        from memory.vector_store import NoctisVectorStore
        vs = NoctisVectorStore()

        results = vs.search(req.query, top_k=3)
        kb_context = ""
        if results:
            kb_hits = [r for r in results if r.get("metadata", {}).get("source") == "kb"]
            if kb_hits:
                kb_context = "\n".join([r["text"] for r in kb_hits])

        if kb_context:
            prompt = (
                f"Answer this cybersecurity question using the knowledge below. "
                f"Be technical, precise, no hand-holding.\n\n"
                f"Knowledge:\n{kb_context}\n\n"
                f"Question: {req.query}"
            )
        else:
            prompt = (
                f"Answer this cybersecurity question from your knowledge. "
                f"Be technical, precise, no hand-holding.\n\n"
                f"Question: {req.query}"
            )

        response = await asyncio.to_thread(noctis.chat, prompt, False)
        source_used = "kb" if kb_context else "model"
        return {
            "query": req.query,
            "source": source_used,
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cybersec/ingest")
async def cybersec_ingest(req: IngestRequest):
    try:
        from tools.file_reader import read_file
        from memory.vector_store import NoctisVectorStore
        if not os.path.exists(req.path):
            raise HTTPException(status_code=404, detail="File not found")
        content = read_file(req.path)
        vs = NoctisVectorStore()
        filename = os.path.basename(req.path)
        chunks = [content[i:i+500] for i in range(0, len(content), 500)]
        for i, chunk in enumerate(chunks):
            if chunk.strip():
                vs.add(chunk.strip(), metadata={
                    "source": "kb",
                    "category": "cybersec",
                    "file": filename,
                    "chunk": i
                })
        return {"status": "ingested", "file": filename, "chunks": len(chunks)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))