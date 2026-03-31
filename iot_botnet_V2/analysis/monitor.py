# analysis/monitor.py
import json
import time
import os
import sys
from collections import deque

# Correction du chemin pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from protocols.mqtt_client import MQTTInterface
from config import settings
from analysis.sniffer import discover_iot_services # Ajout du sniffer

class AttackMonitor:
    def __init__(self):
        self.msg_history = deque() 
        self.window_size = 10 
        self.net = None

    def auto_discover(self):
        """Trouve le broker si nécessaire"""
        if settings.MQTT_CONFIG.get("broker") is None:
            print("[*] Moniteur : Recherche du broker sur le réseau...")
            services = discover_iot_services(settings.NETWORK_PREFIX)
            for ip, service in services:
                if service == "MQTT":
                    settings.MQTT_CONFIG["broker"] = ip
                    return True
            return False
        return True

    def on_message(self, client, userdata, msg):
        try:
            # On détecte si c'est un bot par le nom du topic ou contenu
            # Ici on cherche les identifiants de nos clones
            is_bot = any(id in msg.topic or id in str(msg.payload) for id in ["mkr_alpha", "mkr_beta", "mkr_gamma"])
            self.msg_history.append((time.time(), is_bot))
        except: pass

    def start(self):
        if not self.auto_discover():
            print("[!] Moniteur : Impossible de trouver le broker."); return

        self.net = MQTTInterface("GLOBAL_MONITOR", settings.MQTT_CONFIG)
        self.net.connect(settings.MQTT_CONFIG["broker"], 1883)
        
        # On s'abonne à tout pour analyser le trafic
        self.net.client.subscribe("#")
        self.net.client.on_message = self.on_message

        print(f"[*] Monitoring activé sur {settings.MQTT_CONFIG['broker']}")
        
        try:
            while True:
                # Calcul des taux
                now = time.time()
                while self.msg_history and (now - self.msg_history[0][0]) > self.window_size:
                    self.msg_history.popleft()
                
                total = len(self.msg_history)
                injected = sum(1 for ts, bot in self.msg_history if bot)
                rate = (injected / total * 100) if total > 0 else 0
                
                # Affichage
                os.system('clear' if os.name == 'posix' else 'cls')
                print("="*40)
                print(f"   BOTNET MONITOR | RATE: {rate:.1f}%")
                print("="*40)
                print(f"Messages (10s) : {total}")
                print(f"Légitimes      : {total - injected}")
                print(f"Injectés       : {injected}")
                
                bar = "█" * int(rate/5) + "-" * (20 - int(rate/5))
                print(f"\nIMPACT: [{bar}]")
                
                time.sleep(1)
        except KeyboardInterrupt: pass

if __name__ == "__main__":
    AttackMonitor().start()
