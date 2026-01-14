#include <WiFi.h>

// Paramètres du réseau
const char* ssid = "Ma_Box_Isolee";
const char* password = "12345678"; // 8 caractères min.

// Configuration IP personnalisée pour renforcer l'isolation
IPAddress local_IP(192, 168, 10, 1);  // Adresse de votre "Box" ESP32
IPAddress gateway(192, 168, 10, 1);   // Elle est sa propre passerelle
IPAddress subnet(255, 255, 255, 0);   // Masque de sous-réseau standard

void setup() {
  Serial.begin(115200);

  Serial.println("\n--- Initialisation du réseau isolé ---");

  // 1. Désactiver le mode Station (pour éviter qu'elle cherche un autre Wi-Fi)
  WiFi.mode(WIFI_AP);

  // 2. Configurer les paramètres IP avant de démarrer le point d'accès
  WiFi.softAPConfig(local_IP, gateway, subnet);

  // 3. Démarrer le point d'accès
  // Paramètres : SSID, Password, Canal (1-13), Hidden (0/1), Max_connections
  if (WiFi.softAP(ssid, password, 1, 0, 4)) {
    Serial.println("Point d'accès activé !");
  } else {
    Serial.println("Échec de la configuration.");
  }

  // Affichage des infos
  IPAddress IP = WiFi.softAPIP();
  Serial.print("Nom du réseau (SSID) : ");
  Serial.println(ssid);
  Serial.print("Adresse IP de la Box ESP32 : ");
  Serial.println(IP);
}

void loop() {
  // Afficher le nombre d'appareils connectés (ex: votre MKR 1010)
  Serial.printf("Appareils connectés : %d\n", WiFi.softAPgetStationNum());
  delay(5000); 
}
