from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import uvicorn
import sys
import os
import json
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.noctis_core import NoctisCore

noctis = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global noctis
    print("[Noctis] Initializing core...")
    noctis = NoctisCore()
    print("[Noctis] Core online.")
    yield
    print("[Noctis] Shutting down.")

app = FastAPI(
    title="Noctis API",
    description="DevilCore — N-0CT15 Backend",
    version="7.0.0",
    lifespan=lifespan
)

from api.routes import router
app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "operational"}

# ── Serve UI ──────────────────────────────────────────────────────
ui_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui")
app.mount("/ui", StaticFiles(directory=ui_dir, html=True), name="ui")

@app.get("/")
async def root():
    return FileResponse(
        os.path.join(ui_dir, "index.html"),
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )

@app.get("/favicon.ico")
async def favicon():
    logo_path = os.path.join(ui_dir, "noctis_logo.jpg")
    if os.path.exists(logo_path):
        return FileResponse(logo_path)
    return {"status": "none"}

# ── WebSocket for live UI events ─────────────────────────────────
_ws_clients = set()

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    _ws_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        _ws_clients.discard(websocket)
    except Exception:
        _ws_clients.discard(websocket)

async def broadcast_to_ui(event: str, data: str):
    """Called from ws_bridge to push events to all connected UI clients."""
    if not _ws_clients:
        return
    message = json.dumps({"event": event, "data": data})
    dead = set()
    for ws in _ws_clients:
        try:
            await ws.send_text(message)
        except Exception:
            dead.add(ws)
    _ws_clients.difference_update(dead)

# ── Internal IPC for noctis_voice.py ─────────────────────────────
@app.post("/api/ui-event")
async def ui_event_endpoint(request: Request):
    data = await request.json()
    await broadcast_to_ui(data.get("event", ""), data.get("data", ""))
    return {"status": "ok"}

@app.get("/api/system-stats")
async def get_system_stats():
    """Returns quick CPU, RAM, Battery telemetry for JARVIS HUD."""
    try:
        import psutil
        cpu = f"{psutil.cpu_percent(interval=None)}%"
        ram = f"{psutil.virtual_memory().percent}%"
        bat_sensor = psutil.sensors_battery()
        bat = f"{round(bat_sensor.percent)}%" if bat_sensor else "AC"
        return {"cpu": cpu, "ram": ram, "battery": bat}
    except Exception as e:
        return {"cpu": "N/A", "ram": "N/A", "battery": "N/A"}

@app.post("/api/shutdown")
async def shutdown_endpoint():
    # Kill the current process
    asyncio.create_task(shutdown_task())
    return {"status": "shutting down"}

async def shutdown_task():
    await asyncio.sleep(1)
    os._exit(0)

if __name__ == "__main__":
    uvicorn.run("api.server:app", host="127.0.0.1", port=8000, reload=False)