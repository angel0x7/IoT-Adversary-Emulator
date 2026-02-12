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
