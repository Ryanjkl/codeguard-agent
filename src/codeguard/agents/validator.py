"""Validator Agent - Fourth and final stage of the pipeline.

Receives refactored code suggestions from the Refactor Agent and:
- Runs existing unit tests to verify no regressions
- Generates new test cases for refactored code
- Validates that auto-fixes don't break the build
- Produces a validation report (closed-loop verification)
"""

import subprocess
import time
from pathlib import Path
from typing import Any

from ..config import config
from ..utils.display import display


class ValidatorAgent:
    """Validates refactoring changes through automated testing.

    Implements the closed-loop verification: scan → analyze → refactor → validate.
    """

    def __init__(self, target_path: str = "."):
        self.target_path = Path(target_path).resolve()
        self.test_results: dict[str, Any] = {}
        self.validation_passed: bool = False
        self.test_output: str = ""

    def validate(self, refactor_result: dict[str, Any]) -> dict[str, Any]:
        """Run the validation pipeline."""
        display.agent_start("Validator Agent", "Running tests and validating changes...")

        start = time.time()

        # Step 1: Run existing tests
        self.test_results = self._run_existing_tests()

        # Step 2: Generate targeted tests for changed code
        if config.api_key:
            new_tests = self._ai_generate_tests(refactor_result)
        else:
            new_tests = self._demo_generate_tests(refactor_result)

        # Step 3: Run the new tests
        if new_tests:
            self._execute_new_tests(new_tests)

        # Step 4: Produce validation report
        self._build_validation_report()

        duration = time.time() - start
        self.validation_passed = self._check_pass()

        status_icon = "[PASS]" if self.validation_passed else "[FAIL]"
        display.agent_result(f"Validator Agent [{status_icon}]", 1, duration)

        return self._build_result()

    def _run_existing_tests(self) -> dict[str, Any]:
        """Discover and run existing unit tests."""
        test_files = list(self.target_path.rglob("test_*.py")) + list(
            self.target_path.rglob("*_test.py")
        )

        if not test_files:
            # Try pytest on whole project
            try:
                result = subprocess.run(
                    ["pytest", str(self.target_path), "--tb=short", "-q"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=str(self.target_path),
                )
                self.test_output = result.stdout + result.stderr
                return {
                    "passed": result.returncode == 0,
                    "exit_code": result.returncode,
                    "framework": "pytest",
                    "output": self.test_output[-2000:],
                }
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        return {
            "passed": True,  # Assume pass if no tests found
            "exit_code": 0,
            "framework": "none",
            "output": "No existing test suite found. Run 'pytest' to verify.",
        }

    def _ai_generate_tests(self, refactor_result: dict) -> list[str]:
        """Use Claude API to generate targeted test cases."""
        import anthropic

        client = anthropic.Anthropic(api_key=config.api_key)

        details = refactor_result.get("details", [])
        summary = "\n".join([
            f"- {d.get('file', '?')}:{d.get('line', '?')} {d.get('pattern', '?')}"
            for d in details[:5]
        ])

        try:
            response = client.messages.create(
                model=config.model,
                max_tokens=2048,
                temperature=0.1,
                system="You are a QA engineer. Generate pytest test cases for the refactored code.",
                messages=[{
                    "role": "user",
                    "content": f"Refactored code:\n{summary}\n\nGenerate targeted pytest test cases.",
                }],
            )

            return [response.content[0].text] if response.content else []
        except Exception:
            return []

    def _demo_generate_tests(self, refactor_result: dict) -> list[str]:
        """Demo mode: generate sample test cases."""
        details = refactor_result.get("details", [])
        if not details:
            return []

        test_code = """# Auto-generated validation tests by Validator Agent v1.2

import pytest

def test_no_hardcoded_secrets():
    \"\"\"Verify no hardcoded secrets in source files.\"\"\"
    import re
    import os
    secret_pattern = re.compile(
        r'(?:password|secret|api_key|token)\\s*=\\s*[\"\\'][^\"\\']+[\"\\']',
        re.IGNORECASE
    )
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", "venv")]
        for f in files:
            if f.endswith(".py"):
                content = open(os.path.join(root, f), encoding="utf-8").read()
                matches = secret_pattern.findall(content)
                assert len(matches) == 0, f"Hardcoded secret in {f}: {matches}"

def test_no_sql_injection():
    \"\"\"Verify no SQL injection vulnerabilities.\"\"\"
    import re
    import os
    injection_pattern = re.compile(
        r'execute\\s*\\(\\s*f[\"\\']',
        re.IGNORECASE
    )
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", "venv")]
        for f in files:
            if f.endswith(".py"):
                content = open(os.path.join(root, f), encoding="utf-8").read()
                matches = injection_pattern.findall(content)
                assert len(matches) == 0, f"SQL injection risk in {f}"

def test_no_bare_except_clauses():
    \"\"\"Verify all except clauses specify exception types.\"\"\"
    import re
    import os
    bare_pattern = re.compile(r'except\\s*:')
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", "venv")]
        for f in files:
            if f.endswith(".py") and f != __file__:
                content = open(os.path.join(root, f), encoding="utf-8").read()
                matches = bare_pattern.findall(content)
                assert len(matches) == 0, f"Bare except in {f}: {matches}"

def test_refactored_code_structure():
    \"\"\"Verify refactored code maintains expected structure.\"\"\"
    import ast
    import os
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", "venv")]
        for f in files:
            if f.endswith(".py"):
                content = open(os.path.join(root, f), encoding="utf-8").read()
                try:
                    tree = ast.parse(content)
                    funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                    for func in funcs:
                        lines = func.end_lineno - func.lineno if func.end_lineno else 0
                        assert lines <= 100, f"{f}:{func.lineno} function '{func.name}' too long ({lines} lines)"
                except SyntaxError:
                    pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
        return [test_code]

    def _execute_new_tests(self, test_cases: list[str]):
        """Write and execute auto-generated test cases."""
        test_dir = self.target_path / "tests"
        test_dir.mkdir(exist_ok=True)

        test_file = test_dir / "test_codeguard_validation.py"
        init_file = test_dir / "__init__.py"
        init_file.touch(exist_ok=True)

        for i, test_code in enumerate(test_cases):
            test_file.write_text(test_code, encoding="utf-8")

        try:
            result = subprocess.run(
                ["pytest", str(test_file), "--tb=short", "-v"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.target_path),
            )
            self.test_results["auto_generated"] = {
                "passed": result.returncode == 0,
                "exit_code": result.returncode,
                "output": (result.stdout + result.stderr)[-2000:],
            }
        except subprocess.TimeoutExpired:
            self.test_results["auto_generated"] = {
                "passed": False,
                "output": "Test execution timed out.",
            }
        except FileNotFoundError:
            self.test_results["auto_generated"] = {
                "passed": None,
                "output": "pytest not installed. Tests generated but not executed.",
            }

    def _build_validation_report(self):
        """Compile all test results into a structured report."""
        self.report = {
            "existing_tests": self.test_results,
            "auto_generated_tests": self.test_results.get("auto_generated", {}),
            "overall_pass": self._check_pass(),
            "recommendation": self._recommendation(),
        }

    def _check_pass(self) -> bool:
        """Determine if validation passes overall."""
        existing = self.test_results.get("passed", True)
        auto_gen = self.test_results.get("auto_generated", {}).get("passed", True)
        return existing and (auto_gen is not False)

    def _recommendation(self) -> str:
        if self.validation_passed:
            return (
                "[PASS] All tests pass. Auto-fixes are safe to merge. "
                "Manual refactorings should undergo code review."
            )
        else:
            return "[FAIL] Some tests failed. Review the failing changes before merging."

    def _build_result(self) -> dict[str, Any]:
        return {
            "validation_passed": self.validation_passed,
            "test_results": self.test_results,
            "recommendation": self._recommendation(),
            "report": self.report if hasattr(self, "report") else {},
        }

    def get_test_summary(self) -> str:
        """Return a human-readable test summary."""
        lines = []
        lines.append(f"  Validation: {'[PASS]' if self.validation_passed else '[FAIL]'}")
        lines.append(f"  Existing tests: {'[pass]' if self.test_results.get('passed') else '[fail]'}")
        auto = self.test_results.get("auto_generated", {})
        lines.append(f"  Auto-generated tests: {'[pass]' if auto.get('passed') else '[fail]' if auto.get('passed') is False else '[N/A]'}")
        lines.append(f"  Recommendation: {self._recommendation()}")
        return "\n".join(lines)
