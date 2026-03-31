# protocols/mqtt_client.py
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion # Nouvelle nécessité en v2.0

class MQTTInterface:
    def __init__(self, client_id, config):
        # Correction : Ajout de CallbackAPIVersion.VERSION1 ou VERSION2
        self.client = mqtt.Client(CallbackAPIVersion.VERSION1, client_id)
        self.client.username_pw_set(config["user"], config["pw"])
        
    def connect(self, host, port):
        try:
            self.client.connect(host, port, keepalive=60)
            self.client.loop_start()
        except Exception as e:
            print(f"[!] Erreur de connexion MQTT : {e}")

    def publish(self, topic, payload):
        self.client.publish(topic, payload)
