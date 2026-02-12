#!/usr/bin/env python3
"""
Configuration Module - IoT Adversary Emulator
Gère la configuration globale avec détection automatique du réseau
"""

import os
import re
import subprocess
import socket
from typing import Optional, Dict
from pathlib import Path


class NetworkConfig:
    """Détection automatique de la configuration réseau"""
    
    def __init__(self):
        self.interface: Optional[str] = None
        self.local_ip: Optional[str] = None
        self.network_range: Optional[str] = None
        self.gateway: Optional[str] = None
        
    def detect_interface(self) -> str:
        """
        Détecte automatiquement l'interface réseau active
        Priorité : eth0 > enp* > wlan0 > wlp*
        """
        try:
            # Lister toutes les interfaces
            result = subprocess.run(
                ["ip", "-o", "-4", "addr", "show"],
                capture_output=True, text=True, check=True
            )
            
            interfaces = []
            for line in result.stdout.split('\n'):
                if not line:
                    continue
                    
                # Format: 2: eth0    inet 192.168.1.10/24 ...
                parts = line.split()
                if len(parts) >= 4:
                    iface = parts[1].rstrip(':')
                    ip = parts[3].split('/')[0]
                    
                    # Ignorer loopback
                    if iface == 'lo' or ip.startswith('127.'):
                        continue
                    
                    interfaces.append({
                        'name': iface,
                        'ip': ip,
                        'priority': self._get_interface_priority(iface)
                    })
            
            if not interfaces:
                raise Exception("No active network interface found")
            
            # Trier par priorité
            interfaces.sort(key=lambda x: x['priority'])
            
            best_interface = interfaces[0]
            self.interface = best_interface['name']
            self.local_ip = best_interface['ip']
            
            print(f"[CONFIG] Auto-detected interface: {self.interface}")
            print(f"[CONFIG] Local IP: {self.local_ip}")
            
            return self.interface
            
        except Exception as e:
            print(f"[ERROR] Failed to detect interface: {e}")
            # Fallback
            self.interface = "eth0"
            return self.interface
    
    def _get_interface_priority(self, iface: str) -> int:
        """
        Détermine la priorité d'une interface
        Plus le nombre est petit, plus la priorité est haute
        """
        if iface.startswith('eth'):
            return 1  # Ethernet câblé = priorité maximale
        elif iface.startswith('enp'):
            return 2  # Ethernet PCI
        elif iface.startswith('wlan'):
            return 3  # WiFi
        elif iface.startswith('wlp'):
            return 4  # WiFi PCI
        else:
            return 10  # Autres
    
    def detect_network_range(self) -> str:
        """
        Calcule automatiquement le range réseau à partir de l'IP locale
        Exemple: 192.168.10.5/24 → 192.168.10.0/24
        """
        if not self.local_ip:
            self.detect_interface()
        
        try:
            # Récupérer le masque de sous-réseau
            result = subprocess.run(
                ["ip", "-o", "-4", "addr", "show", self.interface],
                capture_output=True, text=True, check=True
            )
            
            # Format: inet 192.168.10.5/24
            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)', result.stdout)
            if match:
                ip = match.group(1)
                cidr = match.group(2)
                
                # Calculer l'adresse réseau
                ip_parts = [int(x) for x in ip.split('.')]
                mask_bits = int(cidr)
                
                # Créer le masque
                mask = (0xffffffff >> (32 - mask_bits)) << (32 - mask_bits)
                
                # Appliquer le masque
                network = [
                    ip_parts[0] & ((mask >> 24) & 0xff),
                    ip_parts[1] & ((mask >> 16) & 0xff),
                    ip_parts[2] & ((mask >> 8) & 0xff),
                    ip_parts[3] & (mask & 0xff)
                ]
                
                self.network_range = f"{'.'.join(map(str, network))}/{cidr}"
                print(f"[CONFIG] Network range: {self.network_range}")
                
                return self.network_range
            
        except Exception as e:
            print(f"[ERROR] Failed to detect network range: {e}")
            # Fallback basique
            if self.local_ip:
                octets = self.local_ip.split('.')
                self.network_range = f"{octets[0]}.{octets[1]}.{octets[2]}.0/24"
                return self.network_range
        
        # Fallback par défaut
        self.network_range = "192.168.1.0/24"
        return self.network_range
    
    def detect_gateway(self) -> str:
        """Détecte la passerelle par défaut"""
        try:
            result = subprocess.run(
                ["ip", "route", "show", "default"],
                capture_output=True, text=True, check=True
            )
            
            # Format: default via 192.168.1.1 dev eth0
            match = re.search(r'default via (\d+\.\d+\.\d+\.\d+)', result.stdout)
            if match:
                self.gateway = match.group(1)
                print(f"[CONFIG] Gateway: {self.gateway}")
                return self.gateway
                
        except Exception as e:
            print(f"[ERROR] Failed to detect gateway: {e}")
        
        return None
    
    def auto_configure(self) -> Dict:
        """
        Configuration automatique complète
        Retourne un dict avec toute la config réseau
        """
        self.detect_interface()
        self.detect_network_range()
        self.detect_gateway()
        
        return {
            'interface': self.interface,
            'local_ip': self.local_ip,
            'network_range': self.network_range,
            'gateway': self.gateway
        }


class Config:
    """Configuration globale de l'application"""
    
    def __init__(self):
        # Chemins du projet
        self.BASE_DIR = Path(__file__).parent.parent.parent
        self.SRC_DIR = self.BASE_DIR / "src"
        self.DATA_DIR = self.BASE_DIR / "data"
        self.LOGS_DIR = self.DATA_DIR / "logs"
        self.CONFIGS_DIR = self.BASE_DIR / "configs"
        
        # Créer les dossiers si nécessaire
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Configuration réseau (auto-détectée)
        net_config = NetworkConfig()
        network = net_config.auto_configure()
        
        self.INTERFACE = network['interface']
        self.LOCAL_IP = network['local_ip']
        self.NETWORK_RANGE = network['network_range']
        self.GATEWAY = network['gateway']
        
        # Serveur HTTP
        self.SERVER_HOST = "0.0.0.0"
        self.SERVER_PORT = 8080
        
        # MQTT
        self.MQTT_PORT = 1883
        self.MQTT_TIMEOUT = 10
        self.MQTT_QOS = 0
        
        # Attaques
        self.DEFAULT_ATTACK_INTERVAL = 5
        self.FLOOD_RATE = 0.1
        
        # Base de données
        self.DB_PATH = self.DATA_DIR / "emulator.db"
        
        # Logging
        self.LOG_LEVEL = "INFO"
        self.LOG_FILE = self.LOGS_DIR / "app.log"
        self.LOG_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
        self.LOG_BACKUP_COUNT = 5
        
    def __repr__(self):
        return f"""
IoT Adversary Emulator - Configuration
========================================
Network:
  Interface:     {self.INTERFACE}
  Local IP:      {self.LOCAL_IP}
  Network Range: {self.NETWORK_RANGE}
  Gateway:       {self.GATEWAY}

Server:
  Host: {self.SERVER_HOST}
  Port: {self.SERVER_PORT}

Paths:
  Base:    {self.BASE_DIR}
  Logs:    {self.LOGS_DIR}
  DB:      {self.DB_PATH}
========================================
"""


# Instance globale de configuration
config = Config()


if __name__ == "__main__":
    # Test de la configuration
    print(config)
    print("\n✅ Configuration auto-détectée avec succès!")
