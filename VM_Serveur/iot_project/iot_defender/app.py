from flask import Flask, render_template, jsonify, request
from influxdb import InfluxDBClient
from datetime import datetime

app = Flask(__name__)

# ===============================
# CONFIGURATION INFLUXDB
# ===============================

INFLUX_HOST = "localhost"
INFLUX_PORT = 8086
INFLUX_DB = "iotdata"

influx = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
influx.switch_database(INFLUX_DB)

# ===============================
# ROUTE PRINCIPALE
# ===============================

@app.route("/")
def dashboard():
    return render_template("dashboard.html")


# ===============================
# API DATA POUR LES GRAPHES
# ===============================

@app.route("/api/data")
def get_data():

    metric = request.args.get("metric", "temperature")

    def query_measurement(measurement):

        try:
            query = f"SELECT {metric} FROM {measurement} ORDER BY time DESC LIMIT 30"
            result = list(influx.query(query).get_points())

            timestamps = []
            values = []

            for r in result:
                if metric in r:
                    # Format HH:MM:SS propre
                    raw_time = r["time"]
                    dt = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
                    timestamps.append(dt.strftime("%H:%M:%S"))
                    values.append(r[metric])

            return {
                "timestamps": timestamps[::-1],
                "values": values[::-1]
            }

        except Exception as e:
            print("Erreur requête Influx :", e)
            return {
                "timestamps": [],
                "values": []
            }

    mqtt_data = query_measurement("sensors")
    coap_data = query_measurement("sensors_coap")

    # ===============================
    # LOGS SÉCURITÉ AVEC ÉTAT GLOBAL
    # ===============================

    try:
        logs_query = "SELECT * FROM security_logs ORDER BY time DESC LIMIT 50"
        logs_raw = list(influx.query(logs_query).get_points())

        logs = []
        critical_count = 0
        warning_count = 0
        ok_count = 0
        
        # Récupération de l'état global le plus récent
        global_severity = "OK"
        latest_log_message = ""

        for idx, log in enumerate(logs_raw):
            raw_time = log["time"]
            dt = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))

            severity = log.get("severity", "OK")
            log_message = log.get("log_message", "")
            
            # Le premier log (le plus récent) définit l'état global
            if idx == 0:
                global_severity = severity
                latest_log_message = log_message

            if severity == "CRITICAL":
                critical_count += 1
            elif severity == "WARNING":
                warning_count += 1
            else:
                ok_count += 1

            logs.append({
                "time": dt.strftime("%H:%M:%S"),
                "severity": severity,
                "delta_temperature": round(log.get("delta_temperature", 0), 2),
                "delta_humidity": round(log.get("delta_humidity", 0), 2),
                "delta_pressure": round(log.get("delta_pressure", 0), 2),
                "message": log_message,
                "attack_type": log.get("attack_type", "none")
            })

        # ===============================
        # CALCUL SCORE DE RÉSILIENCE
        # ===============================

        total = len(logs_raw)

        if total == 0:
            resilience_score = 100
        else:
            # Formule : les CRITICAL pèsent 3x plus, les WARNING 1x
            impact = (critical_count * 3 + warning_count)
            resilience_score = max(0, 100 - int((impact / total) * 100))

        # ===============================
        # STATISTIQUES ATTAQUES
        # ===============================
        
        attack_stats = {
            "total_attacks": critical_count + warning_count,
            "critical_attacks": critical_count,
            "warnings": warning_count,
            "ddos_detected": sum(1 for log in logs_raw if log.get("attack_type") == "ddos"),
            "mitm_detected": sum(1 for log in logs_raw if log.get("attack_type") == "mitm"),
            "injection_detected": sum(1 for log in logs_raw if log.get("attack_type") == "data_injection"),
            "corruption_detected": sum(1 for log in logs_raw if log.get("attack_type") == "data_corruption")
        }

    except Exception as e:
        print("Erreur logs :", e)
        import traceback
        traceback.print_exc()
        logs = []
        resilience_score = 100
        global_severity = "OK"
        latest_log_message = ""
        attack_stats = {
            "total_attacks": 0,
            "critical_attacks": 0,
            "warnings": 0,
            "ddos_detected": 0,
            "mitm_detected": 0,
            "injection_detected": 0,
            "corruption_detected": 0
        }

    return jsonify({
        "mqtt": mqtt_data,
        "coap": coap_data,
        "logs": logs,
        "resilience_score": resilience_score,
        "global_severity": global_severity,
        "latest_message": latest_log_message,
        "attack_stats": attack_stats
    })


# ===============================
# LANCEMENT SERVEUR
# ===============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
