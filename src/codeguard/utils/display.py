"""Rich terminal display utilities for CodeGuard Agent.

Uses ASCII-safe characters for Windows compatibility.
"""

import time
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box

console = Console()


class AgentDisplay:
    """Handles all rich terminal output formatting."""

    STYLE_AGENT = "bold cyan"
    STYLE_SUCCESS = "bold green"
    STYLE_WARNING = "bold yellow"
    STYLE_ERROR = "bold red"
    STYLE_INFO = "bold blue"
    STYLE_CODE = "dim white"

    @staticmethod
    def banner():
        console.print()
        console.print(
            Panel.fit(
                "[bold cyan]+======================================================+\n"
                "|   [bold white]CodeGuard[/bold white] - AI Code Review & Refactoring Agent  |\n"
                "|   Powered by Claude API / Multi-Agent Pipeline      |\n"
                "+======================================================+[/bold cyan]",
                border_style="cyan",
            )
        )
        console.print()

    @staticmethod
    def agent_start(name: str, description: str):
        console.print(f"\n  [bold cyan]>[/bold cyan] [{AgentDisplay.STYLE_AGENT}]{name}[/{AgentDisplay.STYLE_AGENT}] {description}")
        console.print(f"  [dim]{'-' * 60}[/dim]")

    @staticmethod
    def agent_result(name: str, findings: int, duration: float):
        console.print(
            f"  [bold green][OK][/bold green] [{AgentDisplay.STYLE_SUCCESS}]{name}[/{AgentDisplay.STYLE_SUCCESS}] "
            f"completed -- [yellow]{findings} findings[/yellow] -- [dim]{duration:.2f}s[/dim]"
        )

    @staticmethod
    def finding(pattern_name: str, severity: str, file: str, line: int, description: str):
        severity_color = {
            "critical": "bold red",
            "high": "bold yellow",
            "medium": "yellow",
            "low": "dim",
        }.get(severity, "white")

        console.print(
            f"    [{severity_color}]* {severity.upper()}[/{severity_color}] "
            f"[bold]{pattern_name}[/bold] "
            f"[dim]in {file}:{line}[/dim]"
        )
        if description:
            console.print(f"      [dim]-> {description}[/dim]")

    @staticmethod
    def refactor_diff(file: str, original: str, suggested: str):
        console.print()
        console.print(f"  [bold blue][FILE] {file}[/bold blue]")
        console.print(f"  [red]--- original[/red]")
        for line in original.strip().split("\n")[:5]:
            console.print(f"  [red]  - {line}[/red]")
        console.print(f"  [green]+++ suggested[/green]")
        for line in suggested.strip().split("\n")[:5]:
            console.print(f"  [green]  + {line}[/green]")
        console.print()

    @staticmethod
    def pipeline_progress():
        """Create a rich progress tracker for the agent pipeline."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        )

    @staticmethod
    def summary_table(findings_by_severity: dict, patterns_found: list) -> Table:
        table = Table(title="CodeGuard Analysis Report", box=box.ROUNDED, border_style="cyan")
        table.add_column("Severity", style="bold", width=12)
        table.add_column("Pattern", style="cyan", width=28)
        table.add_column("File", style="dim", width=30)
        table.add_column("Line", justify="right", width=6)
        table.add_column("Auto-Fix", justify="center", width=10)

        for finding in patterns_found:
            sev_color = {
                "critical": "bold red",
                "high": "bold yellow",
                "medium": "yellow",
                "low": "dim",
            }.get(finding.get("severity", "low"), "white")

            table.add_row(
                f"[{sev_color}]{finding.get('severity', '').upper()}[/{sev_color}]",
                finding.get("pattern", ""),
                finding.get("file", ""),
                str(finding.get("line", "-")),
                "[Y]" if finding.get("auto_fixable") else "-",
            )

        # Summary row
        total = sum(findings_by_severity.values())
        table.add_row("", "", "", "", "")
        table.add_row(
            f"[bold]TOTAL: {total}[/bold]",
            f"[red]{findings_by_severity.get('critical', 0)} critical[/red]  "
            f"[yellow]{findings_by_severity.get('high', 0)} high[/yellow]  "
            f"{findings_by_severity.get('medium', 0)} medium",
            "",
            "",
            "",
        )

        return table

    @staticmethod
    def token_usage(prompt_tokens: int, completion_tokens: int, total_cost: float):
        console.print()
        console.print(
            Panel(
                f"[dim]Token Usage:[/dim] {prompt_tokens:,} prompt + {completion_tokens:,} completion "
                f"= [bold]{prompt_tokens + completion_tokens:,} total[/bold]\n"
                f"[dim]Estimated Cost:[/dim] [bold]${total_cost:.4f}[/bold]",
                title="[COST] API Cost",
                border_style="dim",
                width=50,
            )
        )

    @staticmethod
    def done():
        console.print()
        console.print("  [bold green][DONE][/bold green] [bold]CodeGuard analysis complete![/bold]")
        console.print()


display = AgentDisplay()
