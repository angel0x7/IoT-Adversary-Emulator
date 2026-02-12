#!/usr/bin/env python3
"""
Network Scanner Module - IoT Adversary Emulator
Scanner réseau intelligent avec détection automatique et identification précise
"""

import subprocess
import socket
import re
import time
from typing import List, Dict, Optional
from dataclasses import dataclass

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None


@dataclass
class Device:
    """Représentation d'un device détecté"""
    ip: str
    mac: Optional[str] = None
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    ports_open: List[int] = None
    device_type: str = "unknown"
    
    def __post_init__(self):
        if self.ports_open is None:
            self.ports_open = []


class NetworkScanner:
    """Scanner réseau intelligent avec auto-détection"""
    
    def __init__(self, interface: str, network_range: str):
        """
        Args:
            interface: Interface réseau (ex: "eth0")
            network_range: Range réseau CIDR (ex: "192.168.1.0/24")
        """
        self.interface = interface
        self.network_range = network_range
        self.local_ip = None
        self.devices: List[Device] = []
        
        # Base de données de vendors MAC (partielle)
        self.mac_vendors = {
            '00:11:22': 'Arduino',
            '00:A0:50': 'Arduino',
            'A4:CF:12': 'Arduino',
            '98:CD:AC': 'ESP32',
            '24:0A:C4': 'ESP32',
            '30:AE:A4': 'ESP32',
        }
    
    def get_local_ip(self) -> bool:
        """Récupère l'IP locale de l'interface"""
        try:
            result = subprocess.run(
                ["ip", "-4", "addr", "show", self.interface],
                capture_output=True, text=True, check=True
            )
            
            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)', result.stdout)
            if match:
                self.local_ip = match.group(1)
                print(f"[SCAN] IP locale: {self.local_ip}")
                return True
            return False
        except Exception as e:
            print(f"[ERROR] Get local IP: {e}")
            return False
    
    def ping_sweep(self) -> List[str]:
        """
        Scan rapide avec ping pour détecter les hosts actifs
        Plus rapide que nmap pour un premier scan
        """
        print(f"[SCAN] Quick ping sweep on {self.network_range}...")
        
        # Extraire le préfixe réseau
        network_prefix = '.'.join(self.network_range.split('.')[:3])
        
        active_ips = []
        
        # Ping tous les hosts du réseau (1-254)
        for i in range(1, 255):
            ip = f"{network_prefix}.{i}"
            
            # Éviter de pinger notre propre IP
            if ip == self.local_ip:
                continue
            
            # Ping avec timeout court
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "1", ip],
                capture_output=True,
                timeout=2
            )
            
            if result.returncode == 0:
                active_ips.append(ip)
                print(f"[SCAN]   ✓ {ip} is alive")
        
        print(f"[SCAN] Ping sweep found {len(active_ips)} active hosts")
        return active_ips
    
    def nmap_scan(self, targets: Optional[List[str]] = None) -> List[str]:
        """
        Scan nmap pour découverte de hosts
        
        Args:
            targets: Liste d'IPs à scanner (optionnel, sinon tout le range)
        """
        try:
            if targets:
                # Scanner seulement les IPs spécifiées
                target_list = ' '.join(targets)
                print(f"[SCAN] Nmap scanning {len(targets)} targets...")
            else:
                # Scanner tout le range
                target_list = self.network_range
                print(f"[SCAN] Nmap scanning {self.network_range}...")
            
            # Scan avec détection de OS et services
            result = subprocess.run(
                ["sudo", "nmap", "-sn", "-n", "-T4", target_list],
                capture_output=True, text=True, check=True, timeout=120
            )
            
            # Extraire les IPs
            ips = re.findall(r'Nmap scan report for .*?(\d+\.\d+\.\d+\.\d+)', result.stdout)
            
            # Filtrer notre IP
            ips = [ip for ip in ips if ip != self.local_ip]
            
            print(f"[SCAN] Nmap found {len(ips)} hosts")
            return ips
            
        except subprocess.TimeoutExpired:
            print("[ERROR] Nmap scan timeout")
            return []
        except Exception as e:
            print(f"[ERROR] Nmap scan: {e}")
            return []
    
    def get_mac_address(self, ip: str) -> Optional[str]:
        """Récupère l'adresse MAC d'une IP via ARP"""
        try:
            # Ping d'abord pour remplir le cache ARP
            subprocess.run(
                ["ping", "-c", "1", "-W", "1", ip],
                capture_output=True,
                timeout=2
            )
            
            # Lire la table ARP
            result = subprocess.run(
                ["arp", "-n", ip],
                capture_output=True, text=True
            )
            
            # Format: 192.168.1.10 ether a4:cf:12:34:56:78 C eth0
            match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', result.stdout)
            if match:
                return match.group(0).upper()
            
        except Exception as e:
            print(f"[DEBUG] MAC address for {ip}: {e}")
        
        return None
    
    def identify_vendor(self, mac: str) -> Optional[str]:
        """Identifie le vendor à partir du préfixe MAC"""
        if not mac:
            return None
        
        # Nettoyer le MAC
        mac_clean = mac.replace(':', '').replace('-', '').upper()
        
        # Vérifier les préfixes connus
        for prefix, vendor in self.mac_vendors.items():
            prefix_clean = prefix.replace(':', '').replace('-', '').upper()
            if mac_clean.startswith(prefix_clean):
                return vendor
        
        return None
    
    def port_scan(self, ip: str, ports: List[int] = None) -> List[int]:
        """
        Scan des ports ouverts sur une IP
        
        Args:
            ip: IP cible
            ports: Liste de ports à scanner (défaut: ports communs IoT)
        """
        if ports is None:
            # Ports communs pour IoT
            ports = [
                21,    # FTP
                22,    # SSH
                23,    # Telnet
                80,    # HTTP
                443,   # HTTPS
                1883,  # MQTT
                8080,  # HTTP alternatif
                8883,  # MQTT SSL
            ]
        
        open_ports = []
        
        for port in ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                open_ports.append(port)
        
        return open_ports
    
    def identify_mqtt_broker(self, devices: List[Device]) -> Optional[Device]:
        """
        Identifie le broker MQTT parmi les devices
        
        Returns:
            Le device broker ou None
        """
        print("[SCAN] Searching for MQTT broker (port 1883)...")
        
        if not mqtt:
            print("[WARNING] paho-mqtt not installed, cannot verify MQTT")
            # Fallback: chercher port 1883 ouvert
            for device in devices:
                if 1883 in device.ports_open:
                    device.device_type = "broker"
                    print(f"[SCAN] ✓ Broker found at {device.ip} (port 1883 open)")
                    return device
            return None
        
        for device in devices:
            # Vérifier port 1883
            if 1883 not in device.ports_open:
                continue
            
            # Tester connexion MQTT réelle
            try:
                test_client = mqtt.Client(client_id="scanner_test", clean_session=True)
                test_client.connect(device.ip, 1883, 5)
                test_client.loop_start()
                time.sleep(1)
                test_client.loop_stop()
                test_client.disconnect()
                
                device.device_type = "broker"
                print(f"[SCAN] ✓ MQTT Broker confirmed at {device.ip}")
                return device
                
            except Exception as e:
                print(f"[DEBUG] {device.ip} port 1883 open but MQTT failed: {e}")
        
        print("[SCAN] No MQTT broker found")
        return None
    
    def identify_mkr1010(self, devices: List[Device], broker: Optional[Device]) -> Optional[Device]:
        """
        Identifie le MKR1010 avec plusieurs méthodes de détection
        
        Méthode 1: Via MAC address (Arduino vendor)
        Méthode 2: Via MQTT traffic listening
        Méthode 3: Via pattern matching (premier IoT device non-broker)
        
        Returns:
            Le device MKR1010 ou None
        """
        print("[SCAN] Searching for MKR1010 device...")
        
        mkr1010_candidates = []
        
        # Méthode 1: MAC address
        for device in devices:
            if device.device_type == "broker":
                continue
            
            vendor = self.identify_vendor(device.mac) if device.mac else None
            if vendor and 'Arduino' in vendor:
                print(f"[SCAN] ✓ Arduino device detected at {device.ip} (MAC: {device.mac})")
                device.device_type = "mkr1010"
                return device
        
        # Méthode 2: MQTT traffic listening
        if broker and mqtt:
            mkr_device = self._listen_mqtt_for_mkr(broker.ip)
            if mkr_device:
                # Trouver le device correspondant
                for device in devices:
                    if device.ip == mkr_device:
                        device.device_type = "mkr1010"
                        print(f"[SCAN] ✓ MKR1010 confirmed via MQTT at {device.ip}")
                        return device
        
        # Méthode 3: Heuristique - premier device IoT
        print("[SCAN] Using heuristic to identify MKR1010...")
        for device in devices:
            if device.device_type == "broker":
                continue
            
            # Devices IoT ont souvent ces ports ouverts
            iot_indicators = [
                80 in device.ports_open,    # Web interface
                23 in device.ports_open,    # Telnet (IoT devices)
                len(device.ports_open) < 5  # Peu de ports (embedded)
            ]
            
            if any(iot_indicators):
                mkr1010_candidates.append(device)
        
        if mkr1010_candidates:
            # Prendre le premier candidat
            best_candidate = mkr1010_candidates[0]
            best_candidate.device_type = "mkr1010"
            print(f"[SCAN] ✓ MKR1010 identified at {best_candidate.ip} (heuristic)")
            return best_candidate
        
        print("[WARNING] Could not identify MKR1010 device")
        return None
    
    def _listen_mqtt_for_mkr(self, broker_ip: str, duration: int = 5) -> Optional[str]:
        """
        Écoute le trafic MQTT pour détecter le MKR1010
        
        Args:
            broker_ip: IP du broker MQTT
            duration: Durée d'écoute en secondes
        
        Returns:
            IP du MKR1010 ou None
        """
        if not mqtt:
            return None
        
        detected_ips = []
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                client.subscribe("#", qos=0)  # Tous les topics
        
        def on_message(client, userdata, msg):
            try:
                # Essayer de parser le payload
                payload = msg.payload.decode()
                
                # Chercher patterns MKR1010
                if any(keyword in payload.lower() for keyword in ['mkr', 'arduino', 'sensor']):
                    # Essayer d'extraire une IP du topic ou du payload
                    # Topic souvent: iot/device_192.168.1.10/sensors
                    ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', msg.topic + payload)
                    if ip_match:
                        ip = ip_match.group(1)
                        if ip != broker_ip:
                            detected_ips.append(ip)
            except:
                pass
        
        try:
            listener = mqtt.Client(client_id="mkr_listener", clean_session=True)
            listener.on_connect = on_connect
            listener.on_message = on_message
            listener.connect(broker_ip, 1883, 10)
            listener.loop_start()
            
            print(f"[SCAN] Listening to MQTT traffic for {duration}s...")
            time.sleep(duration)
            
            listener.loop_stop()
            listener.disconnect()
            
            if detected_ips:
                # Retourner la plus fréquente
                from collections import Counter
                most_common = Counter(detected_ips).most_common(1)
                return most_common[0][0]
        
        except Exception as e:
            print(f"[DEBUG] MQTT listening error: {e}")
        
        return None
    
    def scan_network(self) -> List[Device]:
        """
        Scan complet du réseau avec toutes les méthodes
        
        Returns:
            Liste de devices détectés
        """
        print(f"\n{'='*60}")
        print("NETWORK SCAN STARTING")
        print(f"{'='*60}\n")
        
        # 1. Obtenir l'IP locale
        if not self.get_local_ip():
            print("[ERROR] Failed to get local IP")
            return []
        
        # 2. Ping sweep rapide
        active_ips = self.ping_sweep()
        
        # 3. Si peu de résultats, faire un nmap complet
        if len(active_ips) < 2:
            print("[SCAN] Few devices found with ping, trying nmap...")
            active_ips = self.nmap_scan()
        
        if not active_ips:
            print("[ERROR] No devices found on network")
            return []
        
        # 4. Analyser chaque device
        print(f"\n[SCAN] Analyzing {len(active_ips)} devices...")
        devices = []
        
        for ip in active_ips:
            print(f"\n[SCAN] Analyzing {ip}...")
            
            # Créer le device
            device = Device(ip=ip)
            
            # Obtenir MAC
            device.mac = self.get_mac_address(ip)
            if device.mac:
                print(f"  MAC: {device.mac}")
                device.vendor = self.identify_vendor(device.mac)
                if device.vendor:
                    print(f"  Vendor: {device.vendor}")
            
            # Scanner les ports
            device.ports_open = self.port_scan(ip)
            if device.ports_open:
                print(f"  Open ports: {device.ports_open}")
            
            devices.append(device)
        
        # 5. Identifier le broker MQTT
        broker = self.identify_mqtt_broker(devices)
        
        # 6. Identifier le MKR1010
        mkr1010 = self.identify_mkr1010(devices, broker)
        
        # 7. Classifier les autres devices
        for device in devices:
            if device.device_type == "unknown":
                device.device_type = "iot"
        
        self.devices = devices
        
        print(f"\n{'='*60}")
        print("SCAN COMPLETE")
        print(f"{'='*60}")
        print(f"Total devices found: {len(devices)}")
        if broker:
            print(f"MQTT Broker: {broker.ip}")
        if mkr1010:
            print(f"MKR1010 Device: {mkr1010.ip}")
        print(f"{'='*60}\n")
        
        return devices


# Test du scanner
if __name__ == "__main__":
    import sys
    
    # Configuration
    interface = "eth0"
    network_range = "192.168.10.0/24"
    
    if len(sys.argv) > 1:
        interface = sys.argv[1]
    if len(sys.argv) > 2:
        network_range = sys.argv[2]
    
    print(f"Testing scanner on {interface} / {network_range}\n")
    
    scanner = NetworkScanner(interface, network_range)
    devices = scanner.scan_network()
    
    print("\nDevices found:")
    for device in devices:
        print(f"  {device.ip:15} | Type: {device.device_type:10} | MAC: {device.mac or 'N/A'}")
