#include <WiFi.h>

/* ---------- AP (réseau isolé) ---------- */
const char* ap_ssid = "Ma_Box_Isolee";
const char* ap_password = "12345678";

IPAddress ap_ip(192, 168, 10, 1);
IPAddress ap_gateway(192, 168, 10, 1);
IPAddress ap_subnet(255, 255, 255, 0);

/* ---------- STA (Internet) ---------- */
const char* sta_ssid = "iPhone de gregmarchal (2)";
const char* sta_password = "gerg2004";

/* ---------- Paramètres ---------- */
const uint32_t STA_TIMEOUT_MS = 15000;
uint32_t lastReconnectAttempt = 0;
const uint32_t RECONNECT_INTERVAL_MS = 10000;

/* ---------- Fonctions ---------- */

void startAP() {
  WiFi.softAPConfig(ap_ip, ap_gateway, ap_subnet);
  WiFi.softAP(ap_ssid, ap_password);
  Serial.print("AP actif | IP : ");
  Serial.println(WiFi.softAPIP());
}

bool connectSTA() {
  Serial.print("Connexion STA à ");
  Serial.println(sta_ssid);

  WiFi.disconnect(true);
  WiFi.begin(sta_ssid, sta_password);

  uint32_t start = millis();

  while (WiFi.status() != WL_CONNECTED) {
    if (millis() - start > STA_TIMEOUT_MS) {
      Serial.println("STA timeout");
      return false;
    }
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nSTA connecté");
  Serial.print("IP STA : ");
  Serial.println(WiFi.localIP());
  return true;
}

void printSTAError(wl_status_t status) {
  Serial.print("Erreur STA : ");
  switch (status) {
    case WL_NO_SSID_AVAIL:   Serial.println("SSID introuvable"); break;
    case WL_CONNECT_FAILED: Serial.println("Mot de passe incorrect"); break;
    case WL_CONNECTION_LOST:Serial.println("Connexion perdue"); break;
    case WL_DISCONNECTED:   Serial.println("Déconnecté"); break;
    default:                Serial.println("Erreur inconnue"); break;
  }
}

/* ---------- Setup ---------- */

void setup() {
  Serial.begin(115200);
  Serial.println("\n--- Démarrage réseau sécurisé ---");

  WiFi.mode(WIFI_AP_STA);

  startAP();

  if (!connectSTA()) {
    printSTAError(WiFi.status());
  }
}

/* ---------- Loop ---------- */

void loop() {
  // Surveillance STA
  if (WiFi.status() != WL_CONNECTED) {
    if (millis() - lastReconnectAttempt > RECONNECT_INTERVAL_MS) {
      lastReconnectAttempt = millis();
      Serial.println("Tentative de reconnexion STA...");
      if (!connectSTA()) {
        printSTAError(WiFi.status());
      }
    }
  }

  Serial.printf("Clients AP : %d | STA : %s\n",
                WiFi.softAPgetStationNum(),
                WiFi.status() == WL_CONNECTED ? "OK" : "HS");

  delay(5000);
}
