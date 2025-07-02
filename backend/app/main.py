from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
from .config import settings
from .api import health, debate
import logging

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.cors_origins,
    logger=True,
    engineio_logger=True
)

# Create FastAPI app
app = FastAPI(
    title="NekoMimi Council API",
    description="AI-powered debate system with multiple personas",
    version="1.0.0",
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(debate.router, prefix="/api", tags=["debate"])

# Set Socket.IO instance for debate module
debate.set_socketio(sio)

# Mount Socket.IO
socket_app = socketio.ASGIApp(sio, app)

@app.on_event("startup")
async def startup_event():
    logger.info("NekoMimi Council API starting up...")
    logger.info(f"AI Provider: {settings.ai_provider}")
    logger.info(f"Debug mode: {settings.debug}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("NekoMimi Council API shutting down...")

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")

@sio.event
async def join_room(sid, room):
    """Join a Socket.IO room for debate updates"""
    await sio.enter_room(sid, room)
    logger.info(f"Client {sid} joined room: {room}")

@sio.event
async def leave_room(sid, room):
    """Leave a Socket.IO room"""
    await sio.leave_room(sid, room)
    logger.info(f"Client {sid} left room: {room}")

# Export the socket app for uvicorn
app = socket_app