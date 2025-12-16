#include <WiFi.h>

/* === Configuration AP === */
const char* ap_ssid     = "Reseau_OT_Segment";
const char* ap_password = "12345678";

IPAddress local_ip(192,168,2,1);
IPAddress gateway(192,168,2,1);
IPAddress subnet(255,255,255,0);

void setup() {
  Serial.begin(115200);

  // Configurer l’ESP32 comme AP avec IP statique
  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(local_ip, gateway, subnet);
  WiFi.softAP(ap_ssid, ap_password);

  Serial.println("=== ESP32 AP démarré ===");
  Serial.print("IP AP : ");
  Serial.println(WiFi.softAPIP());
}

void loop() {
  // Rien à faire, l’ESP32 fournit juste le Wi-Fi
}
