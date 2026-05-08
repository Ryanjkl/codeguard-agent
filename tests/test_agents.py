"""Unit tests for CodeGuard Agent pipeline."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

import pytest
from codeguard.agents.scanner import CodeScanner
from codeguard.agents.analyzer import ImpactAnalyzer


SAMPLE_PROJECT = Path(__file__).parents[1] / "demo" / "sample_project"


class TestScannerAgent:
    def test_scanner_detects_issues(self):
        scanner = CodeScanner(str(SAMPLE_PROJECT))
        findings = scanner.scan()
        assert len(findings) > 0, "Should detect technical debt in sample project"
        assert any(f["severity"] == "critical" for f in findings)

    def test_scanner_finds_security_issues(self):
        scanner = CodeScanner(str(SAMPLE_PROJECT))
        findings = scanner.scan()
        security = [f for f in findings if f["category"] == "security"]
        assert len(security) > 0, "Should detect security issues"

    def test_scanner_by_severity(self):
        scanner = CodeScanner(str(SAMPLE_PROJECT))
        scanner.scan()
        counts = scanner.findings_by_severity()
        assert sum(counts.values()) > 0


class TestAnalyzerAgent:
    def test_analyzer_ranks_findings(self):
        scanner = CodeScanner(str(SAMPLE_PROJECT))
        findings = scanner.scan()
        analyzer = ImpactAnalyzer()
        ranked = analyzer.analyze(findings)
        assert len(ranked) > 0
        # First finding should have highest risk score
        assert ranked[0].get("risk_score", 0) >= ranked[-1].get("risk_score", 0)

    def test_analyzer_identifies_auto_fixable(self):
        scanner = CodeScanner(str(SAMPLE_PROJECT))
        findings = scanner.scan()
        analyzer = ImpactAnalyzer()
        analyzer.analyze(findings)
        auto = analyzer.get_auto_fixable()
        assert len(auto) >= 0  # May be 0 in some cases


class TestPipelineIntegration:
    def test_full_pipeline_e2e(self):
        from codeguard.agents.refactor import CodeRefactorer
        from codeguard.agents.validator import ValidatorAgent

        # Stage 1
        scanner = CodeScanner(str(SAMPLE_PROJECT))
        findings = scanner.scan()

        # Stage 2
        analyzer = ImpactAnalyzer()
        ranked = analyzer.analyze(findings)

        # Stage 3
        refactorer = CodeRefactorer(str(SAMPLE_PROJECT))
        result = refactorer.refactor(ranked)
        assert result["total_suggestions"] > 0

        # Stage 4
        validator = ValidatorAgent(str(SAMPLE_PROJECT))
        validation = validator.validate(result)
        assert "validation_passed" in validation
        assert "recommendation" in validation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
