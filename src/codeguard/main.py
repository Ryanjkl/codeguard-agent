"""CodeGuard Agent - Main CLI entry point.

Orchestrates the multi-agent pipeline:
  Scanner → Analyzer → Refactor → Validator

Usage:
  codeguard scan /path/to/project
  codeguard scan /path/to/project --auto-fix
  codeguard scan /path/to/project --output json
"""

import sys
import time
import json
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from .config import config
from .agents.scanner import CodeScanner
from .agents.analyzer import ImpactAnalyzer
from .agents.refactor import CodeRefactorer
from .agents.validator import ValidatorAgent
from .utils.display import display
from .utils.git_ops import GitOps


console = Console()


@click.group()
@click.version_option(version="1.0.0", prog_name="codeguard")
@click.option("--api-key", envvar="ANTHROPIC_API_KEY", help="Anthropic API key (or set ANTHROPIC_API_KEY env)")
@click.option("--model", default="claude-sonnet-4-6", help="Claude model to use")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def cli(ctx, api_key, model, verbose):
    """CodeGuard Agent - AI-powered code review & refactoring.

    Multi-agent pipeline: Scanner → Analyzer → Refactor → Validator.
    """
    ctx.ensure_object(dict)
    ctx.obj["api_key"] = api_key
    ctx.obj["model"] = model
    ctx.obj["verbose"] = verbose

    if api_key:
        config.api_key = api_key
    config.model = model
    config.verbose = verbose


@cli.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--auto-fix", is_flag=True, help="Automatically apply safe fixes")
@click.option("--output", "-o", type=click.Choice(["terminal", "json", "markdown"]), default="terminal")
@click.option("--max-line-length", type=int, default=50, help="Max function length threshold")
@click.option("--create-pr", is_flag=True, help="Create a GitHub PR with refactoring changes")
@click.pass_context
def scan(ctx, path, auto_fix, output, max_line_length, create_pr):
    """Scan a codebase for technical debt and suggest refactorings.

    PATH: Target project directory to analyze.
    """
    target = Path(path).resolve()
    config.target_path = str(target)
    config.max_function_length = max_line_length
    config.output_format = output

    # ─── Banner ───────────────────────────────────────────
    display.banner()
    console.print(f"  [dim]Target:[/dim] [bold]{target}[/bold]")
    console.print(f"  [dim]Mode:[/dim] {'[green]LIVE (Claude API)[/green]' if ctx.obj['api_key'] else '[yellow]DEMO (Simulated AI)[/yellow]'}")
    console.print(f"  [dim]Auto-fix:[/dim] {'[green]enabled[/green]' if auto_fix else '[dim]disabled[/dim]'}")
    console.print()

    total_start = time.time()

    # ═══════════════════════════════════════════════════════
    # STAGE 1: SCANNER AGENT
    # ═══════════════════════════════════════════════════════
    scanner = CodeScanner(str(target))
    findings = scanner.scan()

    if not findings:
        console.print("[green]No technical debt detected. Codebase looks clean![/green]")
        return

    # Display scanner summary
    sev_counts = scanner.findings_by_severity()
    console.print(
        f"\n  [bold]Scanner Summary:[/bold] "
        f"[red]{sev_counts['critical']} critical[/red] · "
        f"[yellow]{sev_counts['high']} high[/yellow] · "
        f"[dim]{sev_counts['medium']} medium[/dim] · "
        f"{sev_counts['low']} low"
    )

    # ═══════════════════════════════════════════════════════
    # STAGE 2: ANALYZER AGENT
    # ═══════════════════════════════════════════════════════
    analyzer = ImpactAnalyzer()
    ranked = analyzer.analyze(findings)

    console.print(
        f"\n  [bold]Analyzer Summary:[/bold] "
        f"[bold]Total Risk Score: {analyzer.total_risk_score:.1f}[/bold] · "
        f"Top issue: [{ranked[0]['severity']}]{ranked[0]['pattern']}[/{ranked[0]['severity']}]"
    )

    # ═══════════════════════════════════════════════════════
    # STAGE 3: REFACTOR AGENT
    # ═══════════════════════════════════════════════════════
    refactorer = CodeRefactorer(str(target))
    refactor_result = refactorer.refactor(ranked)

    # Apply auto-fixes if requested
    if auto_fix:
        dry_run = False
        changed = refactorer.apply_auto_fixes(dry_run=dry_run)
        console.print(f"\n  [bold green]Auto-fixes applied:[/bold green] {len(changed)} files changed")
        for f in changed:
            console.print(f"    [dim]→ {f}[/dim]")
    else:
        console.print(
            "\n  [dim]💡 Auto-fix is in dry-run mode. "
            "Use --auto-fix to apply changes.[/dim]"
        )

    # ═══════════════════════════════════════════════════════
    # STAGE 4: VALIDATOR AGENT (Closed-Loop)
    # ═══════════════════════════════════════════════════════
    validator = ValidatorAgent(str(target))
    validation_result = validator.validate(refactor_result)

    console.print()
    console.print(validator.get_test_summary())

    # ═══════════════════════════════════════════════════════
    # FINAL REPORT
    # ═══════════════════════════════════════════════════════
    total_duration = time.time() - total_start

    console.print()
    report_table = display.summary_table(
        scanner.findings_by_severity(),
        ranked,
    )
    console.print(report_table)

    # Token usage estimate
    estimated_prompt = len(findings) * 500 + 2000
    estimated_completion = len(findings) * 200 + 1000
    display.token_usage(estimated_prompt, estimated_completion, 0.85)

    # Git operations
    if create_pr:
        git = GitOps(str(target))
        if git.is_repo():
            console.print("\n  [bold blue]📦 Creating refactoring PR...[/bold blue]")
            branch = git.create_refactor_branch()
            git.stage_all()
            git.commit("chore: CodeGuard auto-refactoring - fix technical debt")

            body = _build_pr_body(scanner, analyzer, refactorer, validator)
            pr_url = git.create_pr("🔧 Auto-refactoring by CodeGuard Agent", body)
            if pr_url:
                console.print(f"  [bold green]PR created:[/bold green] {pr_url}")
            else:
                console.print(
                    "  [yellow]PR not created. Push branch and create PR manually.[/yellow]"
                )
        else:
            console.print("  [yellow]Not a git repository. Skipping PR creation.[/yellow]")

    # Save JSON report
    if output == "json":
        report = _build_json_report(
            target, scanner, analyzer, refactorer, validator, total_duration
        )
        report_path = target / "codeguard-report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        console.print(f"\n  [dim]JSON report saved to: {report_path}[/dim]")

    display.done()


