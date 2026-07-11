from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import auth, bridges, cracks, reports, sensors
from services.mqtt import start_mqtt_listener

app = FastAPI(
    title="Bridge Crack Detection API",
    description="Modular backend for bridge infrastructure monitoring",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(bridges.router)
app.include_router(cracks.router)
app.include_router(reports.router)
app.include_router(sensors.router)

@app.on_event("startup")
async def on_startup():
    # Initialize database tables
    init_db()
    
    # Start MQTT ingestion
    start_mqtt_listener(
        active_websockets=sensors.connected_websockets,
        broadcast_fn=sensors.broadcast_to_dashboards
    )

@app.get("/")
def read_root():
    return {"message": "Bridge Crack Detection Backend is running (Modular)!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
