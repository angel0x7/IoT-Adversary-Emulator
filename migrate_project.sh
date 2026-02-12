#!/bin/bash
# Script de migration du projet IoT-Adversary-Emulator
# Réorganise la structure actuelle vers la nouvelle architecture

set -e  # Arrêter en cas d'erreur

echo "🚀 Migration du projet IoT-Adversary-Emulator"
echo "=============================================="
echo ""

# Couleurs pour les messages
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour créer un dossier avec message
create_dir() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        echo -e "${GREEN}✓${NC} Créé: $1"
    else
        echo -e "${YELLOW}⚠${NC} Existe déjà: $1"
    fi
}

# Fonction pour créer un fichier __init__.py
create_init() {
    if [ ! -f "$1/__init__.py" ]; then
        touch "$1/__init__.py"
        echo -e "${GREEN}✓${NC} Créé: $1/__init__.py"
    fi
}

echo -e "${BLUE}[1/10]${NC} Création de la structure de dossiers..."
echo ""

# Structure principale
create_dir "src"
create_dir "tests"
create_dir "docs"
create_dir "web"
create_dir "configs"
create_dir "data"
create_dir "scripts"
create_dir "lab"
create_dir "examples"

# Structure src/
create_dir "src/core"
create_dir "src/scanner"
create_dir "src/attacks"
create_dir "src/network"
create_dir "src/mqtt"
create_dir "src/ai"
create_dir "src/api"
create_dir "src/gui"
create_dir "src/database"
create_dir "src/utils"

# Structure tests/
create_dir "tests/integration"
create_dir "tests/unit"

# Structure web/
create_dir "web/static"
create_dir "web/static/css"
create_dir "web/static/js"
create_dir "web/static/js/components"
create_dir "web/static/assets"
create_dir "web/templates"

# Structure configs/
create_dir "configs/attacks"

# Structure data/
create_dir "data/vulnerabilities"
create_dir "data/signatures"
create_dir "data/logs"
create_dir "data/exports"

# Structure lab/
create_dir "lab/scenarios"

echo ""
echo -e "${BLUE}[2/10]${NC} Création des fichiers __init__.py..."
echo ""

# Tous les packages Python
create_init "src"
create_init "src/core"
create_init "src/scanner"
create_init "src/attacks"
create_init "src/network"
create_init "src/mqtt"
create_init "src/ai"
create_init "src/api"
create_init "src/gui"
create_init "src/database"
create_init "src/utils"
create_init "tests"

echo ""
echo -e "${BLUE}[3/10]${NC} Création des fichiers de configuration de base..."
echo ""

