# 🛠️ Senthium Development Guide

This guide explains how to set up your development environment and contribute to Senthium.

---

## 🏗️ Development Setup

### 1. Fork & Clone
```bash
git clone https://github.com/yourusername/senthium.git
cd senthium
```

### 2. Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\Activate.ps1  # Windows PowerShell
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
pip install -e ".[dev]"
```

---

## 🧪 Testing

### Run Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/test_monitor.py

# Specific test
pytest tests/test_monitor.py::TestSystemMonitor::test_cpu_percent_in_valid_range
```

### Writing Tests
- Place tests in `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Aim for > 80% coverage

---

## 🎨 Code Style

### Formatting
```bash
# Format code with black
black src/ tests/

# Check with flake8
flake8 src/ tests/
```

### Type Checking
```bash
mypy src/
```

---

## 📝 Commit Guidelines

Use conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring

Example:
```bash
git commit -m "feat: add CPU usage monitoring"
git commit -m "fix: handle psutil exception in monitor"
git commit -m "docs: update README with v0.1 usage"
```

---

## 🚀 Release Process

(Will be defined for v1.0)

---

## 🐛 Debugging

### Enable Debug Logging
```python
from utils.logger import setup_logger
logger = setup_logger('senthium', level='DEBUG')
```

### Common Issues
- **Import errors**: Make sure venv is activated
- **Test failures**: Run `pip install -e .` to reinstall
- **Permission errors**: Don't run as admin/root

---

## 📞 Getting Help

- Check existing issues on GitHub
- Read the documentation
- Ask in discussions

---

Happy coding! 💕
