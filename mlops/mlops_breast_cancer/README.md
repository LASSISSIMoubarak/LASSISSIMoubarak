# Simple project example

A minimal Python project showing best practices.

- `src/` layout
- virtual environment
- tests

## Development Installation

1. **Create and activate a virtual environment**:

```bash
# Create the virtual environment
python -m venv .venv

# Activate it:
# macOS/Linux
source .venv/bin/activate
# Windows
.\.venv\Scripts\activate
```

2. **Install the project in editable mode**:

```bash
pip install -e .
```

3. **Install testing dependencies** (if not already in requirements.txt):

```bash
pip install pytest
```

## Run Commands

* **Run tests**:

```bash
pytest
```

* **Use the package in Python**:

```python
from mlops_breast_cancer.utils import mean

res = mean([1, 3, 5])
print(res)
```

## Project Structure

```
mlops_breast_cancer/
│
├── src/
│   └── mlops_breast_cancer/
│       ├── __init__.py
│       └── utils.py
│
├── tests/
│   └── test_utils.py
│
├── pyproject.toml
├── README.md
└── requirements.txt
```

## Resources

* [Python Official Docs](https://python.org)
* [Real Python Tutorials](https://realpython.com)
* [Pytest Documentation](https://docs.pytest.org)
* [Python Packaging User Guide](https://packaging.python.org/)
