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
