# analysis/sniffer.py
import socket
import json
import time
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
from concurrent.futures import ThreadPoolExecutor

def scan_port(ip, port, timeout=0.1):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((ip, port)) == 0
    except: return False

def discover_iot_services(network_prefix):
    discovered = []
    ips = [f"{network_prefix}.{i}" for i in range(1, 255)]
    
    def check_host(ip):
        if scan_port(ip, 1883):
            return (ip, "MQTT") # Retourne bien un tuple de 2 valeurs
        return None

    with ThreadPoolExecutor(max_workers=100) as executor:
        results = list(executor.map(check_host, ips))
    
    return [r for r in results if r is not None]

def auto_detect_telemetry(broker_ip, timeout=15):
    detected = {"topic": None, "keys": []}
    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            if "temperature" in payload:
                detected["topic"] = msg.topic
                detected["keys"] = list(payload.keys())
        except: pass

    scanner = mqtt.Client(CallbackAPIVersion.VERSION1, "ScannerBot")
    try:
        scanner.connect(broker_ip, 1883)
        scanner.subscribe("#")
        scanner.on_message = on_message
        scanner.loop_start()
        start = time.time()
        while detected["topic"] is None and (time.time() - start) < timeout:
            time.sleep(1)
        scanner.loop_stop()
    except: pass
    return detected
