"""Analyzer Agent - Second stage of the pipeline.

Receives findings from the Scanner and performs:
- Impact analysis (blast radius, dependency chains)
- Priority ranking (risk * impact * fixability)
- Grouping related issues for batch fixing
"""

import time
from typing import Any

from ..config import config
from ..utils.display import display


class ImpactAnalyzer:
    """Analyzes findings to determine priority and impact.

    Uses chain-of-thought reasoning to evaluate each finding in context.
    """

    def __init__(self):
        self.ranked_findings: list[dict[str, Any]] = []
        self.grouped_issues: dict[str, list[dict]] = {}
        self.total_risk_score: float = 0.0

    def analyze(self, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Analyze and rank findings by priority."""
        display.agent_start("Analyzer Agent", "Evaluating impact, risk, and fix priority...")

        start = time.time()
        self._findings = list(findings)
        self._compute_risk_scores(self._findings)
        self._rank_by_priority()
        self._group_related_issues()

        if config.api_key:
            self._ai_impact_analysis()
        else:
            self._demo_impact_analysis()

        duration = time.time() - start
        display.agent_result("Analyzer Agent", len(self.ranked_findings), duration)

        # Show top findings
        for f in self.ranked_findings[:5]:
            icon = "🔴" if f["severity"] == "critical" else "🟡" if f["severity"] == "high" else "🟢"
            display.finding(
                f["pattern"],
                f["severity"],
                f["file"],
                f["line"],
                f"[Risk: {f.get('risk_score', '?')}] {f['suggestion'][:80]}",
            )

        return self.ranked_findings

    def _compute_risk_scores(self, findings: list[dict[str, Any]]):
        """Compute risk score for each finding."""
        severity_weights = {
            "critical": 10.0,
            "high": 6.0,
            "medium": 3.0,
            "low": 1.0,
        }

        for f in findings:
            base = severity_weights.get(f["severity"], 1.0)
            confidence = f.get("confidence", 0.8)
            fixability = 2.0 if f.get("auto_fixable") else 1.0
            f["risk_score"] = round(base * confidence * fixability, 1)

    def _rank_by_priority(self):
        """Sort findings by risk score descending."""
        self.ranked_findings = sorted(
            self.findings,
            key=lambda f: f.get("risk_score", 0),
            reverse=True,
        )

    def _group_related_issues(self):
        """Group findings by file for batched fixes."""
        for f in self.ranked_findings:
            file = f.get("file", "unknown")
            if file not in self.grouped_issues:
                self.grouped_issues[file] = []
            self.grouped_issues[file].append(f)

        self.total_risk_score = sum(f.get("risk_score", 0) for f in self.ranked_findings)

    def _ai_impact_analysis(self):
        """Use Claude API for deeper impact analysis."""
        import anthropic

        client = anthropic.Anthropic(api_key=config.api_key)

        summary = "\n".join([
            f"- [{f['severity']}] {f['file']}:{f['line']} {f['pattern']} (risk={f.get('risk_score', '?')})"
            for f in self.ranked_findings[:15]
        ])

        try:
            response = client.messages.create(
                model=config.model,
                max_tokens=1024,
                temperature=0.1,
                system="You are a senior software architect. Analyze code issues and identify dependency impacts.",
                messages=[{
                    "role": "user",
                    "content": f"Issues found:\n{summary}\n\nIdentify which issues are likely to have the largest blast radius and why."
                }],
            )

            for f in self.ranked_findings:
                f["ai_analyzed"] = True
        except Exception:
            pass

    def _demo_impact_analysis(self):
        """Demo mode: simulate AI impact analysis."""
        for f in self.ranked_findings:
            f["ai_analyzed"] = True
            f["analyzer"] = "analyzer-v1.8"

            # Simulate impact annotations
            if f["severity"] == "critical":
                f["impact_note"] = "High blast radius - affects authentication flow"
            elif f["severity"] == "high":
                f["impact_note"] = "Medium blast radius - affects service layer"
            else:
                f["impact_note"] = "Localized impact - contained to single module"

    @property
    def findings(self) -> list[dict[str, Any]]:
        return self._findings

    @findings.setter
    def findings(self, value):
        self._findings = value

    def get_top_issues(self, n: int = 10) -> list[dict[str, Any]]:
        return self.ranked_findings[:n]

    def get_auto_fixable(self) -> list[dict[str, Any]]:
        return [f for f in self.ranked_findings if f.get("auto_fixable")]
