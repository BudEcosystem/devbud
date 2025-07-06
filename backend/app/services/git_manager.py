import asyncio
import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger


class GitWorktreeManager:
    """Manages Git worktrees for isolated development environments."""
    
    def __init__(self, base_path: str = "~/.devbud/worktrees"):
        self.base_path = Path(base_path).expanduser()
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def create_worktree(
        self, 
        repo_path: str, 
        branch_name: str,
        base_branch: Optional[str] = None
    ) -> str:
        """Create a new worktree for the given repository and branch."""
        repo_path = Path(repo_path).expanduser().absolute()
        repo_name = repo_path.name
        worktree_path = self.base_path / repo_name / branch_name
        
        try:
            # Create worktree directory
            worktree_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Build git worktree command
            cmd = f"git -C {repo_path} worktree add {worktree_path}"
            
            if base_branch:
                # Create new branch from specific base
                cmd += f" -b {branch_name} {base_branch}"
            else:
                # Create new branch from current HEAD
                cmd += f" -b {branch_name}"
            
            # Execute worktree creation
            await self._run_command(cmd)
            
            # Install dependencies if needed
            await self._install_dependencies(str(worktree_path))
            
            logger.info(f"Created worktree at {worktree_path}")
            return str(worktree_path)
            
        except Exception as e:
            # Clean up on failure
            if worktree_path.exists():
                await self.remove_worktree(str(worktree_path))
            raise e
    
    async def remove_worktree(self, worktree_path: str) -> None:
        """Remove a worktree."""
        worktree_path = Path(worktree_path).expanduser().absolute()
        
        # Find the main repository path
        result = await self._run_command(
            "git worktree list --porcelain",
            cwd=str(worktree_path.parent.parent)
        )
        
        # Remove the worktree
        await self._run_command(f"git worktree remove {worktree_path} --force")
        
        # Clean up the directory if it still exists
        if worktree_path.exists():
            import shutil
            shutil.rmtree(worktree_path)
        
        logger.info(f"Removed worktree at {worktree_path}")
    
    async def list_worktrees(self, repo_path: str) -> List[Dict[str, str]]:
        """List all worktrees for a repository."""
        repo_path = Path(repo_path).expanduser().absolute()
        
        result = await self._run_command(
            "git worktree list --porcelain",
            cwd=str(repo_path)
        )
        
        worktrees = []
        current_worktree = {}
        
        for line in result.split('\n'):
            if line.startswith('worktree '):
                if current_worktree:
                    worktrees.append(current_worktree)
                current_worktree = {'path': line[9:]}
            elif line.startswith('HEAD '):
                current_worktree['head'] = line[5:]
            elif line.startswith('branch '):
                current_worktree['branch'] = line[7:]
            elif line.startswith('detached'):
                current_worktree['detached'] = True
            elif line == '' and current_worktree:
                worktrees.append(current_worktree)
                current_worktree = {}
        
        if current_worktree:
            worktrees.append(current_worktree)
        
        return worktrees
    
    async def validate_repository(self, repo_path: str) -> bool:
        """Validate if path is a git repository."""
        repo_path = Path(repo_path).expanduser().absolute()
        
        if not repo_path.exists():
            return False
        
        try:
            await self._run_command("git rev-parse --git-dir", cwd=str(repo_path))
            return True
        except Exception:
            return False
    
    async def get_current_branch(self, repo_path: str) -> str:
        """Get the current branch of a repository."""
        repo_path = Path(repo_path).expanduser().absolute()
        
        result = await self._run_command(
            "git rev-parse --abbrev-ref HEAD",
            cwd=str(repo_path)
        )
        
        return result.strip()
    
    async def _install_dependencies(self, worktree_path: str) -> None:
        """Install project dependencies in the worktree."""
        worktree_path = Path(worktree_path)
        
        # Check for package managers in order of preference
        if (worktree_path / "bun.lockb").exists():
            await self._run_command("bun install", cwd=str(worktree_path))
        elif (worktree_path / "package-lock.json").exists():
            await self._run_command("npm install", cwd=str(worktree_path))
        elif (worktree_path / "yarn.lock").exists():
            await self._run_command("yarn install", cwd=str(worktree_path))
        elif (worktree_path / "pnpm-lock.yaml").exists():
            await self._run_command("pnpm install", cwd=str(worktree_path))
        elif (worktree_path / "package.json").exists():
            # Default to npm if package.json exists but no lock file
            await self._run_command("npm install", cwd=str(worktree_path))
        elif (worktree_path / "requirements.txt").exists():
            # Python project
            await self._run_command("pip install -r requirements.txt", cwd=str(worktree_path))
        elif (worktree_path / "Pipfile").exists():
            # Python project with pipenv
            await self._run_command("pipenv install", cwd=str(worktree_path))
        elif (worktree_path / "poetry.lock").exists():
            # Python project with poetry
            await self._run_command("poetry install", cwd=str(worktree_path))
        
        logger.info(f"Dependencies installed for {worktree_path}")
    
    async def _run_command(self, command: str, cwd: Optional[str] = None) -> str:
        """Run a shell command asynchronously."""
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(
                f"Command failed: {command}\n"
                f"Error: {stderr.decode()}"
            )
        
        return stdout.decode()