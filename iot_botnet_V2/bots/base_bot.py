# bots/base_bot.py
import json
import urllib.request
import time
from protocols.mqtt_client import MQTTInterface
from config.settings import MQTT_CONFIG

class BaseBot:
    def __init__(self, bot_id):
        self.bot_id = bot_id
        self.mode = "NORMAL"
        self.is_running = True # Drapeau pour arrêter le bot proprement
        # Utilise l'interface MQTT v2.0 corrigée
        self.net = MQTTInterface(self.bot_id, MQTT_CONFIG)
        self.api_url = "http://localhost:8000/log"

    def log_to_dashboard(self, msg, level="info"):
        """Envoie un log au dashboard via l'API Server"""
        try:
            data = json.dumps({"bot_id": self.bot_id, "msg": msg, "level": level}).encode()
            req = urllib.request.Request(self.api_url, data=data, headers={'Content-Type': 'application/json'})
            urllib.request.urlopen(req, timeout=1)
        except:
            pass # Silencieux si l'API n'est pas lancée

    def setup(self):
        """Initialisation de la connexion et des abonnements"""
        if not MQTT_CONFIG["broker"]:
            print(f"[!] {self.bot_id} : Erreur, IP du broker manquante.")
            return
            
        self.net.connect(MQTT_CONFIG["broker"], MQTT_CONFIG["port"])
        
        # Le bot s'abonne au topic de commande du C2
        self.net.client.subscribe(MQTT_CONFIG["topic_c2"])
        self.net.client.on_message = self.on_c2_command
        
        msg = f"Connecté au Broker et en attente d'ordres."
        print(f"[*] {self.bot_id} {msg}")
        self.log_to_dashboard(msg)

        # Enregistrement pour l'inventaire C2
        self.net.publish("botnet/inventory", json.dumps({"bot_id": self.bot_id}))

    def on_c2_command(self, client, userdata, msg):
        """Réception et décodage des ordres du C2"""
        try:
            payload = json.loads(msg.payload.decode())
            
            # Vérification de la cible (soit 'all', soit l'ID précis du bot)
            target = payload.get("target")
            if target in ["all", self.bot_id]:
                new_mode = payload.get("mode")
                
                # Gestion de l'arrêt du bot
                if new_mode == "KILL":
                    self.is_running = False
                    log_msg = "Ordre d'arrêt reçu. Déconnexion..."
                    print(f"[{self.bot_id}] {log_msg}")
                    self.log_to_dashboard(log_msg, "error")
                    self.net.client.disconnect()
                    return

                old_mode = self.mode
                self.mode = new_mode if new_mode else self.mode
                
                # Transmission des paramètres à la méthode spécifique
                params = payload.get("params", {})
                self.handle_custom_params(params)
                
                log_msg = f"Mode {old_mode} -> {self.mode}"
                print(f"[{self.bot_id}] {log_msg}")
                self.log_to_dashboard(log_msg)
        except Exception as e:
            print(f"[!] Erreur de commande sur {self.bot_id}: {e}")

    def handle_custom_params(self, params):
        """Méthode à surcharger dans iot_sim.py"""
        pass

    def run(self):
        raise NotImplementedError("La méthode run() doit être définie dans la classe enfant.")
