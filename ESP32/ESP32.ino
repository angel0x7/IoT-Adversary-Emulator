#include <WiFi.h>
#include <WiFiManager.h> // Pour la connexion facile à la Livebox
#include <PubSubClient.h> // Pour envoyer les données au Raspberry Pi

// ================= CONFIGURATION RÉSEAU OT (VLAN 10/20) =================
// C'est le réseau que l'ESP32 va CRÉER pour vos capteurs (MKR 1010, etc.)
const char *ssid_AP = "Reseau_OT_Segment";
const char *password_AP = "12345678"; // Mot de passe pour vos capteurs
IPAddress ap_local_ip(192, 168, 2, 1);    // L'ESP32 sera la passerelle 192.168.2.1
IPAddress ap_subnet(255, 255, 255, 0);

// ================= CONFIGURATION SCADA (VLAN 30) =================
// Adresse IP de votre Raspberry Pi (Broker MQTT) sur le réseau Livebox
// !!! À MODIFIER SELON VOTRE CONFIGURATION !!!
IPAddress mqtt_server_ip(192, 168, 1, 50); 
const int mqtt_port = 1883; 

// Topic MQTT où les données seront publiées
const char *mqtt_topic_out = "ot/vlan10/mkr_carrier_data"; 
const char *mqtt_client_id = "ESP32_OT_Gateway"; 

// ================= OBJETS GLOBAUX =================
// Serveur TCP pour écouter les capteurs sur le port 8080
WiFiServer ot_server(8080);

// Clients pour la connexion MQTT
WiFiClient espClient; 
PubSubClient mqtt_client(espClient); 

// Gestionnaire de connexion Wi-Fi (Provisioning)
WiFiManager wm;

// ================= FONCTIONS AUXILIAIRES =================

// Callback pour indiquer que le mode configuration (Portail Captif) est actif
void configModeCallback (WiFiManager *myWiFiManager) {
  Serial.println("\n--- MODE CONFIGURATION ACTIVÉ ---");
  Serial.println("L'ESP32 n'arrive pas à se connecter à la Livebox.");
  Serial.println("Veuillez vous connecter au Wi-Fi : " + myWiFiManager->getConfigPortalSSID());
  Serial.println("Puis ouvrez : http://" + WiFi.softAPIP().toString());
  Serial.println("---------------------------------");
}

// Fonction pour gérer la reconnexion MQTT automatique
void reconnectMQTT() {
  // Tant qu'on n'est pas connecté au broker
  while (!mqtt_client.connected()) {
    Serial.print("Tentative de connexion au Broker MQTT (Raspberry Pi)...");
    
    // Tentative de connexion avec l'ID défini
    if (mqtt_client.connect(mqtt_client_id)) {
      Serial.println("CONNECTÉ !");
    } else {
      Serial.print("Échec (Erreur rc=");
      Serial.print(mqtt_client.state());
      Serial.println("). Nouvelle tentative dans 5s...");
      delay(5000);
    }
  }
}

// ================= SETUP (DÉMARRAGE) =================
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n\n=== DÉMARRAGE PASSERELLE OT/SCADA (ESP32) ===");

  // 1. Activer le mode double : Point d'Accès + Station
  WiFi.mode(WIFI_AP_STA);
  Serial.println("1. Mode Double Interface (AP+STA) activé.");

  // 2. Gestion de la connexion à la Livebox (Interface STA)
  // Si l'ESP32 ne connait pas le wifi, il lance un portail "ESP32_Config_OT"
  wm.setAPCallback(configModeCallback);
  // Timeout de 3 minutes pour la config, sinon il continue
  wm.setConfigPortalTimeout(180); 
  
  Serial.println("2. Connexion à la Livebox en cours...");
  bool res = wm.autoConnect("ESP32_Config_OT"); 

  if(!res) {
    Serial.println("   ATTENTION : Pas de connexion Livebox (Mode autonome ou échec).");
  } else {
    Serial.println("   SUCCÈS : Connecté à la Livebox !");
    Serial.print("   IP WAN (Vers SCADA) : ");
    Serial.println(WiFi.localIP());
  }

  // 3. Configuration du Réseau OT (Interface AP)
  Serial.println("3. Démarrage du Réseau OT (192.168.2.x)...");
  
  // Forcer l'IP statique 192.168.2.1
  if (!WiFi.softAPConfig(ap_local_ip, ap_local_ip, ap_subnet)) {
    Serial.println("   ERREUR : Impossible de configurer l'IP AP !");
  }

  // Lancer le réseau Wi-Fi
  if (WiFi.softAP(ssid_AP, password_AP)) {
    Serial.print("   SUCCÈS : Réseau OT créé : ");
    Serial.println(ssid_AP);
    Serial.print("   IP Passerelle OT : ");
    Serial.println(WiFi.softAPIP());
  } else {
    Serial.println("   ERREUR : Échec création AP.");
  }

  // 4. Démarrage du Serveur de Données (Pour recevoir du MKR 1010)
  ot_server.begin();
  Serial.println("4. Serveur TCP écoute sur le port 8080.");

  // 5. Configuration MQTT
  mqtt_client.setServer(mqtt_server_ip, mqtt_port);
  Serial.println("5. Client MQTT configuré.");

  Serial.println("=== SYSTÈME PRÊT ===\n");
}

// ================= LOOP (BOUCLE PRINCIPALE) =================
void loop() {
  
  // --- PARTIE 1 : GESTION MQTT (Côté Livebox/SCADA) ---
  // On ne tente MQTT que si le WiFi Livebox est connecté
  if (WiFi.status() == WL_CONNECTED) {
    if (!mqtt_client.connected()) {
      reconnectMQTT();
    }
    mqtt_client.loop(); // Important pour maintenir la connexion active
  }

  // --- PARTIE 2 : GESTION DES CAPTEURS (Côté OT) ---
  // Vérifier si un client (MKR 1010) envoie des données
  WiFiClient client_ot = ot_server.available();

  if (client_ot) {
    Serial.println("\n[OT] Nouveau client connecté (MKR 1010).");

    if (client_ot.connected()) {
      
      // Petite pause pour être sûr que tout le message est arrivé
      unsigned long start_time = millis();
      while (!client_ot.available() && (millis() - start_time < 200)) {
        delay(1);
      }

      // Lecture du message envoyé par le MKR 1010
      // Le MKR envoie une ligne finissant par '\n'
      String data_recue = client_ot.readStringUntil('\n');
      data_recue.trim(); // Enlever les espaces inutiles

      if (data_recue.length() > 0) {
        Serial.print("[OT] Données reçues : ");
        Serial.println(data_recue);

        // --- PARTIE 3 : LE RELAIS (OT -> SCADA) ---
        bool envoi_succes = false;

        // Si MQTT est connecté, on relaie
        if (mqtt_client.connected()) {
          Serial.print("[RELAIS] Envoi vers Raspberry Pi... ");
          
          if (mqtt_client.publish(mqtt_topic_out, data_recue.c_str())) {
            Serial.println("OK !");
            envoi_succes = true;
          } else {
            Serial.println("ÉCHEC (Erreur Broker).");
          }
        } else {
          Serial.println("[RELAIS] Impossible : MQTT non connecté.");
        }

        // --- PARTIE 4 : RÉPONSE AU CAPTEUR (ACK) ---
        if (envoi_succes) {
          client_ot.println("ACK_OK"); // Tout s'est bien passé
        } else {
          client_ot.println("ACK_FAIL"); // Problème côté MQTT
        }
        
      }
    }
    
    // Fermer la connexion avec le capteur
    client_ot.stop();
    Serial.println("[OT] Client déconnecté.");
  }
}