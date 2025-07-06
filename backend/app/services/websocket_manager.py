"""WebSocket manager for broadcasting task updates."""
from typing import Dict, Set
from fastapi import WebSocket
import json
import asyncio


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        self.active_connections[task_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, task_id: str):
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
    
    async def send_message(self, task_id: str, message: str):
        if task_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[task_id]:
                try:
                    await connection.send_text(message)
                except:
                    disconnected.add(connection)
            
            # Remove disconnected connections
            for conn in disconnected:
                self.active_connections[task_id].discard(conn)


# Global connection manager instance
manager = ConnectionManager()


async def broadcast_task_output(task_id: str, output: str):
    """Broadcast task output to all connected clients."""
    message = json.dumps({
        "type": "output",
        "task_id": task_id,
        "output": output,
        "timestamp": asyncio.get_event_loop().time()
    })
    
    await manager.send_message(task_id, message)