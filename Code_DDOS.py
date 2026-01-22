import json
import time
import paho.mqtt.publish as publish

# 🔹 Adresse de ton broker Mosquitto
BROKER_IP = "192.168.10.5"
PORT = 1883

# 🔹 Fonction d'envoi des données IoT
def send_sensor_data():
    temperature = 25.6
    humidity = 42.8
    pressure = 101.3

    # 🔸 Tu peux soit envoyer un seul JSON sur un topic,
    # soit plusieurs messages sur différents topics

    # Option 1 : Un seul topic avec un JSON
    payload = json.dumps({
        "temperature": temperature,
        "humidity": humidity,
        "pressure": pressure
    })

    messages = [
        {
            "topic": "iot/mkr1010/sensors",
            "payload": payload,
            "qos": 0,
            "retain": False
        },
        {
            "topic": "iot/unoR4wifi/sensors_state",
            "payload": "OK",
            "qos": 0
        }
    ]

    # 🔹 Envoi multiple d'un coup
    publish.multiple(messages, hostname=BROKER_IP, port=PORT)
    print("📡 Données publiées sur MQTT :")
    print(payload)


# 🔁 Envoi périodique
while True:
    send_sensor_data()
    time.sleep(5)
