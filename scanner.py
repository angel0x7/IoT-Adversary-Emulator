import re
import socket
import subprocess
import time
import netifaces
import ipaddress
import os
from typing import Dict
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion


class SecurityScanner:
    """Scanner de sécurité avec auto-détection complète"""

    def __init__(self, config: Dict):
        self.config = config
        self.quick_mode = config.get('quick_mode', False)
        self.verbose = config.get('verbose', False)

        self.interface = None
        self.local_ip = None
        self.network_range = None
        self.devices = []

        self.broker_ip = None
        self.broker_port = 1883

        self.topics = []
        self.open_services = {}
        self.coap_servers = []

        # credentials à tester
        self.common_credentials = [
            ("mkr1010", "admin"),
            ("unoR4", "admin"),
            ("analyzer", "admin"),
            ("dashboard", "admin"),
            ("iotuser", "admin"),
            ("admin", "admin"),
        ]

        self.mqtt_user = None
        self.mqtt_pass = None

    def run_full_scan(self) -> Dict:
        """Scan complet avec auto-détection"""

        if not self._detect_network():
            raise Exception("Network detection failed")

        self._scan_devices()
        self._find_mqtt_broker()

        if self.broker_ip:
            self._discover_mqtt_topics()

        self._scan_services()
        self._detect_coap_servers()

        return {
            'interface': self.interface,
            'local_ip': self.local_ip,
            'network': self.network_range,
            'devices': self.devices,
            'broker_ip': self.broker_ip,
            'broker_port': self.broker_port,
            'topics': self.topics,
            'open_services': self.open_services,
            'coap_servers': self.coap_servers,
        }

    def _try_mqtt_credentials(self, ip):

        for username, password in self.common_credentials:

            try:

                print(f"[SCAN] Trying {username}/{password}")

                client = mqtt.Client(
                    client_id="scanner_auth",
                    callback_api_version=CallbackAPIVersion.VERSION2
                )

                client.username_pw_set(username, password)

                client.connect(ip, self.broker_port, 5)
                client.loop_start()

                time.sleep(1)

                client.loop_stop()
                client.disconnect()

                print(f"[+] Valid MQTT credentials found: {username}/{password}")

                self.mqtt_user = username
                self.mqtt_pass = password

                return True

            except Exception:
                continue

        return False

    def _detect_network(self) -> bool:
        print("[SCAN] Detecting network configuration...")

        if self.config.get('interface'):
            self.interface = self.config['interface']

        else:
            for iface in netifaces.interfaces():

                if iface == 'lo':
                    continue

                addrs = netifaces.ifaddresses(iface)

                if netifaces.AF_INET in addrs:
                    ipv4_info = addrs[netifaces.AF_INET][0]
                    ip = ipv4_info['addr']

                    if ip.startswith('127.'):
                        continue

                    try:
                        result = subprocess.run(
                            ['ping', '-c', '1', '-W', '1', '-I', iface, '8.8.8.8'],
                            capture_output=True,
                            timeout=2
                        )

                        if result.returncode == 0:
                            self.interface = iface
                            break

                    except:
                        continue

        if not self.interface:
            print("[-] No active interface found")
            return False

        try:
            addrs = netifaces.ifaddresses(self.interface)
            ipv4_info = addrs[netifaces.AF_INET][0]

            self.local_ip = ipv4_info['addr']
            netmask = ipv4_info['netmask']

            network = ipaddress.IPv4Network(
                f"{self.local_ip}/{netmask}", strict=False
            )

            self.network_range = str(network)

            print(f"[+] Interface: {self.interface}")
            print(f"[+] Local IP: {self.local_ip}")
            print(f"[+] Network: {self.network_range}")

            return True

        except Exception as e:
            print(f"[-] Network detection error: {e}")
            return False

    def _scan_devices(self):

        print(f"\n[SCAN] Scanning network: {self.network_range}")

        timeout = 20 if self.quick_mode else 60

        try:
            result = subprocess.run(
                ['sudo', 'nmap', '-sn', '-T4', self.network_range],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            ips = re.findall(
                r'Nmap scan report for .*?(\d+\.\d+\.\d+\.\d+)',
                result.stdout
            )

            self.devices = [ip for ip in ips if ip != self.local_ip]

            if self.devices:

                print(f"[+] Found {len(self.devices)} device(s)")

                for ip in self.devices:
                    print(f"    - {ip}")

                return

        except Exception as e:
            if self.verbose:
                print(f"[!] nmap scan failed: {e}")

        try:

            result = subprocess.run(
                ['sudo', 'arp-scan', '-l', '-I', self.interface],
                capture_output=True,
                text=True,
                timeout=15
            )

            ips = re.findall(
                r'(\d+\.\d+\.\d+\.\d+)\s+[\da-f:]+',
                result.stdout
            )

            self.devices = [ip for ip in ips if ip != self.local_ip]

            if self.devices:
                print(f"[+] Found {len(self.devices)} device(s) (arp-scan)")

        except Exception as e:
            if self.verbose:
                print(f"[!] arp-scan failed: {e}")

    def _find_mqtt_broker(self):

        print("\n[SCAN] Looking for MQTT broker...")

        for ip in self.devices:

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)

            result = sock.connect_ex((ip, 1883))
            sock.close()

            if result == 0:

                print(f"[SCAN] Port 1883 open on {ip}")

                try:

                    client = mqtt.Client(
                        client_id="scanner",
                        callback_api_version=CallbackAPIVersion.VERSION2,
                        clean_session=True
                    )

                    client.connect(ip, 1883, 5)
                    client.disconnect()

                    self.broker_ip = ip
                    print(f"[+] MQTT Broker (no auth): {ip}:1883")
                    return

                except Exception:

                    if self._try_mqtt_credentials(ip):

                        self.broker_ip = ip
                        return

        print("[-] No MQTT broker found")

    def _discover_mqtt_topics(self):

        print(f"\n[SCAN] Discovering MQTT topics on {self.broker_ip}...")

        discovered_topics = set()

        if not discovered_topics:
            print("[SCAN] Using active MQTT subscription...")
            discovered_topics = self._active_mqtt_discovery()

        self.topics = list(discovered_topics)

        print(f"[+] Discovered {len(self.topics)} topic(s): {self.topics}")
        
    def _active_mqtt_discovery(self) -> set:

        discovered = set()

        for username, password in self.common_credentials:

            print(f"[SCAN] Trying MQTT credentials {username}/{password}")

            try:

                client = mqtt.Client(
                    client_id=f"scanner_{username}",
                    callback_api_version=CallbackAPIVersion.VERSION2
                )

                client.username_pw_set(username, password)

                connected = False

                def on_connect(client, userdata, flags, reasonCode, properties):

                    nonlocal connected

                    if reasonCode == 0:
                        connected = True
                        print(f"[+] Auth success with {username}/{password}")
                        client.subscribe("#")

                    else:
                        print(f"[-] MQTT connection failed: {reasonCode}")

                def on_message(client, userdata, msg):

                    topic = msg.topic

                    if topic.startswith("$"):
                        return

                    if topic not in discovered:

                        discovered.add(topic)

                        try:
                            payload = msg.payload.decode()
                        except:
                            payload = str(msg.payload)

                        print(f"[+] Topic discovered: {topic}")
                        print(f"    Payload: {payload}")

                client.on_connect = on_connect
                client.on_message = on_message

                client.connect(self.broker_ip, self.broker_port, 5)

                client.loop_start()

                timeout = time.time() + 5

                while not connected and time.time() < timeout:
                    time.sleep(0.1)

                if not connected:
                    client.loop_stop()
                    client.disconnect()
                    continue

                self.mqtt_user = username
                self.mqtt_pass = password

                duration = 15 if self.quick_mode else 30
                print(f"[SCAN] Listening for {duration}s...")

                time.sleep(duration)

                client.loop_stop()
                client.disconnect()

                break

            except Exception as e:

                if self.verbose:
                    print(f"[!] MQTT error: {e}")

        return discovered

    def _scan_services(self):

        print("\n[SCAN] Scanning services...")

        common_ports = [21, 22, 23, 80, 443, 1883, 5683, 8080, 8883]

        for ip in self.devices:

            open_ports = []

            for port in common_ports:

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)

                result = sock.connect_ex((ip, port))
                sock.close()

                if result == 0:
                    open_ports.append(port)

            if open_ports:

                self.open_services[ip] = open_ports

                print(f"    {ip}: {open_ports}")

    def _detect_coap_servers(self):

        print("\n[SCAN] Looking for CoAP servers...")

        for ip in self.devices:

            if 5683 in self.open_services.get(ip, []):

                self.coap_servers.append(ip)

                print(f"    [+] CoAP server: {ip}:5683")
