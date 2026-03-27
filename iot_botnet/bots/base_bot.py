# bots/base_bot.py
import json
from protocols.mqtt_client import MQTTInterface
from config.settings import MQTT_CONFIG

class BaseBot:
    def __init__(self, bot_id):
        self.bot_id = bot_id
        self.mode = "NORMAL"
        # Utilise l'interface MQTT v2.0 corrigée
        self.net = MQTTInterface(self.bot_id, MQTT_CONFIG)

    def setup(self):
        """Initialisation de la connexion et des abonnements"""
        if not MQTT_CONFIG["broker"]:
            print(f"[!] {self.bot_id} : Erreur, IP du broker manquante.")
            return
            
        self.net.connect(MQTT_CONFIG["broker"], MQTT_CONFIG["port"])
        
        # Le bot s'abonne au topic de commande du C2
        self.net.client.subscribe(MQTT_CONFIG["topic_c2"])
        self.net.client.on_message = self.on_c2_command
        print(f"[*] {self.bot_id} connecté et en attente d'ordres sur {MQTT_CONFIG['topic_c2']}")

    def on_c2_command(self, client, userdata, msg):
        """Réception et décodage des ordres du C2"""
        try:
            payload = json.loads(msg.payload.decode())
            
            # Vérification de la cible (soit 'all', soit l'ID précis du bot)
            if payload.get("target") in ["all", self.bot_id]:
                self.mode = payload.get("mode", self.mode)
                
                # Transmission des paramètres (comme le biais) à la méthode spécifique
                params = payload.get("params", {})
                self.handle_custom_params(params)
                
                print(f"[{self.bot_id}] Ordre C2 appliqué : Mode={self.mode}")
        except Exception as e:
            print(f"[!] Erreur de commande sur {self.bot_id}: {e}")

    def handle_custom_params(self, params):
        """Méthode à surcharger dans iot_sim.py"""
        pass

    def run(self):
        raise NotImplementedError("La méthode run() doit être définie dans la classe enfant.")
