#include <WiFiNINA.h>
#include <PubSubClient.h>
#include <Arduino_MKRIoTCarrier.h>

// === Initialisation Carrier ===
MKRIoTCarrier carrier;

// === Wi-Fi (ESP32 AP) et MQTT (VM Debian) ===
const char* ssid = "Reseau_OT_Segment";      // AP ESP32
const char* password = "12345678";
const char* mqtt_server = "192.168.2.100";   // IP VM Debian
const int mqtt_port = 1883;
const char* mqtt_topic = "mkr1010/sensors";

WiFiClient wifiClient;
PubSubClient client(wifiClient);

// === Capteurs ===
float current_temperature = 0.0;
float current_humidity = 0.0;
float current_iaq = 0.0;
float current_iaq_static = 0.0;

// === Fonctions ===
void connectWiFi() {
  Serial.print("Connexion Wi-Fi à ESP32 AP...");
  WiFi.begin(ssid, password);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConnecté !");
    Serial.print("IP MKR : "); Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nÉchec connexion Wi-Fi !");
  }
}

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("Connexion au broker MQTT...");
    if (client.connect("MKR1010_Client")) {
      Serial.println("OK");
    } else {
      Serial.print("Échec rc=");
      Serial.print(client.state());
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(9600);
  carrier.begin();
  carrier.AirQuality.begin();

  connectWiFi();

  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  // Reconnexion MQTT si nécessaire
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();

  // Lecture capteurs
  current_temperature = carrier.Env.readTemperature();
  current_humidity = carrier.Env.readHumidity();
  current_iaq = carrier.AirQuality.readIAQ();
  current_iaq_static = carrier.AirQuality.readStaticIAQ();

  // Message MQTT
  String payload = "T:" + String(current_temperature,1) +
                   "|H:" + String(current_humidity,0) +
                   "|IAQ:" + String(current_iaq,0) +
                   "|IAQS:" + String(current_iaq_static,0);

  // Publication
  if (client.publish(mqtt_topic, payload.c_str())) {
    Serial.print("Publié : "); Serial.println(payload);
  } else {
    Serial.println("Échec publication MQTT !");
  }

  delay(15000); // toutes les 15s
}
