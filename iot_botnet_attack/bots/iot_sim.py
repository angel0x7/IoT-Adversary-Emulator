# bots/iot_sim.py
import json
import random
import time
from collections import deque # Nécessaire pour le buffer de rejeu
from bots.base_bot import BaseBot
from protocols.coap_client import CoAPInterface
from config.settings import MQTT_CONFIG, ARDUINO_STATS

class IoTBotSim(BaseBot):
    def __init__(self, bot_id):
        super().__init__(bot_id)
        self.current_bias = 0.0
        self.coap = CoAPInterface()
        self.template = ARDUINO_STATS.get("template", ["temperature", "humidity", "pressure"])
        self.frozen_data = None  # Pour le mode Data Freezing
        self.flood_speed = 0.01  # Délai entre messages en mode Flood
        
        # --- Nouvelles variables pour Replay Attack ---
        self.history = deque(maxlen=200) # Stocke les 200 derniers messages capturés
        self.replay_index = 0

    def handle_custom_params(self, params):
        """Réception des ordres complexes du C2"""
        self.manual_values = params.get("manual", False)
        
        # Reset de l'index si on lance un nouveau rejeu
        if self.mode == "REPLAY":
            self.replay_index = 0
            print(f"[{self.bot_id}] Mode REPLAY activé. Buffer: {len(self.history)} messages.")
        
        # Gestion du Data Freezing
        if self.mode == "FREEZE" and self.frozen_data is None:
            self.frozen_data = self.generate_simulated_data()
            print(f"[{self.bot_id}] Données GELEES : {self.frozen_data}")
        elif self.mode != "FREEZE":
            self.frozen_data = None # Reset si on change de mode

        # Valeurs manuelles ou biais
        if self.manual_values:
            self.fixed_temp = params.get("temp")
            self.fixed_hum = params.get("hum")
            self.fixed_pres = params.get("pres")
        else:
            self.current_bias = params.get("bias", 0.0)

    def generate_simulated_data(self):
        # 1. Mode REPLAY (Prioritaire)
        if self.mode == "REPLAY":
            if len(self.history) > 0:
                # On pioche dans l'historique enregistré
                data = self.history[self.replay_index]
                self.replay_index = (self.replay_index + 1) % len(self.history)
                return data
            else:
                # Si le buffer est vide, on renvoie une erreur ou une valeur neutre
                return {"status": "buffering", "info": "No history recorded yet"}

        # 2. Mode FREEZE
        if self.mode == "FREEZE" and self.frozen_data:
            return self.frozen_data

        # 3. Mode MANUAL
        if self.mode == "ATTACK" and getattr(self, 'manual_values', False):
            return {"temperature": self.fixed_temp, "humidity": self.fixed_hum, "pressure": self.fixed_pres}

        # 4. Mode NORMAL / DRIFT / FLOOD
        payload = {}
        for key in self.template:
            if key == "temperature":
                val = ARDUINO_STATS["temp_mean"] + random.uniform(-0.1, 0.1)
                if self.mode in ["ATTACK", "FLOOD"]: val += self.current_bias
            elif key == "humidity": val = ARDUINO_STATS["hum_mean"] + random.uniform(-0.5, 0.5)
            elif key == "pressure": val = ARDUINO_STATS["pres_mean"] + random.uniform(-0.2, 0.2)
            else: val = random.uniform(20, 30)
            payload[key] = round(val, 2)
            
        # --- APPRENTISSAGE PASSIF ---
        # Si le bot est en mode NORMAL, il enregistre les données pour pouvoir les rejouer plus tard
        if self.mode == "NORMAL":
            self.history.append(payload)
            
        return payload

    def run(self):
        self.setup()
        while self.is_running:
            topic = MQTT_CONFIG.get("topic_telemetry")
            if topic:
                data = self.generate_simulated_data()
                payload_str = json.dumps(data)
                self.net.publish(topic, payload_str)
                
                # En mode FLOOD, on ignore le CoAP et on bombarde le MQTT
                if self.mode == "FLOOD":
                    time.sleep(self.flood_speed) 
                    continue # On saute le sleep normal de 5s
                
                self.coap.send_sync(MQTT_CONFIG["broker"], "sensors", payload_str)
            
            # Rythme normal
            time.sleep(5.0 + random.uniform(-0.1, 0.1))
        
        print(f"[*] {self.bot_id} thread terminé.")
