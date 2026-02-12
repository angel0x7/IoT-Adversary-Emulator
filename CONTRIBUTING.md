# Contributing to IoT Adversary Emulator

Thank you for considering contributing to IoT Adversary Emulator! 🎉

## How to Contribute

### Reporting Bugs
- Use GitHub Issues
- Include detailed steps to reproduce
- Provide system information (OS, Python version)
- Attach logs if relevant

### Suggesting Features
- Open a GitHub Discussion first
- Explain the use case
- Discuss implementation approach
- Get community feedback

### Code Contributions

#### 1. Fork the Repository
```bash
git clone https://github.com/YOUR_USERNAME/IoT-Adversary-Emulator.git
cd IoT-Adversary-Emulator
```

#### 2. Create a Branch
```bash
git checkout -b feature/your-feature-name
```

#### 3. Make Your Changes
- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation
- Run tests before committing

#### 4. Commit Your Changes
```bash
git add .
git commit -m "feat: Add awesome new feature"
```

Use conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring

#### 5. Push and Create PR
```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Development Setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Check code style
black src/
pylint src/

# Run specific tests
pytest tests/test_scanner.py -v
```

## Code Standards

- **Python 3.9+** required
- **PEP 8** compliant
- **Type hints** where applicable
- **Docstrings** for all public functions
- **Unit tests** for new code

## Questions?

Feel free to ask in GitHub Discussions or Issues!
