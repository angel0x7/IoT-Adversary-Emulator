#include <WiFiS3.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>


const char* ssid = "Greg";
const char* password = "12345678";
const char* mqtt_server = "172.20.10.4";

WiFiClient wifiClient;
PubSubClient client(wifiClient);



float tempMin = 20.0;
float tempMax = 27.0;

float humMin = 30.0;
float humMax = 60.0;

float presMin = 95.0;
float presMax = 105.0;



void connectWiFi() {
  Serial.print("Connexion WiFi...");
  while (WiFi.begin(ssid, password) != WL_CONNECTED) {
    delay(2000);
    Serial.print(".");
  }

  Serial.println("\nWiFi connecté !");
  Serial.print("IP UNO R4 : ");
  Serial.println(WiFi.localIP());
}



void reconnect() {
  while (!client.connected()) {
    Serial.print("Connexion MQTT...");
    if (client.connect("UNO_R4_SECURITY")) {
      Serial.println("OK");

      client.subscribe("iot/mkr1010/sensors");
      client.subscribe("iot/security/analysis");

      Serial.println("Abonné aux topics sécurité");
    } else {
      Serial.print("Erreur MQTT : ");
      Serial.println(client.state());
      delay(3000);
    }
  }
}



void callback(char* topic, byte* payload, unsigned int length) {

  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, message);

  if (error) {
    Serial.println("Erreur JSON");
    return;
  }



  if (String(topic) == "iot/mkr1010/sensors") {

    float temp = doc["temperature"];
    float hum = doc["humidity"];
    float pres = doc["pressure"];

    bool temp_high = temp > tempMax;
    bool temp_low  = temp < tempMin;

    bool hum_high = hum > humMax;
    bool hum_low  = hum < humMin;

    bool pres_high = pres > presMax;
    bool pres_low  = pres < presMin;

    Serial.println("\n=== Analyse locale UNO ===");
    Serial.print("Temp: "); Serial.println(temp);
    Serial.print("Hum: "); Serial.println(hum);
    Serial.print("Pres: "); Serial.println(pres);

    StaticJsonDocument<256> stateDoc;

    stateDoc["temp_high"] = temp_high;
    stateDoc["temp_low"] = temp_low;
    stateDoc["hum_high"] = hum_high;
    stateDoc["hum_low"] = hum_low;
    stateDoc["pres_high"] = pres_high;
    stateDoc["pres_low"] = pres_low;

    String statePayload;
    serializeJson(stateDoc, statePayload);

    client.publish("iot/unoR4wifi/sensors_state", statePayload.c_str());

    Serial.println("Etat capteurs publié");
  }



  if (String(topic) == "iot/security/analysis") {

    String severity = doc["severity"];

    Serial.println("\n=== Analyse Sécurité Réseau ===");

    if (severity == "CRITICAL") {
      Serial.println(" ALERTE CRITIQUE !");
    }
    else if (severity == "WARNING") {
      Serial.println(" Avertissement sécurité");
    }
    else {
      Serial.println(" Réseau cohérent");
    }

    // Création log complet
    StaticJsonDocument<256> logDoc;
    logDoc["severity"] = severity;
    logDoc["delta_temperature"] = doc["delta_temperature"];
    logDoc["delta_humidity"] = doc["delta_humidity"];
    logDoc["delta_pressure"] = doc["delta_pressure"];

    String logPayload;
    serializeJson(logDoc, logPayload);

    client.publish("iot/security/logs", logPayload.c_str());

    Serial.println("Log sécurité publié");
  }
}



void setup() {
  Serial.begin(9600);
  while (!Serial);

  connectWiFi();

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}



void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}
