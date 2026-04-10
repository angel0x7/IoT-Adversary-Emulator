import time
import json
import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient
from datetime import datetime



MQTT_BROKER = "172.20.10.4"
MQTT_PORT = 1883
MQTT_TOPIC_OUT = "iot/security/analysis"

INFLUX_HOST = "localhost"
INFLUX_PORT = 8086
INFLUX_DB = "iotdata"



DELTA_WARNING = 2.0
DELTA_CRITICAL = 5.0

INTERVAL_WARNING = 7
INTERVAL_CRITICAL = 15

MAX_MESSAGES_PER_MIN = 20

# Seuils pour valeurs aberrantes
TEMP_MIN = -50
TEMP_MAX = 100
HUMIDITY_MIN = 0
HUMIDITY_MAX = 100
PRESSURE_MIN = 80
PRESSURE_MAX = 150



def connect_mqtt():
    """Connexion MQTT avec gestion d'erreur"""
    try:
        client = mqtt.Client()
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        print(" Connecté au broker MQTT")
        return client
    except Exception as e:
        print(f" Erreur connexion MQTT: {e}")
        return None

def connect_influx():
    """Connexion InfluxDB avec gestion d'erreur"""
    try:
        client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
        client.switch_database(INFLUX_DB)
        print(" Connecté à InfluxDB")
        return client
    except Exception as e:
        print(f" Erreur connexion InfluxDB: {e}")
        return None

mqtt_client = connect_mqtt()
influx = connect_influx()

print(" Security Analyzer lancé et blindé...")

last_time = None
message_count = 0
start_minute = time.time()
consecutive_errors = 0



def validate_sensor_data(data, protocol_name):
    """Valide la cohérence des données capteur"""
    if not data:
        return False, f"Données {protocol_name} manquantes"
    
    try:
        temp = float(data.get("temperature", 0))
        hum = float(data.get("humidity", 0))
        pres = float(data.get("pressure", 0))
        
        errors = []
        
        if not (TEMP_MIN <= temp <= TEMP_MAX):
            errors.append(f"Température {protocol_name} hors limites: {temp}°C")
        
        if not (HUMIDITY_MIN <= hum <= HUMIDITY_MAX):
            errors.append(f"Humidité {protocol_name} invalide: {hum}%")
        
        if not (PRESSURE_MIN <= pres <= PRESSURE_MAX):
            errors.append(f"Pression {protocol_name} anormale: {pres}hPa")
        
        if errors:
            return False, " | ".join(errors)
        
        return True, "OK"
    
    except (ValueError, TypeError) as e:
        return False, f"Données {protocol_name} corrompues: {str(e)}"



def get_last_measurement(measurement):
    """Récupère la dernière mesure avec gestion d'erreur robuste"""
    if not influx:
        print(" InfluxDB non connecté")
        return None
    
    try:
        query = f"SELECT * FROM {measurement} ORDER BY time DESC LIMIT 1"
        result = list(influx.query(query).get_points())
        if result:
            return result[0]
    except Exception as e:
        print(f" Erreur requête Influx ({measurement}): {e}")
    
    return None



