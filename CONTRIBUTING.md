# Contributing to Senthium AI

Thank you for your interest in contributing to Senthium AI! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Git
- (Optional) Webcam for testing face detection features

### Setting Up Development Environment

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/senthium-ai.git
   cd senthium-ai
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run tests to verify setup:
   ```bash
   python test_senthium.py
   ```

## Development Workflow

### Running the Application

Test your changes by running the application in dry-run mode:
```bash
python senthium_ai.py --dry-run --verbose
```

### Running Tests

Before submitting a pull request, ensure all tests pass:
```bash
python test_senthium.py
```

### Running the Demo

Test individual components with the demo:
```bash
python example_demo.py
```

## Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to classes and functions
- Keep functions focused and modular
- Add comments for complex logic

## Areas for Contribution

### High Priority
- Platform-specific lock implementations (Windows, macOS improvements)
- Additional process monitoring patterns
- Performance optimizations
- Documentation improvements

### Medium Priority
- Alternative ML models (e.g., using scikit-learn)
- Configuration UI
- Notification system
- Logging improvements

### Low Priority
- Additional face detection backends
- Mobile app integration
- Cloud sync features
- Advanced analytics

## Submitting Changes

1. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes
3. Test thoroughly
4. Commit with clear messages:
   ```bash
   git commit -m "Add feature: description of feature"
   ```
5. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
6. Create a pull request

## Pull Request Guidelines

- Provide a clear description of changes
- Reference any related issues
- Include test results
- Update documentation if needed
- Ensure no security vulnerabilities
- Keep changes focused (one feature per PR)

## Bug Reports

When reporting bugs, include:
- Operating system and version
- Python version
- Steps to reproduce
- Expected vs actual behavior
- Error messages and logs
- Configuration used

## Feature Requests

When requesting features:
- Describe the use case
- Explain why it's beneficial
- Provide examples if possible
- Consider implementation complexity

## Security

If you discover a security vulnerability:
- **Do not** open a public issue
- Email the maintainers directly
- Provide detailed information
- Allow time for patching before disclosure

## Code of Conduct

- Be respectful and professional
- Welcome newcomers
- Accept constructive criticism
- Focus on what's best for the project
- Show empathy towards others

## Questions?

- Open an issue for questions
- Join discussions
- Check existing issues and PRs

Thank you for contributing to Senthium AI!
