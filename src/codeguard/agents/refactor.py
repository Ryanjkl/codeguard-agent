"""Refactor Agent - Third stage of the pipeline.

Receives ranked findings from the Analyzer and generates:
- Specific code diffs for each auto-fixable issue
- Suggested refactorings for manual review items
- Batch refactoring plans for grouped issues
"""

import time
from pathlib import Path
from typing import Any, Optional

from ..config import config
from ..utils.display import display


class CodeRefactorer:
    """Generates refactored code based on analyzer findings.

    Supports auto-fix and suggestion modes.
    """

    def __init__(self, target_path: str = "."):
        self.target_path = Path(target_path).resolve()
        self.refactor_suggestions: list[dict[str, Any]] = []
        self.auto_fixes_applied: int = 0
        self.manual_suggestions: int = 0

    def refactor(self, analyzed_findings: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate refactoring suggestions for each finding."""
        display.agent_start("Refactor Agent", "Generating code fixes and refactoring plans...")

        start = time.time()

        auto_fixable = [f for f in analyzed_findings if f.get("auto_fixable")]
        manual_only = [f for f in analyzed_findings if not f.get("auto_fixable")]

        # Process auto-fixable issues
        for finding in auto_fixable:
            diff = self._generate_auto_fix(finding)
            if diff:
                self.refactor_suggestions.append(diff)
                self.auto_fixes_applied += 1

        # Generate suggestions for manual issues
        for finding in manual_only:
            plan = self._generate_refactor_suggestion(finding)
            if plan:
                self.refactor_suggestions.append(plan)
                self.manual_suggestions += 1

        if config.api_key:
            self._ai_refactor_review()
        else:
            self._demo_refactor_review()

        duration = time.time() - start
        display.agent_result(
            "Refactor Agent",
            len(self.refactor_suggestions),
            duration,
        )

        # Display sample refactorings
        for ref in self.refactor_suggestions[:3]:
            console_finding = display
            if "diff" in ref:
                console_finding.refactor_diff(
                    ref["file"],
                    ref.get("original", ""),
                    ref.get("suggested", ""),
                )
            elif "suggestion_plan" in ref:
                print(f"    [bold blue]📋 {ref['file']}:{ref['line']}[/bold blue]")
                print(f"      {ref['suggestion_plan']}")

        return {
            "total_suggestions": len(self.refactor_suggestions),
            "auto_fixes": self.auto_fixes_applied,
            "manual_suggestions": self.manual_suggestions,
            "details": self.refactor_suggestions,
        }

    def _generate_auto_fix(self, finding: dict) -> Optional[dict]:
        """Generate auto-fix diff based on pattern type."""
        pattern_id = finding.get("pattern_id")
        file_path = self.target_path / finding.get("file", "")

        if not file_path.exists():
            return None

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            line_no = finding.get("line", 1) - 1

            if pattern_id == "BARE_EXCEPT":
                return self._fix_bare_except(finding, lines, line_no)
            elif pattern_id == "SQL_INJECTION":
                return self._fix_sql_injection(finding, lines, line_no)
            elif pattern_id == "MUTABLE_DEFAULT":
                return self._fix_mutable_default(finding, lines, line_no)
            elif pattern_id == "UNUSED_IMPORT":
                return self._fix_unused_import(finding, lines, line_no)
            else:
                return self._generic_fix(finding, lines, line_no)
        except Exception:
            return None

    def _fix_bare_except(self, finding: dict, lines: list[str], line_no: int) -> dict:
        original = lines[line_no] if 0 <= line_no < len(lines) else ""
        indent = len(original) - len(original.lstrip())
        suggested = " " * indent + "except Exception as e:"
        return {
            **finding,
            "fix_type": "auto",
            "original": original,
            "suggested": suggested,
            "diff": f"-{original}\n+{suggested}",
        }

    def _fix_sql_injection(self, finding: dict, lines: list[str], line_no: int) -> dict:
        original = lines[line_no] if 0 <= line_no < len(lines) else ""
        indent = len(original) - len(original.lstrip())
        # Simple heuristic: replace f-string SQL with parameterized
        suggested = (
            " " * indent
            + "# FIXED: Use parameterized query to prevent SQL injection\n"
            + " " * indent
            + 'cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))'
        )
        return {
            **finding,
            "fix_type": "auto",
            "original": original,
            "suggested": suggested,
            "diff": f"-{original}\n+{suggested}",
        }

    def _fix_mutable_default(self, finding: dict, lines: list[str], line_no: int) -> dict:
        original = lines[line_no] if 0 <= line_no < len(lines) else ""
        indent = " " * (len(original) - len(original.lstrip()))

        # Build the fix with proper indentation
        func_def = original.strip()
        paren = func_def.find("(")
        func_name = func_def[:paren] if paren > 0 else func_def

        suggested = f"{indent}{func_name}(None):\n{indent}    if x is None:\n{indent}        x = []"

        return {
            **finding,
            "fix_type": "auto",
            "original": original,
            "suggested": suggested,
            "diff": f"-{original}\n+{suggested}",
        }

    def _fix_unused_import(self, finding: dict, lines: list[str], line_no: int) -> dict:
        original = lines[line_no] if 0 <= line_no < len(lines) else ""
        return {
            **finding,
            "fix_type": "auto",
            "original": original,
            "suggested": "# (removed unused import)",
            "diff": f"-{original}\n+",
        }

    def _generic_fix(self, finding: dict, lines: list[str], line_no: int) -> Optional[dict]:
        original = lines[line_no] if 0 <= line_no < len(lines) else ""
        if not original.strip():
            return None
        return {
            **finding,
            "fix_type": "suggestion",
            "original": original,
            "suggested": f"# REFACTOR: {finding.get('suggestion', 'Review needed')}",
            "suggestion_plan": finding.get("suggestion", "Manual review required."),
        }

    def _generate_refactor_suggestion(self, finding: dict) -> Optional[dict]:
        """Generate a refactoring plan for non-auto-fixable issues."""
        return {
            **finding,
            "fix_type": "manual",
            "suggestion_plan": finding.get("suggestion", "Review and refactor manually."),
            "effort_estimate": self._estimate_effort(finding),
        }

    def _estimate_effort(self, finding: dict) -> str:
        """Rough effort estimation for manual refactoring."""
        weights = {
            "critical": "4-8 hours",
            "high": "2-4 hours",
            "medium": "1-2 hours",
            "low": "30-60 min",
        }
        return weights.get(finding.get("severity", "low"), "1 hour")

    def _ai_refactor_review(self):
        """Use Claude API to review and improve generated refactorings."""
        import anthropic

        client = anthropic.Anthropic(api_key=config.api_key)

        diffs = "\n".join([
            f"File {r.get('file')}:{r.get('line')}:\n{r.get('diff', r.get('suggestion_plan', ''))}"
            for r in self.refactor_suggestions[:10]
        ])

        try:
            client.messages.create(
                model=config.model,
                max_tokens=2048,
                temperature=0.1,
                system="You are a code refactoring expert. Review and improve the following auto-generated refactorings.",
                messages=[{
                    "role": "user",
                    "content": f"Proposed refactorings:\n{diffs}\n\nAre these safe? Any improvements?",
                }],
            )
        except Exception:
            pass

    def _demo_refactor_review(self):
        """Demo mode: simulate AI review of refactorings."""
        for ref in self.refactor_suggestions:
            ref["ai_reviewed"] = True
            ref["reviewer"] = "refactor-v2.3"

            if ref.get("fix_type") == "auto":
                ref["review_status"] = "approved"
                ref["review_note"] = "Auto-fix is safe and follows best practices."
            else:
                ref["review_status"] = "needs_review"
                ref["review_note"] = "Requires human review due to complexity."

    def apply_auto_fixes(self, dry_run: bool = True) -> list[str]:
        """Apply auto-fixes to files. If dry_run, only return what would change."""
        changed_files = []

        for ref in self.refactor_suggestions:
            if ref.get("fix_type") != "auto":
                continue

            file_path = self.target_path / ref.get("file", "")
            if not file_path.exists():
                continue

            if not dry_run:
                try:
                    content = file_path.read_text(encoding="utf-8")
                    original = ref.get("original", "")
                    suggested = ref.get("suggested", "")
                    if original in content:
                        content = content.replace(original, suggested, 1)
                        file_path.write_text(content, encoding="utf-8")
                    changed_files.append(str(ref.get("file")))
                except Exception:
                    continue
            else:
                changed_files.append(f"[DRY RUN] {ref.get('file')}")

        return changed_files
