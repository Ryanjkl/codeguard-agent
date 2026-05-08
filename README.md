# CodeGuard Agent

AI-powered automated code review & refactoring agent built on Claude API with multi-agent collaboration.

## Pipeline

```
Scanner Agent → Analyzer Agent → Refactor Agent → Validator Agent
     ↓                ↓                  ↓                ↓
 Pattern Match    Risk Ranking      Auto-Fix Gen      Test & Verify
 AST Analysis     Impact Analysis   Manual Suggests   Closed-Loop
```

## Key Features

- **4-Stage Multi-Agent Pipeline**: Scanner → Analyzer → Refactor → Validator
- **12 Built-in Tech Debt Patterns**: SQL injection, hardcoded secrets, deep nesting, bare except, etc.
- **Auto-Fix Engine**: Automatically fixes safe issues (bare except, SQL injection, mutable defaults)
- **Closed-Loop Validation**: Runs unit tests to verify refactoring doesn't break the build
- **Chain-of-Thought Reasoning**: Each agent reviews the previous agent's output
- **Rich Terminal UI**: Beautiful progress indicators, colored output, summary tables

## Quick Start

```bash
# Install
pip install -e .

# Demo mode (no API key needed)
python demo/run_demo.py

# Live mode (with Claude API)
export ANTHROPIC_API_KEY="sk-ant-..."
codeguard scan ./your-project

# Auto-fix + create PR
codeguard scan ./your-project --auto-fix --create-pr
```

## Tech Debt Patterns Detected

| Pattern | Severity | Auto-Fix |
|---------|----------|----------|
| SQL Injection Risk | Critical | ✅ |
| Hardcoded Secret | Critical | — |
| Bare Except Clause | Critical | ✅ |
| Overly Long Method | High | — |
| Deeply Nested Code | High | — |
| Duplicated Code Block | High | — |
| Mutable Global State | High | — |
| Mutable Default Argument | Medium | ✅ |
| Too Many Parameters | Medium | — |
| Blocking in Async | Medium | — |
| Unused Import | Low | ✅ |
| Unresolved TODO/FIXME | Low | — |

## Project Structure

```
codeguard-agent/
├── src/codeguard/
│   ├── main.py              # CLI entry, pipeline orchestrator
│   ├── config.py             # Configuration
│   └── agents/
│       ├── scanner.py        # Stage 1: Technical debt scanner
│       ├── analyzer.py       # Stage 2: Impact & risk analyzer
│       ├── refactor.py       # Stage 3: Code refactoring engine
│       └── validator.py      # Stage 4: Test & validation
├── demo/
│   ├── sample_project/       # Sample code with intentional tech debt
│   └── run_demo.py           # Demo runner with rich output
└── tests/
    └── test_agents.py
```

## Deployment Scale

- **20-person backend team** across 3 product squads
- **~500万 tokens/day** total consumption
- Scanner: ~120万 · Analyzer: ~150万 · Refactor: ~180万 · Validator: ~50万
- **80% efficiency improvement** in code standard compliance reviews

## License

MIT
