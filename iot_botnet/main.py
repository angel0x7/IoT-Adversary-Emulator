# main.py
import time
import threading
import sys
import json
import os
from bots.iot_sim import IoTBotSim
from analysis.sniffer import discover_iot_services, auto_detect_telemetry
from config import settings
from protocols.mqtt_client import MQTTInterface

class BotManager:
    def __init__(self):
        self.running_bots = {}
        self.net = None
        self.broker_ip = None

    def spawn_bot(self, bot_id):
        if self.broker_ip: # Sécurité : on ne lance que si on a une IP
            if bot_id not in self.running_bots:
                print(f"[*] Déploiement du bot : {bot_id}")
                bot = IoTBotSim(bot_id)
                thread = threading.Thread(target=bot.run, daemon=True)
                thread.start()
                self.running_bots[bot_id] = bot
        else:
            print(f"[!] Erreur : Impossible de lancer {bot_id}, IP broker manquante.")

    def start(self):
        print("="*50)
        print("   IOT BOTNET : AUTOMATIC MANAGER MODE   ")
        print("="*50)

        # 1. Recherche du Broker avec répétition si échec
        while not self.broker_ip:
            print(f"[*] Recherche du Broker sur {settings.NETWORK_PREFIX}.0/24...")
            services = discover_iot_services(settings.NETWORK_PREFIX)
            for ip, service in services:
                if service == "MQTT":
                    self.broker_ip = ip
                    break
            if not self.broker_ip:
                print("[!] Broker non trouvé. Nouvelle tentative dans 5s...")
                time.sleep(5)
        
        settings.MQTT_CONFIG["broker"] = self.broker_ip
        print(f"[+] Broker détecté à : {self.broker_ip}")

        # 2. Détection du Topic
        print("[*] Analyse du flux en cours... (Publiez des données avec l'Arduino !)")
        telemetry = auto_detect_telemetry(self.broker_ip)
        
        if telemetry["topic"]:
            settings.MQTT_CONFIG["topic_telemetry"] = telemetry["topic"]
            settings.ARDUINO_STATS["template"] = telemetry["keys"]
            print(f"[+] Cible identifiée : {telemetry['topic']}")
        else:
            print("[!] Topic non détecté. Utilisation du secours.")
            settings.MQTT_CONFIG["topic_telemetry"] = "iot/mkr1010/sensors"

        # 3. Connexion du Manager
        try:
            self.net = MQTTInterface("BOT_MANAGER", settings.MQTT_CONFIG)
            self.net.connect(self.broker_ip, 1883)
            self.net.client.subscribe("botnet/manage")
            self.net.client.on_message = self.on_message_callback
            self.net.client.loop_start()
        except Exception as e:
            print(f"[!!] Erreur connexion Manager : {e}")
            sys.exit(1)

        # 4. Lancement des bots initiaux
        for name in ["mkr_alpha", "mkr_beta", "mkr_gamma"]:
            self.spawn_bot(name)
            time.sleep(0.2)

        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            print("\n[*] Arrêt.")

    def on_message_callback(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            if data.get("action") == "SPAWN":
                for _ in range(data.get("count", 1)):
                    new_id = f"mkr_extra_{len(self.running_bots) + 1}"
                    self.spawn_bot(new_id)
        except: pass

if __name__ == "__main__":
    BotManager().start()
