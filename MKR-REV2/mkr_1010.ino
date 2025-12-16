#include <WiFiNINA.h> 
#include <Arduino_MKRIoTCarrier.h> 

// Le Carrier doit être initialisé avant tout usage de ses périphériques
MKRIoTCarrier carrier; 

// --- Configuration du Réseau OT (AP de l'ESP32) ---
const char* ap_ssid = "Reseau_OT_Segment"; 
const char* ap_password = "12345678"; 
// L'adresse IP statique de l'ESP32 en mode AP
const IPAddress esp32_server_ip(192, 168, 2, 1); 
const int ot_server_port = 8080; 

WiFiClient client;

// --- Variables d'état et de données ---
float current_temperature = 0.0;
float current_humidity = 0.0;
float current_iaq = 0.0;
float current_iaq_static = 0.0;
String network_status = "INITIALISATION...";

// --- Fonction utilitaire pour centrer le texte sur l'écran ---
int centerText(const String& text, uint8_t size) {
  int textLength = text.length();
  int pixelWidth = textLength * (6 * size); 
  return (carrier.display.width() - pixelWidth) / 2;
}


// --- Fonction de connexion Wi-Fi au réseau OT (AP de l'ESP32) ---
void connectWiFi() {
  network_status = "CONNEXION OT...";
  WiFi.begin(ap_ssid, ap_password);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    attempts++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    network_status = "OT CONNECTE: " + String(WiFi.localIP()[3]);
  } else {
    network_status = "CONNEXION ECHOUÉE";
  }
}

// --- Fonction de mise à jour de l'affichage local ---
void updateDisplay() {
  carrier.display.fillScreen(ST77XX_BLACK);
  carrier.display.setTextColor(ST77XX_WHITE);
  carrier.display.setTextWrap(false);

  // Affichage du statut réseau
  carrier.display.setTextSize(1);
  carrier.display.setTextColor(ST77XX_YELLOW);
  String statusLine = "STATUT: " + network_status;
  carrier.display.setCursor(centerText(statusLine, 1), 5);
  carrier.display.println(statusLine);
  carrier.display.drawFastHLine(0, 18, carrier.display.width(), ST77XX_BLUE);

  // Affichage des données de capteurs
  carrier.display.setTextSize(2);
  carrier.display.setTextColor(ST77XX_CYAN);
  String tempLine = "Temp: " + String(current_temperature, 1) + " C";
  carrier.display.setCursor(centerText(tempLine, 2), 30);
  carrier.display.println(tempLine);

  carrier.display.setTextSize(2);
  carrier.display.setTextColor(ST77XX_GREEN);
  String humLine = "Hum: " + String(current_humidity, 0) + " %";
  carrier.display.setCursor(centerText(humLine, 2), 60);
  carrier.display.println(humLine);

  carrier.display.setTextSize(2);
  carrier.display.setTextColor(ST77XX_MAGENTA);
  String iaqLine = "IAQ: " + String(current_iaq, 0);
  carrier.display.setCursor(centerText(iaqLine, 2), 90);
  carrier.display.println(iaqLine);
  
  carrier.display.setTextSize(1);
  carrier.display.setTextColor(ST77XX_RED);
  String iaqsLine = "IAQ STATIQUE: " + String(current_iaq_static, 0);
  carrier.display.setCursor(centerText(iaqsLine, 1), 125);
  carrier.display.println(iaqsLine);
}

void setup() {
  Serial.begin(9600);
  Serial.println(F("--- MKR 1010: Capteur OT (Client TCP) ---"));

  // Initialisation de la Carrier (sans le boîtier)
  carrier.noCase();
  if (carrier.begin()) {
    Serial.println("Carrier IoT Rev 2 OK.");
    carrier.AirQuality.begin();
    carrier.display.fillScreen(ST77XX_BLACK);
  } else {
    Serial.println("ERREUR: Echec de l'initialisation de la Carrier.");
  }

  // Tente la première connexion au réseau OT
  connectWiFi();
}

void loop() {
  // A. Vérification de la connexion et reconnexion si nécessaire
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
    if (WiFi.status() != WL_CONNECTED) {
      network_status = "DECONNEXION";
      updateDisplay();
      delay(5000); // Attend 5s avant de réessayer
      return;
    }
  }
  
  // B. LECTURE DES CAPTEURS
  current_temperature = carrier.Env.readTemperature();
  current_humidity = carrier.Env.readHumidity();
  current_iaq_static = carrier.AirQuality.readStaticIAQ();
  current_iaq = carrier.AirQuality.readIAQ();
  
  // C. CONSOLIDATION ET AFFICHAGE LOCAL
  network_status = "OT CONNECTE: " + String(WiFi.localIP()[3]);
  updateDisplay(); 

  // D. PRÉPARATION DU MESSAGE CONSOLIDÉ
  // Format : T:24.5|H:55.2|IAQ:120|IAQS:110
  String consolidatedMessage = "T:" + String(current_temperature, 1) + 
                               "|H:" + String(current_humidity, 1) +
                               "|IAQ:" + String(current_iaq, 0) +
                               "|IAQS:" + String(current_iaq_static, 0);
  
  // E. ENVOI DES DONNÉES PAR TCP à la Passerelle ESP32
  if (client.connect(esp32_server_ip, ot_server_port)) {
    Serial.print("Envoi: ");
    Serial.println(consolidatedMessage);
    
    // Envoi du message suivi d'un saut de ligne
    client.println(consolidatedMessage); 
    
    // F. Lecture de la réponse (ACK) de l'ESP32
    long start_wait = millis();
    bool ack_received = false;
    while (client.connected() && (millis() - start_wait < 1000)) { // Attendre max 1s
        if (client.available()) {
            String response = client.readStringUntil('\n');
            response.trim();
            if (response == "ACK_OK") {
                Serial.println("✅ Passerelle ACK_OK: Donnee relayee.");
                ack_received = true;
            } else if (response.startsWith("ACK_FAIL")) {
                Serial.println("❌ Passerelle ACK_FAIL: " + response);
                ack_received = true;
            }
            break;
        }
    }
    
    if (!ack_received) {
        Serial.println("Timeout: Pas d'acquittement recu.");
    }
    
    client.stop(); 
  } else {
    Serial.println("❌ Echec de connexion au serveur ESP32.");
  }
  
  delay(15000); // Envoi toutes les 15 secondes
}