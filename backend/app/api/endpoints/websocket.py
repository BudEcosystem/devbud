from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import asyncio
import json
from typing import Dict, Set

from app.core.database import get_db
from app.models import Task
from app.services.claude_runner import ClaudeCodeRunner
from app.services.websocket_manager import manager

router = APIRouter()
claude_runner = ClaudeCodeRunner()


@router.websocket("/task/{task_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    task_id: str
):
    """WebSocket endpoint for real-time task output streaming."""
    await manager.connect(websocket, task_id)
    
    try:
        # Keep connection alive
        while True:
            # Wait for messages from client (like ping/pong)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle client messages if needed
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except asyncio.TimeoutError:
                # Send periodic ping to keep connection alive
                await websocket.send_text(json.dumps({
                    "type": "ping",
                    "timestamp": asyncio.get_event_loop().time()
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)
    except Exception as e:
        manager.disconnect(websocket, task_id)
        raise e


@router.websocket("/tasks")
async def websocket_all_tasks(websocket: WebSocket):
    """WebSocket endpoint for monitoring all tasks."""
    await websocket.accept()
    
    try:
        while True:
            # Send periodic updates about all active tasks
            active_tasks = claude_runner.active_processes.keys()
            
            status_update = {
                "type": "status_update",
                "active_tasks": list(active_tasks),
                "timestamp": asyncio.get_event_loop().time()
            }
            
            await websocket.send_text(json.dumps(status_update))
            
            # Wait for 5 seconds before next update
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        pass
    except Exception:
        pass