# .gitignore
if [ ! -f ".gitignore" ]; then
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
env/
venv/
.venv
ENV/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
*.log
logs/
data/logs/*
!data/logs/.gitkeep

# Database
*.db
*.sqlite3

# OS
.DS_Store
Thumbs.db

# Project specific
data/exports/*
!data/exports/.gitkeep
configs/local.yaml
*.pcap
EOF
    echo -e "${GREEN}✓${NC} Créé: .gitignore"
else
    echo -e "${YELLOW}⚠${NC} Existe déjà: .gitignore"
fi

# .gitkeep files
touch data/logs/.gitkeep
touch data/exports/.gitkeep
echo -e "${GREEN}✓${NC} Créé: fichiers .gitkeep"

# requirements.txt
if [ ! -f "requirements.txt" ]; then
    cat > requirements.txt << 'EOF'
# Core
paho-mqtt>=1.6.1
scapy>=2.5.0
python-nmap>=0.7.1

# Web Server
flask>=2.3.0
flask-cors>=4.0.0
flask-socketio>=5.3.0

# AI/ML (Phase 2+)
scikit-learn>=1.3.0
numpy>=1.24.0
pandas>=2.0.0

# Database
sqlalchemy>=2.0.0

# Utils
pyyaml>=6.0
requests>=2.31.0
colorama>=0.4.6
tqdm>=4.65.0

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
EOF
    echo -e "${GREEN}✓${NC} Créé: requirements.txt"
else
    echo -e "${YELLOW}⚠${NC} Existe déjà: requirements.txt"
fi

echo ""
echo -e "${BLUE}[4/10]${NC} Création de setup.py..."
echo ""

if [ ! -f "setup.py" ]; then
    cat > setup.py << 'EOF'
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="iot-adversary-emulator",
    version="0.1.0",
    author="angel0x7",
    author_email="your.email@example.com",
    description="AI-Powered IoT Security Testing & Vulnerability Analysis Platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/angel0x7/IoT-Adversary-Emulator",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "iot-emulator=src.main:main",
        ],
    },
)
EOF
    echo -e "${GREEN}✓${NC} Créé: setup.py"
else
    echo -e "${YELLOW}⚠${NC} Existe déjà: setup.py"
fi

echo ""
echo -e "${BLUE}[5/10]${NC} Création de README.md..."
echo ""

if [ ! -f "README.md" ]; then
    cat > README.md << 'EOF'
# 🔒 IoT Adversary Emulator

<div align="center">

**AI-Powered IoT Security Testing & Vulnerability Analysis Platform**

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

*Transform IoT security testing with autonomous AI agents*

[Features](#-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Roadmap](#-roadmap) • [Contributing](#-contributing)

</div>

---

## 🎯 Vision

IoT Adversary Emulator aims to become the **first fully autonomous AI-powered cybersecurity platform** capable of discovering, analyzing, and exploiting IoT vulnerabilities—including zero-day discoveries.

### Current Status: **Phase 0 - Foundations** 🏗️

We're building the foundation for an intelligent security testing platform. Check our [roadmap](docs/roadmap.md) to see where we're headed!

---

## ✨ Features

### Current (v0.1.0)
- 🌐 **Network Discovery** - Automated scanning and device identification
- 🎯 **Multiple Attack Vectors** - MITM, Injection, Flood, Deauth
- 📡 **MQTT Protocol Support** - Specialized IoT protocol testing
- 💻 **Web Interface** - Real-time monitoring and control
- 📊 **Statistics & Logging** - Comprehensive attack analytics

### Coming Soon (Phase 1)
- 🤖 **AI-Powered Analysis** - ML-based anomaly detection
- 🔍 **Vulnerability Scanner** - Automated CVE matching
- 📈 **Smart Recommendations** - AI suggests optimal attack strategies
- 🧪 **Docker Lab Environment** - Reproducible testing scenarios

### Future (Phase 2-4)
- 🖥️ **Desktop Application** - Native app for Windows, macOS, Linux
- 🧠 **Advanced AI Agent** - Autonomous penetration testing
- 🎨 **3D Network Visualization** - Immersive topology views
- 🌍 **Complex Network Simulation** - Realistic enterprise environments
- 🔓 **Zero-Day Discovery** - AI-driven vulnerability hunting

---

## 🚀 Installation

### Prerequisites
- Python 3.9 or higher
- Root/Administrator privileges (for network operations)
- Linux recommended (Ubuntu 20.04+, Kali Linux)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/angel0x7/IoT-Adversary-Emulator.git
cd IoT-Adversary-Emulator

# Install dependencies
pip install -r requirements.txt

# Install system packages (Linux)
sudo apt-get update
sudo apt-get install -y nmap dsniff

# Run the setup
python setup.py install
```

### For detailed installation instructions, see [Installation Guide](docs/installation.md)

---

## 🎮 Quick Start

### 1. Start the Server
```bash
sudo python src/main.py
```

### 2. Open the Web Interface
Navigate to `http://localhost:8080` in your browser

### 3. Scan Your Network
Click "Scan Network" to discover IoT devices

### 4. Launch an Attack
1. Select an attack type (MITM recommended)
2. Choose a target device
3. Configure parameters
4. Click "Launch Attack"

### 5. Monitor Results
Watch real-time statistics and logs in the dashboard

---

## 📚 Documentation

- [**Quick Start Guide**](docs/quick-start.md) - Get up and running in 5 minutes
- [**Architecture**](docs/architecture.md) - System design and components
- [**Attack Techniques**](docs/attack-techniques.md) - Detailed attack explanations
- [**API Reference**](docs/api-reference.md) - REST API documentation
- [**Contributing Guide**](CONTRIBUTING.md) - How to contribute to the project

---

## 🗺️ Roadmap

We have an ambitious multi-year plan to build the ultimate AI cyber platform.

### Phase 0: Foundations (Weeks 1-8) - Current ✅
- Modular architecture
- Core attack capabilities
- Professional codebase

### Phase 1: Basic AI (Weeks 9-20) - Q1-Q2 2025
- ML-based anomaly detection
- Smart attack recommendations
- Vulnerability prediction

### Phase 2: Desktop App (Weeks 21-32) - Q2-Q3 2025
- Cross-platform native application
- Advanced UI with 3D visualization
- Professional reporting

### Phase 3: Advanced AI (Weeks 33-52) - Q3-Q4 2025
- Deep learning models
- Autonomous agent prototype
- Zero-day hunting capabilities

### Phase 4+: AI Cyber Platform (2026-2029)
- Fully autonomous AI agent
- Complex network simulation
- Enterprise-grade platform

[**Full Roadmap**](docs/roadmap.md) with weekly objectives and milestones.

---

## 🤝 Contributing

We welcome contributions from the community! Whether it's:

- 🐛 Bug reports and fixes
- ✨ New features and attack techniques
- 📖 Documentation improvements
- 🧪 Test coverage
- 💡 Ideas and suggestions

Please read our [Contributing Guide](CONTRIBUTING.md) to get started.

---

## ⚖️ Legal & Ethical Use

**⚠️ IMPORTANT DISCLAIMER**

This tool is designed for **authorized security testing only**. Misuse of this software for attacking systems without explicit permission is **illegal** and **unethical**.

### Acceptable Use
✅ Authorized penetration testing  
✅ Security research in controlled environments  
✅ Educational purposes in isolated labs  
✅ IoT security auditing with permission  

### Prohibited Use
❌ Attacking systems without authorization  
❌ Disrupting production networks  
❌ Illegal hacking activities  
❌ Violating terms of service  

**Users are solely responsible for complying with applicable laws and regulations.**

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- The amazing open-source security community
- Contributors and testers
- Researchers advancing IoT security

---

## 📞 Contact & Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/angel0x7/IoT-Adversary-Emulator/issues)
- **Discussions**: [Join the conversation](https://github.com/angel0x7/IoT-Adversary-Emulator/discussions)
- **Email**: your.email@example.com

---

<div align="center">

**⭐ Star this repo if you find it useful!**

*Building the future of autonomous IoT security testing* 🚀

</div>
EOF
    echo -e "${GREEN}✓${NC} Créé: README.md"
else
    echo -e "${YELLOW}⚠${NC} Existe déjà: README.md (renommé en README.old.md)"
    mv README.md README.old.md
fi

echo ""
echo -e "${BLUE}[6/10]${NC} Création de CONTRIBUTING.md..."
echo ""

if [ ! -f "CONTRIBUTING.md" ]; then
    cat > CONTRIBUTING.md << 'EOF'
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
EOF
    echo -e "${GREEN}✓${NC} Créé: CONTRIBUTING.md"
else
    echo -e "${YELLOW}⚠${NC} Existe déjà: CONTRIBUTING.md"
fi

echo ""
echo -e "${BLUE}[7/10]${NC} Création de LICENSE (MIT)..."
echo ""

if [ ! -f "LICENSE" ]; then
    cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2025 angel0x7

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
    echo -e "${GREEN}✓${NC} Créé: LICENSE"
else
    echo -e "${YELLOW}⚠${NC} Existe déjà: LICENSE"
fi

echo ""
echo -e "${BLUE}[8/10]${NC} Création de pytest.ini..."
echo ""

if [ ! -f "pytest.ini" ]; then
    cat > pytest.ini << 'EOF'
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --cov=src
    --cov-report=html
    --cov-report=term-missing
EOF
    echo -e "${GREEN}✓${NC} Créé: pytest.ini"
else
    echo -e "${YELLOW}⚠${NC} Existe déjà: pytest.ini"
fi

echo ""
echo -e "${BLUE}[9/10]${NC} Création de la configuration par défaut..."
echo ""

if [ ! -f "configs/default.yaml" ]; then
    cat > configs/default.yaml << 'EOF'
# Configuration par défaut - IoT Adversary Emulator

network:
  interface: "eth0"
  range: "192.168.10.0/24"
  
server:
  host: "0.0.0.0"
  port: 8080
  debug: false
  
mqtt:
  default_port: 1883
  timeout: 10
  qos: 0
  
attacks:
  mitm:
    enabled: true
    default_interval: 5
  injection:
    enabled: true
    default_interval: 5
  flood:
    enabled: true
    rate: 0.1
  deauth:
    enabled: false  # WiFi only
    
logging:
  level: "INFO"
  file: "data/logs/app.log"
  max_size_mb: 10
  backup_count: 5
  
database:
  type: "sqlite"
  path: "data/emulator.db"
EOF
    echo -e "${GREEN}✓${NC} Créé: configs/default.yaml"
else
    echo -e "${YELLOW}⚠${NC} Existe déjà: configs/default.yaml"
fi

echo ""
echo -e "${BLUE}[10/10]${NC} Création des fichiers de documentation..."
echo ""

# docs/installation.md
if [ ! -f "docs/installation.md" ]; then
    cat > docs/installation.md << 'EOF'
# Installation Guide

Detailed installation instructions for IoT Adversary Emulator.

## Prerequisites
- Python 3.9+
- Root/sudo access
- Linux (Ubuntu/Kali) or macOS

## Step-by-Step Installation

### 1. Clone Repository
```bash
git clone https://github.com/angel0x7/IoT-Adversary-Emulator.git
cd IoT-Adversary-Emulator
```

### 2. System Dependencies
**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y nmap dsniff python3-dev
```

**macOS:**
```bash
brew install nmap
```

### 3. Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify Installation
```bash
python -c "import src; print('Success!')"
```

## Troubleshooting

### Permission Denied
Run with sudo: `sudo python src/main.py`

### Import Errors
Ensure all dependencies are installed: `pip install -r requirements.txt`

### Network Issues
Check your interface name: `ip addr` or `ifconfig`
EOF
    echo -e "${GREEN}✓${NC} Créé: docs/installation.md"
fi

echo ""
echo "=============================================="
echo -e "${GREEN}✅ Migration terminée avec succès!${NC}"
echo "=============================================="
echo ""
echo "📁 Structure créée:"
echo "   - src/ (modules Python)"
echo "   - tests/ (tests unitaires)"
echo "   - docs/ (documentation)"
echo "   - web/ (interface web)"
echo "   - configs/ (configurations)"
echo "   - data/ (données et logs)"
echo ""
echo "📄 Fichiers créés:"
echo "   - README.md (documentation principale)"
echo "   - requirements.txt (dépendances)"
echo "   - setup.py (package)"
echo "   - LICENSE (MIT)"
echo "   - CONTRIBUTING.md (guide de contribution)"
echo ""
echo "🔜 Prochaines étapes:"
echo "   1. Migrer votre code dans src/"
echo "   2. Découper complete_attack_system_fixed.py"
echo "   3. Créer des tests dans tests/"
echo "   4. Installer: pip install -e ."
echo ""
echo "📖 Voir PROJECT_STRUCTURE.md et ROADMAP.md pour la suite!"
echo ""
