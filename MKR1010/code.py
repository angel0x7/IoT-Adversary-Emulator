#include <WiFiNINA.h>
#include <PubSubClient.h>
#include <WiFiUdp.h>
#include "Arduino_MKRIoTCarrier.h"

// ===== Wi-Fi =====
const char* ssid = "Ma_Box_Isolee";
const char* password = "12345678";

// ===== Serveur =====
const char* server_ip = "192.168.10.6";
const int mqttPort = 1883;
const int coapPort = 5683;

// ===== Objets =====
WiFiClient espClient;
PubSubClient mqttClient(espClient);
WiFiUDP udp;
MKRIoTCarrier carrier;

unsigned long lastMsg = 0;

// ===== Wi-Fi =====
void setup_wifi() {
  Serial.print("Connexion WiFi...");
  while (WiFi.begin(ssid, password) != WL_CONNECTED) {
    delay(2000);
    Serial.print(".");
  }
  Serial.println("\nWiFi connecté");
  Serial.print("IP MKR1010: ");
  Serial.println(WiFi.localIP());
}

// ===== MQTT =====
void reconnect_mqtt() {
  while (!mqttClient.connected()) {
    Serial.print("Connexion MQTT...");
    if (mqttClient.connect("MKR1010Client")) {
      Serial.println("OK");
    } else {
      Serial.print("Erreur: ");
      Serial.println(mqttClient.state());
      delay(3000);
    }
  }
}
uint16_t messageId = 0;

// ===== CoAP POST (UDP brut) =====
void sendCoAP(String payload) {
  messageId ++;
 
  byte coapPacket[256];
  int index = 0;

  coapPacket[index++] = 0x50; // Version 1, Confirmable
  coapPacket[index++] = 0x02; // Code 0.02 = POST


  coapPacket[index++] = (messageId >> 8) & 0xFF; // Message ID
  coapPacket[index++] = messageId & 0xFF;

  // Option Uri-Path = "sensors"
  coapPacket[index++] = 0xB7;
  memcpy(&coapPacket[index], "sensors", 7);
  index += 7;

  // Payload marker
  coapPacket[index++] = 0xFF;

  // Payload JSON
  payload.getBytes(&coapPacket[index], payload.length() + 1);
  index += payload.length();

  udp.beginPacket(server_ip, coapPort);
  udp.write(coapPacket, index);
  udp.endPacket();

  Serial.print("CoAP envoyé (ID: ");
  Serial.print(messageId);
  Serial.println(") : " + payload);


}

// ===== SETUP =====
void setup() {
  Serial.begin(9600);
  carrier.begin();
  setup_wifi();

  mqttClient.setServer(server_ip, mqttPort);
  udp.begin(5683);
}

// ===== LOOP =====
void loop() {
  if (!mqttClient.connected()) {
    reconnect_mqtt();
  }
  mqttClient.loop();

  unsigned long now = millis();
  if (now - lastMsg > 5000) {
    lastMsg = now;

    float t = carrier.Env.readTemperature();
    float h = carrier.Env.readHumidity();
    float p = carrier.Pressure.readPressure();

    String payload = "{\"temperature\": " + String(t) +
                     ", \"humidity\": " + String(h) +
                     ", \"pressure\": " + String(p) + "}";

    // MQTT
    mqttClient.publish("iot/mkr1010/sensors", payload.c_str());
    Serial.println("MQTT envoyé");

    // CoAP
    sendCoAP(payload);
  }
}
