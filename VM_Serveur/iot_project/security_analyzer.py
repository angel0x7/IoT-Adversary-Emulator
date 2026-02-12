import time
import json
import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient

# =============================
# CONFIG
# =============================

MQTT_BROKER = "192.168.10.6"
MQTT_PORT = 1883
MQTT_TOPIC_OUT = "iot/security/analysis"

INFLUX_HOST = "localhost"
INFLUX_PORT = 8086
INFLUX_DB = "iotdata"

# =============================
# SEUILS
# =============================

DELTA_WARNING = 2.0
DELTA_CRITICAL = 5.0

INTERVAL_WARNING = 7
INTERVAL_CRITICAL = 15

MAX_MESSAGES_PER_MIN = 20

# =============================
# CONNEXIONS
# =============================

mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

influx = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
influx.switch_database(INFLUX_DB)

print("🧠 Security Analyzer lancé...")

last_time = None
message_count = 0
start_minute = time.time()

# =============================
# FONCTION RECUP DERNIERE MESURE
# =============================

def get_last_measurement(measurement):
    try:
        query = f"SELECT * FROM {measurement} ORDER BY time DESC LIMIT 1"
        result = list(influx.query(query).get_points())
        if result:
            return result[0]
    except Exception as e:
        print("Erreur Influx:", e)
    return None

# =============================
# LOOP PRINCIPALE
# =============================

while True:
    try:
        current_time = time.time()

        mqtt_data = get_last_measurement("sensors")
        coap_data = get_last_measurement("sensors_coap")

        if mqtt_data and coap_data:

            delta_temp = abs(mqtt_data["temperature"] - coap_data["temperature"])
            delta_hum = abs(mqtt_data["humidity"] - coap_data["humidity"])
            delta_pres = abs(mqtt_data["pressure"] - coap_data["pressure"])

            max_delta = max(delta_temp, delta_hum, delta_pres)

            logs = []
            severity = "OK"

            # ==========================
            # 1️⃣ Désynchronisation
            # ==========================

            if max_delta > DELTA_CRITICAL:
                severity = "CRITICAL"
                logs.append("🚨 Incohérence critique MQTT vs CoAP")
            elif max_delta > DELTA_WARNING:
                severity = "WARNING"
                logs.append("⚠️ Écart suspect entre MQTT et CoAP")

            # ==========================
            # 2️⃣ Analyse timing
            # ==========================

            if last_time is not None:
                interval = current_time - last_time

                if interval > INTERVAL_CRITICAL:
                    severity = "CRITICAL"
                    logs.append(f"⏱ Délai anormal ({interval:.2f}s) → possible interception")

                elif interval > INTERVAL_WARNING:
                    if severity != "CRITICAL":
                        severity = "WARNING"
                    logs.append(f"⏱ Délai légèrement élevé ({interval:.2f}s)")

            last_time = current_time

            # ==========================
            # 3️⃣ Détection DDOS
            # ==========================

            message_count += 1

            if current_time - start_minute >= 60:
                if message_count > MAX_MESSAGES_PER_MIN:
                    severity = "CRITICAL"
                    logs.append(f"🚨 Volume anormal ({message_count}/min) → possible DDOS")

                message_count = 0
                start_minute = current_time

            # ==========================
            # PAYLOAD MQTT
            # ==========================

            payload = {
                "mqtt_temperature": mqtt_data["temperature"],
                "coap_temperature": coap_data["temperature"],
                "delta_temperature": delta_temp,
                "delta_humidity": delta_hum,
                "delta_pressure": delta_pres,
                "severity": severity,
                "logs": logs
            }

            mqtt_client.publish(MQTT_TOPIC_OUT, json.dumps(payload))

            # ==========================
            # ÉCRITURE INFLUX
            # ==========================

            json_body = [{
                "measurement": "security_logs",
                "fields": {
                    "delta_temperature": float(delta_temp),
                    "delta_humidity": float(delta_hum),
                    "delta_pressure": float(delta_pres),
                    "severity": severity,
                    "max_delta": float(max_delta),
                    "log_count": len(logs)
                }
            }]

            influx.write_points(json_body)

            print("📤 Analyse publiée & enregistrée :", payload)

    except Exception as e:
        print("Erreur analyse :", e)

    time.sleep(5)
