# Contributing to Senthium AI

First off, **thank you** for considering contributing to Senthium AI! 💜

It's people like you that make Senthium AI a great tool for privacy-conscious developers and creators.

## 🌟 Ways to Contribute

### 1. Report Bugs 🐛
Found a bug? Help us fix it!
- Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md)
- Include: OS, Python version, error messages, steps to reproduce
- Check if it's already reported in [Issues](../../issues)

### 2. Suggest Features 💡
Have an idea? We'd love to hear it!
- Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md)
- Explain the problem it solves
- Describe your proposed solution

### 3. Improve Documentation 📚
- Fix typos, clarify explanations
- Add examples, tutorials, or guides
- Translate docs to other languages

### 4. Write Code 💻
- Fix bugs, add features, optimize performance
- Follow our code style (see below)
- Add tests for your changes

### 5. Help Others 🤝
- Answer questions in [Discussions](../../discussions)
- Review pull requests
- Share your use cases and setups

---

## 🚀 Getting Started

### Development Setup

1. **Fork the repository**
   ```bash
   # Click "Fork" button on GitHub
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/senthium-ai.git
   cd senthium-ai
   ```

3. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install -e .[dev]  # Installs dev tools (pytest, black, etc.)
   ```

5. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

6. **Make your changes** 🎨
   - Write code
   - Add tests
   - Update docs

7. **Run tests**
   ```bash
   pytest tests/
   ```

8. **Check code style**
   ```bash
   black src/ tests/
   flake8 src/ tests/
   mypy src/
   ```

9. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add awesome feature"
   # or
   git commit -m "fix: resolve camera initialization bug"
   ```

10. **Push to your fork**
    ```bash
    git push origin feature/your-feature-name
    ```

11. **Create Pull Request**
    - Go to your fork on GitHub
    - Click "New Pull Request"
    - Fill out the PR template
    - Wait for review!

---

## 📝 Code Style Guide

### Python Style
We follow **PEP 8** with some tweaks:

```python
# ✅ Good
def recognize_face(image: np.ndarray, tolerance: float = 0.6) -> Optional[str]:
    """
    Recognize a face in the given image.
    
    Args:
        image: RGB image array (H x W x 3)
        tolerance: Distance threshold for matching (default: 0.6)
    
    Returns:
        Name of recognized person or None if unknown
    """
    # Implementation here
    pass

# ❌ Bad
def recognize_face(image,tolerance=0.6):
    # No type hints, no docstring
    pass
```

### Key Rules
- **Type hints** everywhere (use `mypy` to check)
- **Docstrings** for all public functions/classes
- **Line length**: 100 characters max (not 80!)
- **Imports**: Standard library → Third party → Local
- **Naming**:
  - `snake_case` for functions/variables
  - `PascalCase` for classes
  - `UPPER_CASE` for constants

### Formatting
We use **Black** (automatic formatting):
```bash
black src/ tests/
```

### Linting
We use **Flake8** (style checker):
```bash
flake8 src/ tests/
```

---

## 🧪 Testing Guidelines

### Writing Tests
- Put tests in `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use descriptive names: `test_face_recognition_returns_none_for_unknown_face`

### Test Structure
```python
import pytest
from src.vision.recognizer import FaceRecognizer

class TestFaceRecognizer:
    def test_recognize_known_face(self):
        # Arrange
        recognizer = FaceRecognizer(tolerance=0.6)
        known_image = load_test_image("john.jpg")
        
        # Act
        result = recognizer.recognize(known_image)
        
        # Assert
        assert result == "john"
    
    def test_recognize_unknown_face(self):
        # Arrange
        recognizer = FaceRecognizer(tolerance=0.6)
        unknown_image = load_test_image("stranger.jpg")
        
        # Act
        result = recognizer.recognize(unknown_image)
        
        # Assert
        assert result is None
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_recognizer.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_recognizer.py::TestFaceRecognizer::test_recognize_known_face
```

---

## 📋 Commit Message Convention

We use **Conventional Commits**:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, CI, etc.)
- `perf`: Performance improvements

### Examples
```bash
# Feature
git commit -m "feat(recognition): add liveness detection"

# Bug fix
git commit -m "fix(camera): handle camera not found error gracefully"

# Documentation
git commit -m "docs(readme): add installation instructions for macOS"

# Breaking change
git commit -m "feat(api): change face encoding format

BREAKING CHANGE: Face encodings now use 512-dim vectors instead of 128-dim"
```

---

## 🔀 Pull Request Process

1. **Update documentation** if you changed functionality
2. **Add tests** for new features or bug fixes
3. **Update CHANGELOG.md** with your changes
4. **Ensure CI passes** (tests, linting, type checking)
5. **Get approval** from at least one maintainer
6. **Squash commits** if requested (we'll help!)

### PR Checklist
Before submitting, make sure:
- [ ] Code follows style guide
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No merge conflicts
- [ ] Descriptive PR title
- [ ] Linked to related issue (if any)

---

## 🏆 Recognition

Contributors will be:
- Listed in `README.md` (Contributors section)
- Mentioned in release notes
- Given credit in `CHANGELOG.md`

Top contributors may be invited to become **maintainers**!

---

## 🤔 Questions?

- **General questions**: [Discussions](../../discussions)
- **Bug reports**: [Issues](../../issues)
- **Security issues**: See [SECURITY.md](SECURITY.md)
- **Direct contact**: shivadeepak.dev@gmail.com

---

## 📜 Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).

By participating, you agree to uphold this code. Please report unacceptable behavior to shivadeepak.dev@gmail.com.

---

## 💜 Thank You!

Your contributions make Senthium AI better for everyone. We appreciate your time and effort!

**Happy coding!** 🚀

---

**License**: By contributing, you agree that your contributions will be licensed under the MIT License.
