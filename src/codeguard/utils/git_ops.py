"""Git operations: branch creation, PR generation, diff analysis."""

import os
import subprocess
from pathlib import Path
from typing import Optional


class GitOps:
    """Minimal git operations wrapper."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()

    def _run(self, *args: str, capture: bool = True) -> str:
        """Run a git command and return output."""
        cmd = ["git", "-C", str(self.repo_path)] + list(args)
        if capture:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, check=True)
            return ""

    def is_repo(self) -> bool:
        return self.repo_path.joinpath(".git").exists()

    def current_branch(self) -> str:
        return self._run("rev-parse", "--abbrev-ref", "HEAD")

    def has_changes(self) -> bool:
        return bool(self._run("status", "--porcelain"))

    def create_refactor_branch(self, base: str = "main") -> str:
        import time
        timestamp = int(time.time())
        branch_name = f"codeguard/auto-refactor-{timestamp}"
        self._run("checkout", "-b", branch_name, base)
        return branch_name

    def stage_all(self):
        self._run("add", "-A")

    def commit(self, message: str):
        self._run("commit", "-m", message)

    def diff(self) -> str:
        return self._run("diff", "HEAD")

    def diff_files(self) -> list[str]:
        return self._run("diff", "--name-only", "HEAD").split("\n")

    def log(self, n: int = 5) -> str:
        return self._run("log", f"-{n}", "--oneline", "--decorate")

    def push(self, branch: str, remote: str = "origin"):
        self._run("push", "-u", remote, branch)

    def create_pr(self, title: str, body: str, base: str = "main") -> Optional[str]:
        """Create a PR using gh CLI if available."""
        try:
            result = subprocess.run(
                ["gh", "pr", "create", "--title", title, "--body", body, "--base", base],
                capture_output=True,
                text=True,
                cwd=str(self.repo_path),
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except FileNotFoundError:
            pass
        return None

    def get_diff_for_ai(self, target_branch: str = "main") -> str:
        """Get a clean diff for AI analysis."""
        return self._run("diff", target_branch, "--unified=3")
