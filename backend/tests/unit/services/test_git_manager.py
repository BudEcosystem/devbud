import pytest
import os
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.unit
class TestGitWorktreeManager:
    """Test GitWorktreeManager service."""
    
    @pytest.fixture
    def git_manager(self, tmp_path):
        """Create GitWorktreeManager instance with test path."""
        from app.services.git_manager import GitWorktreeManager
        return GitWorktreeManager(base_path=str(tmp_path / "worktrees"))
    
    async def test_create_worktree(self, git_manager, test_repo_path):
        """Test creating a new worktree."""
        branch_name = "feature-test"
        
        worktree_path = await git_manager.create_worktree(
            repo_path=test_repo_path,
            branch_name=branch_name
        )
        
        # Verify worktree was created
        assert os.path.exists(worktree_path)
        assert branch_name in worktree_path
        
        # Verify it's a valid git worktree
        result = subprocess.run(
            ["git", "worktree", "list"],
            cwd=test_repo_path,
            capture_output=True,
            text=True
        )
        assert worktree_path in result.stdout
    
    async def test_create_worktree_with_base_branch(self, git_manager, test_repo_path):
        """Test creating worktree from specific base branch."""
        # Create a base branch first
        subprocess.run(
            ["git", "checkout", "-b", "develop"],
            cwd=test_repo_path,
            check=True
        )
        
        worktree_path = await git_manager.create_worktree(
            repo_path=test_repo_path,
            branch_name="feature-from-develop",
            base_branch="develop"
        )
        
        # Verify branch was created from develop
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=worktree_path,
            capture_output=True,
            text=True
        )
        assert result.stdout.strip() == "feature-from-develop"
    
    async def test_remove_worktree(self, git_manager, test_repo_path):
        """Test removing a worktree."""
        # Create worktree first
        branch_name = "feature-to-remove"
        worktree_path = await git_manager.create_worktree(
            repo_path=test_repo_path,
            branch_name=branch_name
        )
        
        # Remove worktree
        await git_manager.remove_worktree(worktree_path)
        
        # Verify it was removed
        assert not os.path.exists(worktree_path)
        
        # Verify git knows it's removed
        result = subprocess.run(
            ["git", "worktree", "list"],
            cwd=test_repo_path,
            capture_output=True,
            text=True
        )
        assert worktree_path not in result.stdout
    
    async def test_list_worktrees(self, git_manager, test_repo_path):
        """Test listing all worktrees for a repository."""
        # Create multiple worktrees
        branches = ["feature-1", "feature-2", "feature-3"]
        created_paths = []
        
        for branch in branches:
            path = await git_manager.create_worktree(
                repo_path=test_repo_path,
                branch_name=branch
            )
            created_paths.append(path)
        
        # List worktrees
        worktrees = await git_manager.list_worktrees(test_repo_path)
        
        assert len(worktrees) >= len(branches)  # Main worktree + created ones
        
        # Verify our worktrees are in the list
        worktree_paths = [w["path"] for w in worktrees]
        for path in created_paths:
            assert path in worktree_paths
    
    async def test_install_dependencies_npm(self, git_manager, tmp_path):
        """Test installing npm dependencies in worktree."""
        # Create a fake worktree with package.json
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()
        
        package_json = {
            "name": "test-project",
            "dependencies": {
                "express": "^4.18.0"
            }
        }
        
        import json
        (worktree_path / "package.json").write_text(json.dumps(package_json))
        
        with patch('app.services.git_manager.GitWorktreeManager._run_command') as mock_run:
            mock_run.return_value = None
            await git_manager._install_dependencies(str(worktree_path))
            
            # Verify npm install was called
            mock_run.assert_called_with("npm install", str(worktree_path))
    
    async def test_install_dependencies_no_package_manager(self, git_manager, tmp_path):
        """Test installing dependencies when no package manager is detected."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()
        
        # No package.json or other package files
        result = await git_manager._install_dependencies(str(worktree_path))
        
        # Should complete without error
        assert result is None
    
    async def test_validate_repository_path(self, git_manager):
        """Test repository path validation."""
        # Valid git repository
        assert await git_manager.validate_repository(self.test_repo_path) is True
        
        # Non-existent path
        assert await git_manager.validate_repository("/non/existent/path") is False
        
        # Not a git repository
        non_git_path = self.tmp_path / "not-git"
        non_git_path.mkdir()
        assert await git_manager.validate_repository(str(non_git_path)) is False
    
    async def test_get_current_branch(self, git_manager, test_repo_path):
        """Test getting current branch of repository."""
        branch = await git_manager.get_current_branch(test_repo_path)
        assert branch in ["main", "master"]  # Could be either
        
        # Create and checkout new branch
        subprocess.run(
            ["git", "checkout", "-b", "test-branch"],
            cwd=test_repo_path,
            check=True
        )
        
        branch = await git_manager.get_current_branch(test_repo_path)
        assert branch == "test-branch"
    
    async def test_cleanup_worktree_on_error(self, git_manager, test_repo_path):
        """Test that worktree is cleaned up if creation fails."""
        with patch('app.services.git_manager.GitWorktreeManager._install_dependencies') as mock_install:
            mock_install.side_effect = Exception("Installation failed")
            
            with pytest.raises(Exception, match="Installation failed"):
                await git_manager.create_worktree(
                    repo_path=test_repo_path,
                    branch_name="feature-fail"
                )
            
            # Verify worktree was cleaned up
            worktrees = await git_manager.list_worktrees(test_repo_path)
            assert not any("feature-fail" in w["path"] for w in worktrees)