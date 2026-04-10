# api_server.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import uvicorn
import time
import os
from typing import List
from analysis.sniffer import discover_iot_services

app = FastAPI()
# Variable globale pour capturer la boucle d'événements principale
main_loop = None

# Autorisation du CORS pour le dashboard local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    """Gère les clients connectés au dashboard via WebSocket"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
from config import settings

manager = ConnectionManager()

def on_mqtt_message(client, userdata, msg):
    """Callback lors de la réception d'un message MQTT"""
    try:
        payload = json.loads(msg.payload.decode())
        topic = msg.topic
        
        # Structure du message pour le Frontend
        broadcast_data = {
            "type": "telemetry",
            "topic": topic,
            "data": payload,
            "timestamp": time.time()
        }
        
        # Correction : Utilisation de la boucle principale capturée au démarrage
        if main_loop and main_loop.is_running():
            asyncio.run_coroutine_threadsafe(manager.broadcast(broadcast_data), main_loop)
        
    except Exception as e:
        pass # Silencieux pour éviter de polluer la console

# Configuration du client MQTT d'écoute pour l'API
mqtt_listener = mqtt.Client(CallbackAPIVersion.VERSION1, "API_DASHBOARD_LISTENER")
mqtt_listener.username_pw_set(settings.MQTT_CONFIG["user"], settings.MQTT_CONFIG["pw"])
mqtt_listener.on_message = on_mqtt_message

def start_mqtt():
    """Démarre l'écoute MQTT en arrière-plan"""
    if not settings.MQTT_CONFIG["broker"]:
        print("[*] API : Recherche du Broker sur le réseau...")
        services = discover_iot_services(settings.NETWORK_PREFIX)
        for ip, service in services:
            if service == "MQTT":
                settings.MQTT_CONFIG["broker"] = ip
                break
    
    if settings.MQTT_CONFIG["broker"]:
        try:
            mqtt_listener.connect(settings.MQTT_CONFIG["broker"], 1883)
            mqtt_listener.subscribe("#") 
            mqtt_listener.loop_start()
            print(f"[*] API connectée au Broker MQTT : {settings.MQTT_CONFIG['broker']}")
        except Exception as e:
            print(f"[!] API : Erreur connexion Broker : {e}")
    else:
        print("[!] API : Aucun Broker trouvé.")

@app.on_event("startup")
async def startup_event():
    global main_loop
    main_loop = asyncio.get_running_loop() # Capture la boucle FastAPI
    import threading
    threading.Thread(target=start_mqtt, daemon=True).start()

@app.get("/")
async def read_index():
    """Sert la page d'accueil du dashboard"""
    return FileResponse('index.html')

@app.get("/status")
async def get_status():
    return {
        "status": "online", 
        "broker": settings.MQTT_CONFIG["broker"],
        "message": "IoT Cyber-Lab API is Running"
    }

@app.post("/command")
async def send_command(payload: dict):
    if settings.MQTT_CONFIG["broker"]:
        try:
            topic = settings.MQTT_CONFIG["topic_c2"]
            mqtt_listener.publish(topic, json.dumps(payload))
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    return {"status": "error"}

@app.post("/spawn")
async def spawn_bots(data: dict):
    if settings.MQTT_CONFIG["broker"]:
        try:
            payload = {
                "action": "SPAWN", 
                "count": data.get("count", 1),
                "name": data.get("name") # Nouveau : support d'un nom spécifique
            }
            mqtt_listener.publish("botnet/manage", json.dumps(payload))
            return {"status": "success"}
        except: return {"status": "error"}
    return {"status": "error"}

@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/log")
async def log_event(data: dict):
    if main_loop and main_loop.is_running():
        await manager.broadcast({"type": "log", "data": data, "timestamp": time.time()})
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
