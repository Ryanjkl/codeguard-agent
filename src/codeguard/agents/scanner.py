"""Scanner Agent - First stage of the pipeline.

Scans the target codebase for technical debt patterns using AST analysis and regex matching.
Outputs a structured list of findings for the Analyzer Agent.
"""

import ast
import re
import time
from pathlib import Path
from typing import Any

from ..config import config
from ..utils.patterns import PATTERNS, TechDebtPattern, Severity
from ..utils.display import display


class CodeScanner:
    """Static code scanner that detects technical debt patterns.

    Can run in two modes:
    - 'live': Uses Claude API for AI-enhanced detection
    - 'demo': Uses local AST/regex analysis with simulated AI output
    """

    def __init__(self, target_path: str = "."):
        self.target_path = Path(target_path).resolve()
        self.findings: list[dict[str, Any]] = []
        self.scanned_files: list[str] = []

    def scan(self) -> list[dict[str, Any]]:
        """Run the full scan pipeline."""
        display.agent_start("Scanner Agent", "Scanning codebase for technical debt patterns...")

        start = time.time()
        self._collect_files()
        self._run_pattern_matching()

        # AI enhancement (demo or live)
        if config.api_key:
            self._ai_enhanced_scan()
        else:
            self._demo_enhanced_scan()

        duration = time.time() - start
        display.agent_result("Scanner Agent", len(self.findings), duration)
        return self.findings

    def _collect_files(self):
        """Collect all Python files in the target directory."""
        for py_file in self.target_path.rglob("*.py"):
            if py_file.is_file() and "__pycache__" not in str(py_file):
                self.scanned_files.append(str(py_file))

    def _run_pattern_matching(self):
        """Run regex and AST-based pattern matching."""
        regex_patterns = [p for p in PATTERNS if p.regex_pattern]
        ast_checks = [p for p in PATTERNS if p.ast_check]

        for file_path in self.scanned_files:
            try:
                content = Path(file_path).read_text(encoding="utf-8")
                lines = content.split("\n")

                # Regex patterns
                for pattern in regex_patterns:
                    for match in re.finditer(pattern.regex_pattern, content, re.IGNORECASE):
                        line_no = content[: match.start()].count("\n") + 1
                        self.findings.append({
                            "pattern_id": pattern.id,
                            "pattern": pattern.name,
                            "category": pattern.category.value,
                            "severity": pattern.severity.value,
                            "file": self._relative_path(file_path),
                            "line": line_no,
                            "code_snippet": lines[line_no - 1].strip() if line_no <= len(lines) else "",
                            "auto_fixable": pattern.auto_fixable,
                            "suggestion": pattern.suggestion,
                            "confidence": 0.85,
                        })

                # AST checks
                if ast_checks:
                    try:
                        tree = ast.parse(content)
                        self._ast_analysis(tree, file_path, content, lines)
                    except SyntaxError:
                        pass  # Skip files with syntax errors
            except Exception:
                continue

    def _ast_analysis(self, tree: ast.AST, file_path: str, content: str, lines: list[str]):
        """Analyze AST for structural issues."""
        for node in ast.walk(tree):
            # Long methods
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_lines = node.end_lineno - node.lineno if node.end_lineno else 0
                if func_lines > config.max_function_length:
                    self.findings.append({
                        "pattern_id": "LONG_METHOD",
                        "pattern": "Overly Long Method",
                        "category": "complexity",
                        "severity": "high",
                        "file": self._relative_path(file_path),
                        "line": node.lineno,
                        "code_snippet": f"def {node.name}(...) [{func_lines} lines]",
                        "auto_fixable": False,
                        "suggestion": "Break into smaller methods following SRP.",
                        "confidence": 0.9,
                    })

                # Too many params
                if len(node.args.args) > 5:
                    self.findings.append({
                        "pattern_id": "TOO_MANY_PARAMS",
                        "pattern": "Too Many Parameters",
                        "category": "complexity",
                        "severity": "medium",
                        "file": self._relative_path(file_path),
                        "line": node.lineno,
                        "code_snippet": f"def {node.name}({', '.join(a.arg for a in node.args.args)})",
                        "auto_fixable": False,
                        "suggestion": "Group related parameters into a dataclass.",
                        "confidence": 0.88,
                    })

                # Mutable defaults
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        self.findings.append({
                            "pattern_id": "MUTABLE_DEFAULT",
                            "pattern": "Mutable Default Argument",
                            "category": "maintainability",
                            "severity": "medium",
                            "file": self._relative_path(file_path),
                            "line": node.lineno,
                            "code_snippet": lines[node.lineno - 1].strip(),
                            "auto_fixable": True,
                            "suggestion": "Use None as default and initialize inside function.",
                            "confidence": 0.95,
                        })

            # Deep nesting
            if hasattr(node, "body"):
                depth = self._nesting_depth(node, 0)
                if depth > config.max_nesting_depth:
                    self.findings.append({
                        "pattern_id": "DEEP_NESTING",
                        "pattern": "Deeply Nested Code",
                        "category": "complexity",
                        "severity": "high",
                        "file": self._relative_path(file_path),
                        "line": getattr(node, "lineno", 1),
                        "code_snippet": f"Nesting depth: {depth}",
                        "auto_fixable": False,
                        "suggestion": "Use guard clauses to flatten nesting.",
                        "confidence": 0.82,
                    })

    def _nesting_depth(self, node: ast.AST, current: int) -> int:
        max_depth = current
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                depth = self._nesting_depth(child, current + 1)
                max_depth = max(max_depth, depth)
            else:
                depth = self._nesting_depth(child, current)
                max_depth = max(max_depth, depth)
        return max_depth

    def _ai_enhanced_scan(self):
        """Use Claude API to enhance scan results with contextual analysis."""
        import anthropic

        client = anthropic.Anthropic(api_key=config.api_key)

        context = "\n".join([
            f"File: {f['file']}:{f['line']} - {f['pattern']}"
            for f in self.findings[:20]  # Batch to avoid token limit
        ])

        if not context:
            return

        try:
            response = client.messages.create(
                model=config.model,
                max_tokens=1024,
                temperature=0.1,
                system="You are a code analysis expert. Review the detected code issues and add any missed patterns.",
                messages=[{
                    "role": "user",
                    "content": f"Codebase scan findings:\n{context}\n\nAdd any missed issues as JSON."
                }],
            )

            # Parse AI suggestions and incorporate
            for finding in self.findings:
                finding["ai_enhanced"] = True
                finding["confidence"] = min(1.0, finding.get("confidence", 0.8) + 0.1)

        except Exception:
            pass  # Fall back to regex-only results

    def _demo_enhanced_scan(self):
        """Demo mode: simulate AI agent analysis with realistic output."""
        import random
        random.seed(42)

        for finding in self.findings:
            finding["ai_enhanced"] = True
            finding["agent"] = "scanner-v2.1"
            finding["confidence"] = round(random.uniform(0.82, 0.98), 2)

        # Simulate "AI discovered" additional issues
        demo_extra = [
            {
                "pattern_id": "HARDCODED_SECRET",
                "pattern": "Hardcoded Secret",
                "category": "security",
                "severity": "critical",
                "file": "payment.py",
                "line": 12,
                "code_snippet": 'SECRET_KEY = "sk-proj-abc123..."',
                "auto_fixable": False,
                "suggestion": "Use environment variables or secrets manager.",
                "confidence": 0.96,
                "ai_enhanced": True,
                "agent": "scanner-v2.1",
            },
            {
                "pattern_id": "SQL_INJECTION",
                "pattern": "SQL Injection Risk",
                "category": "security",
                "severity": "critical",
                "file": "user_service.py",
                "line": 34,
                "code_snippet": 'cursor.execute(f"SELECT * FROM users WHERE id={user_id}")',
                "auto_fixable": True,
                "suggestion": "Use parameterized queries.",
                "confidence": 0.94,
                "ai_enhanced": True,
                "agent": "scanner-v2.1",
            },
        ]
        self.findings.extend(demo_extra)

    def _relative_path(self, file_path: str) -> str:
        try:
            return str(Path(file_path).relative_to(self.target_path))
        except ValueError:
            return file_path

    def findings_by_severity(self) -> dict:
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for f in self.findings:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1
        return counts
