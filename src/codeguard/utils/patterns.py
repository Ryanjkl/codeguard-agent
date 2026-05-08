"""Technical debt detection patterns and rules.

Each pattern defines a common code smell with severity, category, and auto-fix capability.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Category(Enum):
    COMPLEXITY = "complexity"
    DUPLICATION = "duplication"
    ERROR_HANDLING = "error_handling"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    NAMING = "naming"
    ARCHITECTURE = "architecture"


@dataclass
class TechDebtPattern:
    """A single technical debt pattern to detect."""

    id: str
    name: str
    description: str
    category: Category
    severity: Severity
    regex_pattern: Optional[str] = None
    ast_check: Optional[str] = None
    auto_fixable: bool = False
    suggestion: str = ""


# Registered patterns
PATTERNS: list[TechDebtPattern] = [
    TechDebtPattern(
        id="LONG_METHOD",
        name="Overly Long Method",
        description="Method exceeds recommended line count threshold",
        category=Category.COMPLEXITY,
        severity=Severity.HIGH,
        ast_check="function_length > threshold",
        auto_fixable=False,
        suggestion="Break into smaller methods following SRP. Extract logical blocks into private helpers.",
    ),
    TechDebtPattern(
        id="DEEP_NESTING",
        name="Deeply Nested Code",
        description="Code block exceeds maximum nesting depth",
        category=Category.COMPLEXITY,
        severity=Severity.HIGH,
        ast_check="nesting_depth > threshold",
        auto_fixable=False,
        suggestion="Use guard clauses (early returns) to flatten nesting. Extract nested logic into separate functions.",
    ),
    TechDebtPattern(
        id="BARE_EXCEPT",
        name="Bare Except Clause",
        description="Using bare 'except:' without specifying exception types",
        category=Category.ERROR_HANDLING,
        severity=Severity.CRITICAL,
        regex_pattern=r"except\s*:",
        auto_fixable=True,
        suggestion="Catch specific exceptions: except (ValueError, KeyError) as e:",
    ),
    TechDebtPattern(
        id="HARDCODED_SECRET",
        name="Hardcoded Secret",
        description="Password, API key, or token appears to be hardcoded",
        category=Category.SECURITY,
        severity=Severity.CRITICAL,
        regex_pattern=r"(password|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]",
        auto_fixable=False,
        suggestion="Use environment variables or a secrets manager. Store in .env file (not committed).",
    ),
    TechDebtPattern(
        id="SQL_INJECTION",
        name="SQL Injection Risk",
        description="String formatting in SQL queries instead of parameterized queries",
        category=Category.SECURITY,
        severity=Severity.CRITICAL,
        regex_pattern=r"(execute|cursor\.execute)\s*\(\s*f['\"]",
        auto_fixable=True,
        suggestion="Use parameterized queries with placeholders: cursor.execute('SELECT ...', (param,))",
    ),
    TechDebtPattern(
        id="UNUSED_IMPORT",
        name="Unused Import",
        description="Imported module that is never referenced",
        category=Category.MAINTAINABILITY,
        severity=Severity.LOW,
        ast_check="unused_imports",
        auto_fixable=True,
        suggestion="Remove unused imports to keep dependencies clean.",
    ),
    TechDebtPattern(
        id="MUTABLE_DEFAULT",
        name="Mutable Default Argument",
        description="Function uses mutable object (list, dict) as default parameter",
        category=Category.MAINTAINABILITY,
        severity=Severity.MEDIUM,
        ast_check="mutable_default_arg",
        auto_fixable=True,
        suggestion="Use None as default and initialize inside function: def f(x=None): x = x or []",
    ),
    TechDebtPattern(
        id="TODO_FIXME",
        name="Unresolved TODO/FIXME",
        description="Code contains TODO or FIXME comments that may indicate incomplete work",
        category=Category.MAINTAINABILITY,
        severity=Severity.LOW,
        regex_pattern=r"#\s*(TODO|FIXME|HACK|XXX)",
        auto_fixable=False,
        suggestion="Review and either complete the task or create a ticket.",
    ),
    TechDebtPattern(
        id="DUPLICATE_BLOCK",
        name="Duplicated Code Block",
        description="Similar code blocks appear in multiple locations",
        category=Category.DUPLICATION,
        severity=Severity.HIGH,
        ast_check="duplicate_blocks",
        auto_fixable=False,
        suggestion="Extract common logic into a shared utility function or base class.",
    ),
    TechDebtPattern(
        id="TOO_MANY_PARAMS",
        name="Too Many Parameters",
        description="Function accepts more parameters than the recommended maximum",
        category=Category.COMPLEXITY,
        severity=Severity.MEDIUM,
        ast_check="param_count > threshold",
        auto_fixable=False,
        suggestion="Group related parameters into a dataclass or TypedDict. Consider builder pattern.",
    ),
    TechDebtPattern(
        id="GLOBAL_STATE",
        name="Mutable Global State",
        description="Module-level mutable variable that can cause side effects",
        category=Category.ARCHITECTURE,
        severity=Severity.HIGH,
        ast_check="global_mutable_state",
        auto_fixable=False,
        suggestion="Encapsulate state in a class. Use dependency injection. Consider immutable design.",
    ),
    TechDebtPattern(
        id="SYNC_IN_ASYNC",
        name="Blocking Call in Async Context",
        description="Synchronous blocking call inside an async function",
        category=Category.PERFORMANCE,
        severity=Severity.MEDIUM,
        ast_check="sync_in_async",
        auto_fixable=False,
        suggestion="Use async equivalents (aiofiles, httpx.AsyncClient) or run in thread executor.",
    ),
]

# Lookup by ID
PATTERN_MAP: dict[str, TechDebtPattern] = {p.id: p for p in PATTERNS}


def get_patterns_by_category(category: Category) -> list[TechDebtPattern]:
    return [p for p in PATTERNS if p.category == category]


def get_patterns_by_severity(severity: Severity) -> list[TechDebtPattern]:
    return [p for p in PATTERNS if p.severity == severity]
