import paho.mqtt.client as mqtt

# On définit le topic à écouter (doit être IDENTIQUE à l'Arduino)
TOPIC = "iot/mkr1010/env"

def on_message(client, userdata, msg):
    print(f"Message reçu sur {msg.topic} : {msg.payload.decode()}")
    # Ici, vous pouvez ajouter du code pour enregistrer dans une base de données
    with open("donnees_capteurs.log", "a") as f:
        f.write(msg.payload.decode() + "\n")

client = mqtt.Client()
client.on_message = on_message
client.connect("localhost", 1883)
client.subscribe(TOPIC) # La VM s'abonne au topic

print("En attente des données de l'Arduino...")
client.loop_forever()
