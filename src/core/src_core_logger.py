#!/usr/bin/env python3
"""
Logging Module - IoT Adversary Emulator
Système de logging centralisé avec niveaux et couleurs
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional


# Couleurs pour le terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class ColoredFormatter(logging.Formatter):
    """Formatter avec couleurs pour le terminal"""
    
    COLORS = {
        'DEBUG': Colors.OKCYAN,
        'INFO': Colors.OKGREEN,
        'WARNING': Colors.WARNING,
        'ERROR': Colors.FAIL,
        'CRITICAL': Colors.FAIL + Colors.BOLD,
    }
    
    def format(self, record):
        # Ajouter la couleur selon le niveau
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Colors.ENDC}"
        
        return super().format(record)


class LoggerManager:
    """Gestionnaire de loggers pour l'application"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.loggers = {}
            self.log_dir = None
            self.log_file = None
            self._initialized = True
    
    def setup(self, log_dir: Path, log_file: str = "app.log", level: str = "INFO"):
        """
        Configure le système de logging
        
        Args:
            log_dir: Dossier pour les logs
            log_file: Nom du fichier de log
            level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_file = self.log_dir / log_file
        
        # Niveau de log global
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        
        # Format des logs
        file_format = logging.Formatter(
            '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_format = ColoredFormatter(
            '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Handler fichier (avec rotation)
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(file_format)
        
        # Handler console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(console_format)
        
        # Logger racine
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Message de démarrage
        root_logger.info("=" * 60)
        root_logger.info("IoT Adversary Emulator - Logging System Initialized")
        root_logger.info(f"Log file: {self.log_file}")
        root_logger.info(f"Log level: {level}")
        root_logger.info("=" * 60)
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Obtient ou crée un logger pour un module
        
        Args:
            name: Nom du module (généralement __name__)
        
        Returns:
            Logger configuré
        """
        if name not in self.loggers:
            logger = logging.getLogger(name)
            self.loggers[name] = logger
        
        return self.loggers[name]


# Instance globale
_logger_manager = LoggerManager()


def setup_logging(log_dir: Path, log_file: str = "app.log", level: str = "INFO"):
    """Configure le système de logging de l'application"""
    _logger_manager.setup(log_dir, log_file, level)


def get_logger(name: str) -> logging.Logger:
    """Obtient un logger pour un module"""
    return _logger_manager.get_logger(name)


# Logger par défaut pour les tests
if __name__ == "__main__":
    # Test du système de logging
    setup_logging(Path("./logs"), level="DEBUG")
    
    logger = get_logger("test_module")
    
    logger.debug("Ceci est un message DEBUG")
    logger.info("Ceci est un message INFO")
    logger.warning("Ceci est un message WARNING")
    logger.error("Ceci est un message ERROR")
    logger.critical("Ceci est un message CRITICAL")
    
    print(f"\n✅ Logs écrits dans: {_logger_manager.log_file}")
