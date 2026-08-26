"""
WebSocket bridge fallback (now acts as an HTTP IPC client to FastAPI).
Routes voice/LLM events to the FastAPI server running on port 8000.
"""
import threading
import json
import requests

def _post_event(event: str, data: str):
    try:
        requests.post(
            "http://127.0.0.1:8000/api/ui-event",
            json={"event": event, "data": data},
            timeout=0.5
        )
    except Exception:
        pass

def broadcast(event: str, data: str):
    """Thread-safe broadcast callable from noctis_voice.py's sync code."""
    threading.Thread(target=_post_event, args=(event, data), daemon=True).start()
