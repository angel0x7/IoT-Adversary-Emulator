# config/settings.py

# On définit le segment réseau à scanner
NETWORK_PREFIX = "172.20.10" 

MQTT_CONFIG = {
    "broker": None,               # Sera rempli dynamiquement
    "port": 1883,
    "user": "mkr1010",
    "pw": "admin",
    "topic_telemetry": "iot/mkr1010/sensors",
    "topic_c2": "cmd/botnet/system"
}

ARDUINO_STATS = {
    "interval": 5.0,
    "jitter": 0.15,
    "temp_mean": 24.0,
    "hum_mean": 50.0,
    "pres_mean": 1013.0
}
