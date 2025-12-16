#include <WiFi.h>
#include <PubSubClient.h>

/* ===== CONFIG ===== */
#define AP_SSID       "ESP32_AP"
#define AP_PASSWORD   "12345678"

#define MQTT_SERVER   "192.168.4.2"
#define MQTT_PORT     1883

#define MQTT_PUB_TOPIC "esp32/status"
#define MQTT_SUB_TOPIC "esp32/cmd"

/* ================== */

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastMsg = 0;

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message reçu [");
  Serial.print(topic);
  Serial.print("] : ");

  String msg;
  for (int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }
  Serial.println(msg);

  if (msg == "ON") {
    Serial.println("Commande ON reçue");
  }
  if (msg == "OFF") {
    Serial.println("Commande OFF reçue");
  }
}

void setup_wifi_ap() {
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASSWORD);

  IPAddress IP = WiFi.softAPIP();
  Serial.print("ESP32 AP IP : ");
  Serial.println(IP);
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Connexion MQTT...");
    if (client.connect("ESP32_AP_Client")) {
      Serial.println("OK");
      client.subscribe(MQTT_SUB_TOPIC);
    } else {
      Serial.print("Échec, rc=");
      Serial.print(client.state());
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);

  setup_wifi_ap();

  client.setServer(MQTT_SERVER, MQTT_PORT);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();
  if (now - lastMsg > 5000) {
    lastMsg = now;
    client.publish(MQTT_PUB_TOPIC, "ESP32 actif");
  }
}