def _build_pr_body(scanner, analyzer, refactorer, validator) -> str:
    """Build a detailed PR description."""
    lines = [
        "## 🔧 CodeGuard Automated Refactoring",
        "",
        "This PR was automatically generated by **CodeGuard Agent** — "
        "an AI-powered code review and refactoring system.",
        "",
        "### Pipeline Summary",
        "",
        "```",
        "  Scanner → Analyzer → Refactor → Validator",
        "```",
        "",
        f"### Issues Found: {len(scanner.findings)}",
    ]

    sev = scanner.findings_by_severity()
    lines.append(f"- 🔴 Critical: {sev['critical']}")
    lines.append(f"- 🟡 High: {sev['high']}")
    lines.append(f"- 🟢 Medium: {sev['medium']}")
    lines.append(f"- ⚪ Low: {sev['low']}")

    lines.append("")
    lines.append(f"### Risk Score: {analyzer.total_risk_score:.1f}")
    lines.append(f"### Auto-Fixes Applied: {refactorer.auto_fixes_applied}")
    lines.append(f"### Manual Suggestions: {refactorer.manual_suggestions}")
    lines.append(f"### Validation: {'✅ Passed' if validator.validation_passed else '❌ Failed'}")
    lines.append("")
    lines.append("### 🤖 Agents Involved")
    lines.append("- **Scanner Agent v2.1** — Pattern matching + AST analysis")
    lines.append("- **Analyzer Agent v1.8** — Risk assessment + impact analysis")
    lines.append("- **Refactor Agent v2.3** — Auto-fix generation + manual suggestions")
    lines.append("- **Validator Agent v1.2** — Test execution + closed-loop verification")
    lines.append("")
    lines.append("---")
    lines.append("*Generated by [CodeGuard Agent](https://github.com/your/codeguard-agent)*")

    return "\n".join(lines)


def _build_json_report(
    target, scanner, analyzer, refactorer, validator, duration
) -> dict:
    """Build a structured JSON report."""
    return {
        "project": str(target),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "duration_seconds": round(duration, 2),
        "pipeline": {
            "scanner": {
                "findings": len(scanner.findings),
                "by_severity": scanner.findings_by_severity(),
            },
            "analyzer": {
                "risk_score": analyzer.total_risk_score,
                "top_issues": [
                    {
                        "pattern": f["pattern"],
                        "severity": f["severity"],
                        "file": f["file"],
                        "line": f["line"],
                        "risk_score": f.get("risk_score", 0),
                    }
                    for f in analyzer.get_top_issues(10)
                ],
            },
            "refactorer": {
                "auto_fixes": refactorer.auto_fixes_applied,
                "manual_suggestions": refactorer.manual_suggestions,
                "total": len(refactorer.refactor_suggestions),
            },
            "validator": {
                "passed": validator.validation_passed,
                "recommendation": validator._recommendation() if hasattr(validator, '_recommendation') else "",
            },
        },
        "findings": scanner.findings,
    }


def main():
    """Entry point for python -m codeguard."""
    cli()


if __name__ == "__main__":
    main()
