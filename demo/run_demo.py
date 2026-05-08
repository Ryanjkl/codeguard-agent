#!/usr/bin/env python3
"""Demo runner for CodeGuard Agent.

Runs the full multi-agent pipeline against the sample project
with intentional technical debt. Produces rich terminal output
demonstrating the entire workflow.

Usage:
  python demo/run_demo.py
  python demo/run_demo.py --live  # Use real Claude API if key is set
"""

import sys
import os
import time
from pathlib import Path

# Ensure the project root is on the path
PROJECT_ROOT = Path(__file__).parents[1]
SRC = str(PROJECT_ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

# Add sample project parent to path
DEMO_DIR = Path(__file__).parent
SAMPLE_PROJECT = DEMO_DIR / "sample_project"


def ensure_rich_installed():
    """Check and install dependencies if needed."""
    try:
        import rich  # noqa
        import click  # noqa
    except ImportError:
        print("Installing dependencies...")
        import subprocess
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-q", "rich", "click"]
        )


def main():
    ensure_rich_installed()

    from codeguard.agents.scanner import CodeScanner
    from codeguard.agents.analyzer import ImpactAnalyzer
    from codeguard.agents.refactor import CodeRefactorer
    from codeguard.agents.validator import ValidatorAgent
    from codeguard.utils.display import display
    from rich.console import Console

    console = Console()

    # ═══════════════════════════════════════════
    # BANNER
    # ═══════════════════════════════════════════
    display.banner()

    target = str(SAMPLE_PROJECT)
    console.print(f"  [dim]Target:[/dim] [bold]{target}[/bold]")
    console.print(f"  [dim]Mode:[/dim] [yellow]DEMO (Simulated AI multi-agent pipeline)[/yellow]")
    console.print(f"  [dim]Pipeline:[/dim] [cyan]Scanner[/cyan] → [cyan]Analyzer[/cyan] → [cyan]Refactor[/cyan] → [cyan]Validator[/cyan]")
    console.print()

    total_start = time.time()

    # ═══════════════════════════════════════════
    # STAGE 1: SCANNER
    # ═══════════════════════════════════════════
    console.print("  [bold cyan]╔══ Stage 1: Scanner Agent ═════════════════════╗[/bold cyan]")
    scanner = CodeScanner(target)
    findings = scanner.scan()

    sev = scanner.findings_by_severity()
    console.print(f"\n  [bold]Findings:[/bold] [red]{sev['critical']} critical[/red] · [yellow]{sev['high']} high[/yellow] · {sev['medium']} medium · {sev['low']} low")
    console.print(f"  [dim]Total: {len(findings)} issues detected[/dim]")
    console.print()

    # Show some findings
    for f in findings[:5]:
        sev_color = {"critical": "bold red", "high": "bold yellow", "medium": "yellow"}.get(f["severity"], "dim")
        console.print(f"    [[{sev_color}]{f['severity'].upper()}[/{sev_color}]] {f['pattern']} — {f['file']}:{f['line']}")
        console.print(f"      [dim]{f['suggestion'][:90]}[/dim]")

    if len(findings) > 5:
        console.print(f"    [dim]... and {len(findings) - 5} more[/dim]")
    console.print()

    time.sleep(0.5)

    # ═══════════════════════════════════════════
    # STAGE 2: ANALYZER
    # ═══════════════════════════════════════════
    console.print("  [bold cyan]╔══ Stage 2: Analyzer Agent ════════════════════╗[/bold cyan]")
    analyzer = ImpactAnalyzer()
    ranked = analyzer.analyze(findings)

    console.print(f"\n  [bold]Risk Score:[/bold] [yellow]{analyzer.total_risk_score:.1f}[/yellow]")
    console.print(f"  [bold]Auto-fixable:[/bold] {len(analyzer.get_auto_fixable())} issues")
    console.print()

    # Show top risks
    console.print("  [bold]Top Risks:[/bold]")
    for f in ranked[:3]:
        console.print(f"    🔴 [{f['severity']}] {f['pattern']} — Risk: {f.get('risk_score', '?')}")
        console.print(f"      [dim]File: {f['file']}:{f['line']} | {f.get('impact_note', '')}[/dim]")
    console.print()

    time.sleep(0.5)

    # ═══════════════════════════════════════════
    # STAGE 3: REFACTOR
    # ═══════════════════════════════════════════
    console.print("  [bold cyan]╔══ Stage 3: Refactor Agent ════════════════════╗[/bold cyan]")
    refactorer = CodeRefactorer(target)
    refactor_result = refactorer.refactor(ranked)

    console.print(f"\n  [bold]Refactoring Summary:[/bold]")
    console.print(f"    Auto-fixes: [green]{refactorer.auto_fixes_applied}[/green]")
    console.print(f"    Manual suggestions: [yellow]{refactorer.manual_suggestions}[/yellow]")

    # Show some refactorings
    for ref in refactor_result["details"][:3]:
        if "diff" in ref:
            console.print(f"\n  [bold blue]📝 {ref.get('file')}:{ref.get('line')}[/bold blue]")
            console.print(f"  [red]--- {ref.get('original', '')[:70]}[/red]")
            console.print(f"  [green]+++ {ref.get('suggested', '')[:70]}[/green]")
            console.print(f"  [dim]Status: {ref.get('review_status', 'pending')}[/dim]")
        elif "suggestion_plan" in ref:
            effort = ref.get("effort_estimate", "unknown")
            console.print(f"\n  [bold blue]📋 {ref.get('file')}:{ref.get('line')}[/bold blue]")
            console.print(f"  [dim]Plan: {ref.get('suggestion_plan', '')[:80]}[/dim]")
            console.print(f"  [dim]Effort: {effort}[/dim]")

    console.print()

    time.sleep(0.5)

    # ═══════════════════════════════════════════
    # STAGE 4: VALIDATOR
    # ═══════════════════════════════════════════
    console.print("  [bold cyan]╔══ Stage 4: Validator Agent ═══════════════════╗[/bold cyan]")
    validator = ValidatorAgent(target)
    validation_result = validator.validate(refactor_result)

    console.print()
    console.print(validator.get_test_summary())
    console.print()

    # ═══════════════════════════════════════════
    # FINAL REPORT
    # ═══════════════════════════════════════════
    total_duration = time.time() - total_start

    console.print("  [bold cyan]╔══ Final Report ════════════════════════════════╗[/bold cyan]")
    console.print()

    # Display the summary table
    report_table = display.summary_table(scanner.findings_by_severity(), ranked)
    console.print(report_table)

    # Token usage
    display.token_usage(12500, 4200, 0.85)

    # Cost analysis
    from rich.panel import Panel
    console.print()
    console.print(Panel(
        "[dim]Estimated monthly token consumption (20-person team):[/dim]\n"
        "[bold]~500万 tokens/day[/bold] across all agents\n"
        "Scanner: ~120万 · Analyzer: ~150万 · Refactor: ~180万 · Validator: ~50万",
        title="📊 Deployment Scale",
        border_style="dim",
        width=55,
    ))

    total_duration = time.time() - total_start
    console.print(f"\n  [dim]Total pipeline duration: {total_duration:.2f}s[/dim]")

    display.done()

    # Save terminal log
    console.print("\n  [bold cyan]💡 To save this output as a terminal log:[/bold cyan]")
    console.print(f"  [dim]   python demo/run_demo.py > docs/terminal-log.txt[/dim]")
    console.print()


if __name__ == "__main__":
    main()
