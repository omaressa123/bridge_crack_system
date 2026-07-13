from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from database import init_db
from logging_config import setup_logging
from routers import auth, bridges, cracks, reports, sensors, admin
from middleware.security import RateLimitMiddleware
from services.mqtt import start_mqtt_listener

logger = logging.getLogger(__name__)

_mqtt_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _mqtt_client
    setup_logging()
    init_db()
    _mqtt_client = start_mqtt_listener(
        active_websockets=sensors.connected_websockets,
        broadcast_fn=sensors.broadcast_to_dashboards,
    )
    logger.info("Application startup complete")
    yield
    if _mqtt_client is not None:
        _mqtt_client.loop_stop()
        _mqtt_client.disconnect()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="Bridge Crack Detection API",
    description="Modular backend for bridge infrastructure monitoring",
    version="2.0.0",
    lifespan=lifespan,
)

_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
allow_origins = [origin.strip() for origin in _cors_origins.split(",") if origin.strip()]

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(bridges.router)
app.include_router(cracks.router)
app.include_router(reports.router)
app.include_router(sensors.router)
app.include_router(admin.router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Preserve legacy `{error: ...}` response shape for the frontend."""
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"error": detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return validation errors in legacy `{error: ...}` shape."""
    errors = exc.errors()
    if errors:
        first = errors[0]
        loc = " ".join(str(part) for part in first.get("loc", []) if part != "body")
        message = f"{loc}: {first['msg']}".strip(": ")
    else:
        message = "Validation error"
    return JSONResponse(status_code=422, content={"error": message})


@app.get("/")
def read_root():
    return {"message": "Bridge Crack Detection Backend is running (Modular)!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
