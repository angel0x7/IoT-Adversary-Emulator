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
    # LOGS SÉCURITÉ
    # ===============================

    try:
        logs_query = "SELECT * FROM security_logs ORDER BY time DESC LIMIT 50"
        logs_raw = list(influx.query(logs_query).get_points())

        logs = []
        critical_count = 0
        warning_count = 0

        for log in logs_raw:
            raw_time = log["time"]
            dt = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))

            severity = log.get("severity", "OK")

            if severity == "CRITICAL":
                critical_count += 1
            elif severity == "WARNING":
                warning_count += 1

            logs.append({
                "time": dt.strftime("%H:%M:%S"),
                "severity": severity,
                "delta_temperature": log.get("delta_temperature", 0),
                "delta_humidity": log.get("delta_humidity", 0),
                "delta_pressure": log.get("delta_pressure", 0)
            })

        # ===============================
        # CALCUL SCORE DE RÉSILIENCE
        # ===============================

        total = len(logs_raw)

        if total == 0:
            resilience_score = 100
        else:
            impact = (critical_count * 2 + warning_count)
            resilience_score = max(0, 100 - int((impact / total) * 100))

    except Exception as e:
        print("Erreur logs :", e)
        logs = []
        resilience_score = 100

    return jsonify({
        "mqtt": mqtt_data,
        "coap": coap_data,
        "logs": logs,
        "resilience_score": resilience_score
    })


# ===============================
# LANCEMENT SERVEUR
# ===============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
