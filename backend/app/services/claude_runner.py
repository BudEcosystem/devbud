import asyncio
import os
from typing import AsyncGenerator, Dict, Optional
from datetime import datetime
from loguru import logger

from app.core.config import settings


class ClaudeCodeRunner:
    """Manages Claude Code CLI processes for code generation tasks."""
    
    def __init__(self):
        self.active_processes: Dict[str, asyncio.subprocess.Process] = {}
        self.timeout = settings.CLAUDE_TIMEOUT
    
    async def start_task(
        self, 
        task_id: str, 
        worktree_path: str, 
        instructions: str
    ) -> AsyncGenerator[str, None]:
        """Start Claude Code CLI and stream output."""
        try:
            # Create subprocess
            process = await asyncio.create_subprocess_exec(
                "claude", "code",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=worktree_path,
                env=self._get_environment()
            )
            
            self.active_processes[task_id] = process
            logger.info(f"Started Claude Code process for task {task_id} (PID: {process.pid})")
            
            # Send instructions
            if process.stdin:
                process.stdin.write(instructions.encode())
                await process.stdin.drain()
                process.stdin.close()
            
            # Stream output with timeout
            try:
                async with asyncio.timeout(self.timeout):
                    async for line in process.stdout:
                        output = line.decode('utf-8', errors='replace')
                        yield output
                        
                        # Check if process has terminated
                        if process.returncode is not None:
                            break
            
            except asyncio.TimeoutError:
                yield f"\n[ERROR] Task timeout after {self.timeout} seconds\n"
                await self.stop_task(task_id)
            
            # Wait for process to complete
            await process.wait()
            
            if process.returncode == 0:
                yield "\n[SUCCESS] Claude Code completed successfully\n"
            else:
                yield f"\n[ERROR] Claude Code exited with code {process.returncode}\n"
                
        except FileNotFoundError:
            yield "[ERROR] Claude Code CLI not found. Please ensure 'claude' is installed and in PATH\n"
        except Exception as e:
            yield f"[ERROR] Failed to start Claude Code: {str(e)}\n"
            logger.error(f"Error in Claude Code runner: {e}")
        finally:
            # Clean up
            if task_id in self.active_processes:
                del self.active_processes[task_id]
    
    async def stop_task(self, task_id: str) -> bool:
        """Stop a running Claude Code task."""
        if task_id not in self.active_processes:
            return False
        
        process = self.active_processes[task_id]
        
        try:
            # Terminate the process
            process.terminate()
            
            # Wait for it to terminate
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                # Force kill if it doesn't terminate
                process.kill()
                await process.wait()
            
            logger.info(f"Stopped Claude Code process for task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping task {task_id}: {e}")
            return False
        finally:
            if task_id in self.active_processes:
                del self.active_processes[task_id]
    
    async def get_task_status(self, task_id: str) -> str:
        """Get the status of a Claude Code task."""
        if task_id not in self.active_processes:
            return "not_found"
        
        process = self.active_processes[task_id]
        
        if process.returncode is None:
            return "running"
        elif process.returncode == 0:
            return "completed"
        else:
            return "failed"
    
    async def cleanup_all(self) -> None:
        """Stop all active Claude Code processes."""
        task_ids = list(self.active_processes.keys())
        
        for task_id in task_ids:
            await self.stop_task(task_id)
        
        logger.info("Cleaned up all Claude Code processes")
    
    def _get_environment(self) -> Dict[str, str]:
        """Get environment variables for Claude Code process."""
        env = os.environ.copy()
        
        # Add Claude-specific environment variables
        env["CLAUDE_MODEL"] = settings.CLAUDE_MODEL
        
        # Add any other required environment variables
        # env["CLAUDE_API_KEY"] = settings.CLAUDE_API_KEY  # If needed
        
        return env