while True:
    try:
        current_time = time.time()
        
        # Reconnexion si nécessaire
        if not mqtt_client:
            mqtt_client = connect_mqtt()
            if not mqtt_client:
                time.sleep(5)
                continue
        
        if not influx:
            influx = connect_influx()
            if not influx:
                time.sleep(5)
                continue
        
        mqtt_data = get_last_measurement("sensors")
        coap_data = get_last_measurement("sensors_coap")
        
        logs = []
        severity = "OK"
        
    
        
        mqtt_valid, mqtt_msg = validate_sensor_data(mqtt_data, "MQTT")
        coap_valid, coap_msg = validate_sensor_data(coap_data, "CoAP")
        
        if not mqtt_valid:
            severity = "CRITICAL"
            logs.append(f" {mqtt_msg}")
        
        if not coap_valid:
            severity = "CRITICAL"
            logs.append(f" {coap_msg}")
        
        # Si les deux protocoles sont invalides, on skip cette itération
        if not mqtt_valid and not coap_valid:
            logs.append(" Aucun protocole ne fournit de données valides")
            
            # Enregistrement du log d'erreur
            json_body = [{
                "measurement": "security_logs",
                "fields": {
                    "delta_temperature": 0.0,
                    "delta_humidity": 0.0,
                    "delta_pressure": 0.0,
                    "severity": "CRITICAL",
                    "max_delta": 0.0,
                    "log_message": " | ".join(logs)
                },
                "tags": {
                    "attack_type": "data_corruption"
                }
            }]
            
            try:
                influx.write_points(json_body)
            except Exception as e:
                print(f" Erreur écriture InfluxDB: {e}")
            
            time.sleep(5)
            continue
        
        # Si seulement un est valide, on continue avec avertissement
        if not mqtt_valid or not coap_valid:
            if severity != "CRITICAL":
                severity = "WARNING"
        

        
        if mqtt_data and coap_data and mqtt_valid and coap_valid:
            try:
                delta_temp = abs(float(mqtt_data["temperature"]) - float(coap_data["temperature"]))
                delta_hum = abs(float(mqtt_data["humidity"]) - float(coap_data["humidity"]))
                delta_pres = abs(float(mqtt_data["pressure"]) - float(coap_data["pressure"]))
                
                max_delta = max(delta_temp, delta_hum, delta_pres)
                
                if max_delta > DELTA_CRITICAL:
                    severity = "CRITICAL"
                    logs.append(f" Incohérence critique MQTT vs CoAP (Δmax={max_delta:.2f})")
                    logs.append(f"   → ΔTemp={delta_temp:.2f}°C | ΔHum={delta_hum:.2f}% | ΔPres={delta_pres:.2f}hPa")
                
                elif max_delta > DELTA_WARNING:
                    if severity != "CRITICAL":
                        severity = "WARNING"
                    logs.append(f" Écart suspect MQTT vs CoAP (Δmax={max_delta:.2f})")
            
            except (ValueError, TypeError, KeyError) as e:
                severity = "CRITICAL"
                logs.append(f" Erreur calcul des deltas: {str(e)}")
                delta_temp = delta_hum = delta_pres = 0.0
                max_delta = 0.0
        else:
            delta_temp = delta_hum = delta_pres = 0.0
            max_delta = 0.0
        
    
        
        if last_time is not None:
            interval = current_time - last_time
            
            if interval > INTERVAL_CRITICAL:
                severity = "CRITICAL"
                logs.append(f" Délai anormal ({interval:.2f}s) → possible interception/DoS")
            
            elif interval > INTERVAL_WARNING:
                if severity != "CRITICAL":
                    severity = "WARNING"
                logs.append(f" Délai légèrement élevé ({interval:.2f}s)")
        
        last_time = current_time
        

        
        message_count += 1
        
        if current_time - start_minute >= 60:
            if message_count > MAX_MESSAGES_PER_MIN:
                severity = "CRITICAL"
                logs.append(f" Volume anormal ({message_count} msg/min) → possible DDoS")
            
            message_count = 0
            start_minute = current_time
   
        
        # (Optionnel : à implémenter si besoin de détecter des valeurs qui ne changent jamais)
        

        
        if not logs:
            logs.append(" Réseau opérationnel - Aucune anomalie détectée")
        

        
        payload = {
            "mqtt_temperature": mqtt_data.get("temperature", 0) if mqtt_data else 0,
            "coap_temperature": coap_data.get("temperature", 0) if coap_data else 0,
            "delta_temperature": delta_temp,
            "delta_humidity": delta_hum,
            "delta_pressure": delta_pres,
            "severity": severity,
            "logs": logs,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            mqtt_client.publish(MQTT_TOPIC_OUT, json.dumps(payload))
        except Exception as e:
            print(f" Erreur publication MQTT: {e}")
            mqtt_client = None  # Force reconnexion
        

        
        # Détermination du type d'attaque
        attack_type = "none"
        if "DDoS" in " ".join(logs):
            attack_type = "ddos"
        elif "interception" in " ".join(logs):
            attack_type = "mitm"
        elif "Incohérence" in " ".join(logs):
            attack_type = "data_injection"
        elif "corrompues" in " ".join(logs) or "invalide" in " ".join(logs):
            attack_type = "data_corruption"
        
        json_body = [{
            "measurement": "security_logs",
            "fields": {
                "delta_temperature": float(delta_temp),
                "delta_humidity": float(delta_hum),
                "delta_pressure": float(delta_pres),
                "severity": severity,
                "max_delta": float(max_delta),
                "log_message": " | ".join(logs)
            },
            "tags": {
                "attack_type": attack_type
            }
        }]
        
        try:
            influx.write_points(json_body)
            consecutive_errors = 0  # Reset compteur erreurs
        except Exception as e:
            print(f" Erreur écriture InfluxDB: {e}")
            consecutive_errors += 1
            if consecutive_errors > 10:
                influx = None  # Force reconnexion
        
        print(f" [{severity}] Analyse publiée - {len(logs)} log(s)")
        for log in logs:
            print(f"   {log}")
    
    except KeyboardInterrupt:
        print("\n Arrêt du Security Analyzer")
        break
    
    except Exception as e:
        print(f" Erreur critique dans la loop principale: {e}")
        import traceback
        traceback.print_exc()
        # Continue quand même
    
    time.sleep(5)

# Fermeture propre
if mqtt_client:
    mqtt_client.disconnect()
if influx:
    influx.close()
