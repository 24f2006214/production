import json
import time
import uuid
from collections import deque

from fastapi import FastAPI, Query, Request
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest


EMAIL = "24f2006214@ds.study.iitm.ac.in"
STARTED = time.monotonic()
REQUESTS = Counter("http_requests", "Total HTTP requests")
LOGS = deque(maxlen=1000)

app = FastAPI()


@app.middleware("http")
async def observe(request: Request, call_next):
    request_id = str(uuid.uuid4())
    REQUESTS.inc()
    started = time.perf_counter()
    response = await call_next(request)
    entry = {
        "level": "INFO",
        "ts": time.time(),
        "path": request.url.path,
        "request_id": request_id,
    }
    LOGS.append(entry)
    print(json.dumps(entry), flush=True)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{time.perf_counter() - started:.6f}"
    return response


@app.get("/work")
async def work(n: int = Query(..., ge=0)):
    # Perform deterministic CPU work while keeping the requested count.
    for _ in range(n):
        pass
    return {"email": EMAIL, "done": n}


@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "uptime_s": max(0.0, time.monotonic() - STARTED)}


@app.get("/logs/tail")
async def logs_tail(limit: int = Query(10, ge=0, le=1000)):
    return list(LOGS)[-limit:]

