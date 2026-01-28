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
cd python
uv sync --extra dev --extra docs
```

### Run Tests

```bash
uv run pytest
```

### Run Type Checker

```bash
uv run mypy utss --ignore-missing-imports
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
│   └── strategy.schema.json    # JSON Schema (SOURCE OF TRUTH)
├── python/utss/
│   ├── models.py               # Pydantic models
│   ├── validator.py            # Validation functions
│   └── __init__.py             # Public API
├── examples/                   # Example strategies
├── docs/                       # Documentation (MkDocs)
└── mkdocs.yml                  # MkDocs configuration
```

---

## Making Changes

### Schema Changes

The JSON Schema is the **source of truth**. When making schema changes:

1. **Update JSON Schema first** (`schema/v1/strategy.schema.json`)
2. **Update Python models** (`python/utss/models.py`)
3. **Add/update examples** (`examples/`)
4. **Update documentation** (`docs/`)
5. **Run tests** to ensure everything works

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

1. Add to `IndicatorType` enum in JSON Schema
2. Add to `IndicatorType` enum in `models.py`
3. Document in specification

---

## Code Style

### Python

- Use [Ruff](https://docs.astral.sh/ruff/) for formatting and linting
- Follow PEP 8
- Use type hints everywhere
- Keep lines under 100 characters

```bash
# Format code
uv run ruff format utss

# Check linting
uv run ruff check utss
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
5. **Run type checker** (`uv run mypy utss`)
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
