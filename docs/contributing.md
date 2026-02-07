# Contributing

Thank you for your interest in contributing to UTSS!

---

## Development Setup

### Clone the Repository

```bash
git clone https://github.com/obichan117/universal-trading-strategy-schema.git
cd universal-trading-strategy-schema
```

### Install Dependencies

```bash
uv sync
```

### Run Tests

```bash
uv run pytest
```

### Build Documentation

```bash
uv run mkdocs serve
```

---

## Project Structure

```
universal-trading-strategy-schema/
├── schema/v1/
│   ├── strategy.schema.json    # JSON Schema (SOURCE OF TRUTH)
│   └── backtest.schema.json    # Backtest config schema
├── packages/
│   ├── utss/                   # Schema package (pip install utss)
│   ├── pyutss/                 # Backtesting engine (pip install pyutss)
│   ├── utss-llm/               # LLM integration (pip install utss-llm)
│   └── utss-mcp/               # MCP server (pip install utss-mcp)
├── examples/                   # Example strategies
├── docs/                       # Documentation (MkDocs)
├── pyproject.toml              # Workspace root (uv workspaces)
└── mkdocs.yml                  # MkDocs configuration
```

---

## Making Changes

### Schema Changes

The JSON Schema is the **source of truth**. When making schema changes:

1. **Update JSON Schema first** (`schema/v1/strategy.schema.json`)
2. **Update Python models** (`packages/utss/src/utss/models.py`)
3. **Update capabilities** (`packages/utss/src/utss/capabilities.py`)
4. **Add/update examples** (`examples/`)
5. **Update documentation** (`docs/`)
6. **Run tests** (`uv run pytest`)

### Adding a New Signal Type

1. Add to JSON Schema under `definitions`:

```json
"NewSignal": {
  "type": "object",
  "required": ["type", "field"],
  "properties": {
    "type": { "const": "new_signal" },
    "field": { "type": "string" }
  }
}
```

2. Add to `Signal` oneOf in JSON Schema

3. Add Pydantic model:

```python
class NewSignal(BaseSchema):
    type: Literal["new_signal"]
    field: str
```

4. Add to `Signal` union type

5. Export from `__init__.py`

6. Add example usage in `docs/`

### Adding a New Indicator

1. Add computation function in the appropriate `engine/indicators/` category module
2. Add entry to `INDICATOR_REGISTRY` in `engine/indicators/dispatcher.py`
3. Add `@staticmethod` wrapper to `IndicatorService` in `engine/indicators/service.py`
4. Add to `SUPPORTED_INDICATORS` in `packages/utss/src/utss/capabilities.py`
5. Add tests and document in specification

---

## Code Style

### Python

- Use [Ruff](https://docs.astral.sh/ruff/) for formatting and linting
- Follow PEP 8
- Use type hints everywhere
- Keep lines under 100 characters

```bash
# Format code
uv run ruff format

# Check linting
uv run ruff check
```

### YAML Examples

- Use 2-space indentation
- Include comments explaining the strategy
- Follow existing example patterns

---

## Pull Request Process

1. **Fork** the repository
2. **Create a branch** for your feature (`git checkout -b feature/my-feature`)
3. **Make changes** following the guidelines above
4. **Run tests** (`uv run pytest`)
5. **Run linter** (`uv run ruff check`)
6. **Build docs** (`uv run mkdocs build --strict`)
7. **Commit** with a clear message
8. **Push** to your fork
9. **Open a Pull Request**

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new portfolio signal fields
fix: correct RSI indicator parameter validation
docs: update quickstart guide
chore: update dependencies
```

---

## Reporting Issues

### Bug Reports

Include:

- UTSS version (`python -c "import utss; print(utss.__version__)"`)
- Python version
- Minimal example to reproduce
- Expected vs actual behavior

### Feature Requests

Include:

- Use case description
- Example of how it would be used
- Any alternative approaches considered

---

## Questions?

- Open an issue on GitHub
- Check existing issues for similar questions
- Review the documentation

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
