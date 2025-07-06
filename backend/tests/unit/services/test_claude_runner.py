import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, create_autospec
from asyncio.subprocess import Process


@pytest.mark.unit
class TestClaudeCodeRunner:
    """Test ClaudeCodeRunner service."""
    
    @pytest.fixture
    def claude_runner(self):
        """Create ClaudeCodeRunner instance."""
        from app.services.claude_runner import ClaudeCodeRunner
        return ClaudeCodeRunner()
    
    async def test_start_task(self, claude_runner, tmp_path):
        """Test starting a Claude Code task."""
        task_id = "test-task-id"
        worktree_path = str(tmp_path)
        instructions = "Implement test feature"
        
        # Mock the subprocess
        mock_process = MagicMock()
        mock_process.stdout = AsyncMock()
        mock_process.stdin = AsyncMock()
        mock_process.stderr = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = None
        
        # Mock stdout iteration
        mock_process.stdout.__aiter__.return_value = [
            b"Starting Claude Code...\n",
            b"Processing instructions...\n",
            b"Task completed successfully\n"
        ].__iter__()
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_process) as mock_create:
            output_lines = []
            async for line in claude_runner.start_task(task_id, worktree_path, instructions):
                output_lines.append(line)
            
            # Verify subprocess was created correctly
            mock_create.assert_called_once_with(
                "claude", "code",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=worktree_path,
                env=claude_runner._get_environment()
            )
            
            # Verify instructions were sent
            mock_process.stdin.write.assert_called_once_with(instructions.encode())
            mock_process.stdin.drain.assert_called_once()
            
            # Verify output was streamed
            assert len(output_lines) == 3
            assert "Starting Claude Code" in output_lines[0]
            assert "Task completed successfully" in output_lines[2]
            
            # Verify process is tracked
            assert task_id in claude_runner.active_processes
    
    async def test_stop_task(self, claude_runner):
        """Test stopping a running task."""
        task_id = "test-task-id"
        
        # Create mock process
        mock_process = MagicMock()
        mock_process.terminate = AsyncMock()
        mock_process.wait = AsyncMock()
        mock_process.returncode = -15  # SIGTERM
        
        claude_runner.active_processes[task_id] = mock_process
        
        # Stop the task
        result = await claude_runner.stop_task(task_id)
        
        assert result is True
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()
        assert task_id not in claude_runner.active_processes
    
    async def test_stop_nonexistent_task(self, claude_runner):
        """Test stopping a task that doesn't exist."""
        result = await claude_runner.stop_task("nonexistent-task")
        assert result is False
    
    async def test_get_task_status(self, claude_runner):
        """Test getting task status."""
        task_id = "test-task-id"
        
        # Test when task doesn't exist
        status = await claude_runner.get_task_status(task_id)
        assert status == "not_found"
        
        # Test with running process
        mock_process = MagicMock()
        mock_process.returncode = None
        claude_runner.active_processes[task_id] = mock_process
        
        status = await claude_runner.get_task_status(task_id)
        assert status == "running"
        
        # Test with completed process
        mock_process.returncode = 0
        status = await claude_runner.get_task_status(task_id)
        assert status == "completed"
        
        # Test with failed process
        mock_process.returncode = 1
        status = await claude_runner.get_task_status(task_id)
        assert status == "failed"
    
    async def test_handle_process_error(self, claude_runner, tmp_path):
        """Test handling process errors."""
        task_id = "test-task-id"
        worktree_path = str(tmp_path)
        instructions = "Test instructions"
        
        # Mock subprocess to raise an error
        with patch('asyncio.create_subprocess_exec', side_effect=FileNotFoundError("claude not found")):
            output_lines = []
            async for line in claude_runner.start_task(task_id, worktree_path, instructions):
                output_lines.append(line)
            
            # Should yield error message
            assert len(output_lines) >= 1
            assert "Error" in output_lines[0]
            assert "claude not found" in output_lines[0]
    
    async def test_process_timeout(self, claude_runner, tmp_path):
        """Test task timeout handling."""
        task_id = "test-task-id"
        worktree_path = str(tmp_path)
        instructions = "Test instructions"
        
        # Mock process that never completes
        mock_process = MagicMock()
        mock_process.stdout = AsyncMock()
        mock_process.stdin = AsyncMock()
        mock_process.stderr = AsyncMock()
        mock_process.terminate = AsyncMock()
        mock_process.wait = AsyncMock()
        
        # Mock stdout to simulate hanging
        async def mock_readline():
            await asyncio.sleep(10)  # Simulate hanging
            return b""
        
        mock_process.stdout.__aiter__.return_value = [].__iter__()
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            # Set a short timeout for testing
            claude_runner.timeout = 0.1
            
            output_lines = []
            async for line in claude_runner.start_task(task_id, worktree_path, instructions):
                output_lines.append(line)
            
            # Should have timeout message
            assert any("timeout" in line.lower() for line in output_lines)
    
    async def test_concurrent_tasks(self, claude_runner, tmp_path):
        """Test running multiple tasks concurrently."""
        task_ids = ["task-1", "task-2", "task-3"]
        worktree_path = str(tmp_path)
        
        # Mock processes
        mock_processes = []
        for i, task_id in enumerate(task_ids):
            mock_process = MagicMock()
            mock_process.stdout = AsyncMock()
            mock_process.stdin = AsyncMock()
            mock_process.stderr = AsyncMock()
            mock_process.pid = 1000 + i
            
            # Different output for each task
            mock_process.stdout.__aiter__.return_value = [
                f"Output from {task_id}".encode()
            ].__iter__()
            
            mock_processes.append(mock_process)
        
        with patch('asyncio.create_subprocess_exec', side_effect=mock_processes):
            # Start all tasks
            tasks = []
            for task_id in task_ids:
                task = asyncio.create_task(
                    claude_runner.start_task(task_id, worktree_path, f"Instructions for {task_id}")
                )
                tasks.append(task)
            
            # Verify all processes are tracked
            await asyncio.sleep(0.1)  # Let tasks start
            assert len(claude_runner.active_processes) == 3
            
            # Clean up
            for task in tasks:
                task.cancel()
    
    async def test_environment_variables(self, claude_runner):
        """Test environment variable configuration."""
        env = claude_runner._get_environment()
        
        assert "CLAUDE_MODEL" in env
        assert env["CLAUDE_MODEL"] == "opus-4"
        assert "PATH" in env  # Should inherit system PATH
    
    async def test_cleanup_on_exit(self, claude_runner):
        """Test that processes are cleaned up properly."""
        task_id = "test-task-id"
        
        # Create mock process
        mock_process = MagicMock()
        mock_process.terminate = AsyncMock()
        mock_process.wait = AsyncMock()
        mock_process.returncode = None
        
        claude_runner.active_processes[task_id] = mock_process
        
        # Cleanup all processes
        await claude_runner.cleanup_all()
        
        mock_process.terminate.assert_called_once()
        assert len(claude_runner.active_processes) == 0