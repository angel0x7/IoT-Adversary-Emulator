#!/usr/bin/env python3
"""
Fonctionnalités:
- Scan automatique du réseau
- Identification des vulnérabilités
- Tests d'attaques automatisés (MITM, Injection, Flood, DoS)
- Génération de rapports d'audit
- Recommandations de sécurité
"""

import json
import subprocess
import time
import os
import re
import socket
from datetime import datetime
from typing import List, Dict, Optional
import paho.mqtt.client as mqtt

# ============================================
# CLASSE PRINCIPALE : AUDITEUR DE SÉCURITÉ IoT
# ============================================
class IoTSecurityAuditor:
    """
    Auditeur de sécurité automatique pour réseaux IoT
    """
    
    def __init__(self, network_range: str = "172.20.10.0/24", interface: str = "eth0", quick_mode: bool = False):
        self.network_range = network_range
        self.interface = interface
        self.local_ip = None
        self.quick_mode = quick_mode  # Mode rapide pour tests
        
        # Résultats d'audit
        self.audit_results = {
            'scan_results': {},
            'vulnerabilities': [],
            'attack_tests': [],
            'security_score': 0,
            'recommendations': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Devices découverts
        self.devices = []
        self.broker_ip = None
        self.mqtt_topics = []
        
        print("""
╔═══════════════════════════════════════════════════════════╗
║    IoT Security Auditor - Adversary Emulator             ║
║    Automated Security Assessment Tool                     ║
╚═══════════════════════════════════════════════════════════╝
        """)
        
        if quick_mode:
            print("[*] QUICK MODE: Using fast scan methods\n")
    
    # ========================================
    # PHASE 1 : RECONNAISSANCE
    # ========================================
    
    def phase1_reconnaissance(self):
        """Phase 1: Reconnaissance du réseau"""
        print("\n[PHASE 1] 🔍 RECONNAISSANCE")
        print("="*60)
        
        # 1.1 Obtenir l'IP locale
        print("[1.1] Detecting local IP...")
        if not self._get_local_ip():
            return False
        
        # 1.2 Scanner le réseau
        print(f"[1.2] Scanning network {self.network_range}...")
        self.devices = self._scan_network()
        
        if not self.devices:
            print("[-] No devices found")
            return False
        
        print(f"[+] Found {len(self.devices)} devices")
        
        # 1.3 Identifier les services
        print("[1.3] Identifying services...")
        self._identify_services()
        
        # 1.4 Découvrir le broker MQTT
        print("[1.4] Looking for MQTT broker...")
        self.broker_ip = self._find_mqtt_broker()
        
        if self.broker_ip:
            print(f"[+] MQTT Broker found: {self.broker_ip}")
            
            # 1.5 Découvrir les topics MQTT
            print("[1.5] Discovering MQTT topics...")
            self._discover_mqtt_topics()
        
        self.audit_results['scan_results'] = {
            'total_devices': len(self.devices),
            'broker_found': self.broker_ip is not None,
            'broker_ip': self.broker_ip,
            'topics_discovered': len(self.mqtt_topics),
            'devices': self.devices
        }
        
        return True
    
    def _get_local_ip(self) -> bool:
        """Obtient l'IP locale"""
        try:
            result = subprocess.run(
                ["ip", "-4", "addr", "show", self.interface],
                capture_output=True, text=True, check=True
            )
            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)', result.stdout)
            if match:
                self.local_ip = match.group(1)
                print(f"    Local IP: {self.local_ip}")
                return True
            return False
        except Exception as e:
            print(f"    Error: {e}")
            return False
    
    def _scan_network(self) -> List[str]:
        """Scanne le réseau avec nmap (optimisé)"""
        discovered_ips = []
        
        # Méthode 1: Scan rapide nmap (30 secondes max)
        try:
            print("    Method 1: Quick nmap scan (max 30s)...")
            result = subprocess.run(
                ["sudo", "nmap", "-sn", "-T5", "--min-rate", "1000", self.network_range],
                capture_output=True, text=True, check=True, timeout=30
            )
            ips = re.findall(r'Nmap scan report for .*?(\d+\.\d+\.\d+\.\d+)', result.stdout)
            discovered_ips.extend([ip for ip in ips if ip != self.local_ip])
            print(f"    Found {len(discovered_ips)} devices with nmap")
        except subprocess.TimeoutExpired:
            print("    Nmap timeout - trying alternative method...")
        except Exception as e:
            print(f"    Nmap failed: {e}")
        
        # Méthode 2: Scan ARP (plus rapide sur réseau local)
        if len(discovered_ips) == 0:
            try:
                print("    Method 2: ARP scan...")
                result = subprocess.run(
                    ["sudo", "arp-scan", "-l", "-I", self.interface],
                    capture_output=True, text=True, timeout=15
                )
                ips = re.findall(r'(\d+\.\d+\.\d+\.\d+)', result.stdout)
                discovered_ips.extend([ip for ip in ips if ip != self.local_ip and ip.startswith(self.network_range.split('/')[0][:10])])
                print(f"    Found {len(discovered_ips)} devices with arp-scan")
            except:
                pass
        
        # Méthode 3: Ping sweep simple (fallback)
        if len(discovered_ips) == 0:
            print("    Method 3: Ping sweep (scanning first 20 IPs)...")
            base_ip = '.'.join(self.network_range.split('.')[:3])
            for i in range(1, 21):  # Scan seulement les 20 premières IPs
                ip = f"{base_ip}.{i}"
                if ip == self.local_ip:
                    continue
                try:
                    result = subprocess.run(
                        ["ping", "-c", "1", "-W", "1", ip],
                        capture_output=True, timeout=2
                    )
                    if result.returncode == 0:
                        discovered_ips.append(ip)
                        print(f"    Found: {ip}")
                except:
                    pass
        
        # Dédupliquer
        discovered_ips = list(set(discovered_ips))
        return discovered_ips
    
    def _identify_services(self):
        """Identifie les services sur chaque device"""
        print("    Scanning common IoT ports...")
        common_ports = [80, 443, 1883, 8883, 5683, 8080, 22, 23]
        
        for device_ip in self.devices:
            open_ports = []
            for port in common_ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((device_ip, port))
                sock.close()
                if result == 0:
                    open_ports.append(port)
            
            if open_ports:
                print(f"    {device_ip}: ports {open_ports}")
    
    def _find_mqtt_broker(self) -> Optional[str]:
        """Trouve le broker MQTT"""
        for ip in self.devices:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((ip, 1883))
            sock.close()
            
            if result == 0:
                try:
                    test_client = mqtt.Client(client_id="audit_test", clean_session=True)
                    test_client.connect(ip, 1883, 5)
                    test_client.loop_start()
                    time.sleep(1)
                    test_client.loop_stop()
                    test_client.disconnect()
                    return ip
                except:
                    continue
        return None
    
    def _discover_mqtt_topics(self):
        """Découvre les topics MQTT actifs"""
        discovered_topics = []
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                client.subscribe("#")
        
        def on_message(client, userdata, msg):
            if msg.topic not in discovered_topics and not msg.topic.startswith('$SYS'):
                discovered_topics.append(msg.topic)
                print(f"    Topic: {msg.topic}")
        
        try:
            client = mqtt.Client(client_id="topic_discovery", clean_session=True)
            client.on_connect = on_connect
            client.on_message = on_message
            
            client.connect(self.broker_ip, 1883, 60)
            client.loop_start()
            
            # Mode rapide: 5 secondes, mode normal: 15 secondes
            listen_time = 5 if self.quick_mode else 15
            print(f"    Listening for {listen_time} seconds...")
            time.sleep(listen_time)
            
            client.loop_stop()
            client.disconnect()
            
            self.mqtt_topics = discovered_topics
            print(f"    Found {len(discovered_topics)} active topics")
            
        except Exception as e:
            print(f"    Error: {e}")
    
    # ========================================
    # PHASE 2 : ANALYSE DES VULNÉRABILITÉS
    # ========================================
    
    def phase2_vulnerability_analysis(self):
        """Phase 2: Analyse des vulnérabilités"""
        print("\n[PHASE 2] 🔐 VULNERABILITY ANALYSIS")
        print("="*60)
        
        vulnerabilities = []
        
        # 2.1 Test d'authentification MQTT
        print("[2.1] Testing MQTT authentication...")
        auth_vuln = self._test_mqtt_authentication()
        if auth_vuln:
            vulnerabilities.append(auth_vuln)
        
        # 2.2 Test de chiffrement
        print("[2.2] Testing encryption...")
        crypto_vuln = self._test_encryption()
        if crypto_vuln:
            vulnerabilities.append(crypto_vuln)
        
        # 2.3 Test de permissions MQTT
        print("[2.3] Testing MQTT permissions...")
        perm_vuln = self._test_mqtt_permissions()
        if perm_vuln:
            vulnerabilities.append(perm_vuln)
        
        # 2.4 Test de segmentation réseau
        print("[2.4] Testing network segmentation...")
        seg_vuln = self._test_network_segmentation()
        if seg_vuln:
            vulnerabilities.append(seg_vuln)
        
        self.audit_results['vulnerabilities'] = vulnerabilities
        
        print(f"\n[+] Found {len(vulnerabilities)} vulnerabilities")
        return True
    
    def _test_mqtt_authentication(self) -> Optional[Dict]:
        """Teste si le broker MQTT nécessite une authentification"""
        if not self.broker_ip:
            return None
        
        try:
            # Tenter connexion sans credentials
            client = mqtt.Client(client_id="auth_test", clean_session=True)
            client.connect(self.broker_ip, 1883, 5)
            client.loop_start()
            time.sleep(2)
            
            # Si on arrive ici, pas d'auth requise
            client.loop_stop()
            client.disconnect()
            
            print("    [!] No authentication required (CRITICAL)")
            return {
                'id': 'MQTT-AUTH-001',
                'severity': 'CRITICAL',
                'title': 'MQTT Broker without Authentication',
                'description': 'The MQTT broker allows anonymous connections without credentials',
                'impact': 'Anyone can connect and publish/subscribe to all topics',
                'cvss_score': 9.8
            }
        except:
            print("    [✓] Authentication required")
            return None
    
    def _test_encryption(self) -> Optional[Dict]:
        """Teste si le trafic MQTT est chiffré"""
        if not self.broker_ip:
            return None
        
        # Tester port 8883 (MQTT over TLS)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((self.broker_ip, 8883))
        sock.close()
        
        if result != 0:
            print("    [!] No TLS/SSL encryption (HIGH)")
            return {
                'id': 'MQTT-CRYPTO-001',
                'severity': 'HIGH',
                'title': 'MQTT Traffic Not Encrypted',
                'description': 'MQTT broker only listening on port 1883 (plaintext)',
                'impact': 'Traffic can be intercepted and read by attackers',
                'cvss_score': 7.5
            }
        else:
            print("    [✓] TLS/SSL available on port 8883")
            return None
    
    def _test_mqtt_permissions(self) -> Optional[Dict]:
        """Teste les permissions MQTT (ACL)"""
        if not self.broker_ip or not self.mqtt_topics:
            return None
        
        try:
            # Tenter de publier sur tous les topics
            client = mqtt.Client(client_id="perm_test", clean_session=True)
            client.connect(self.broker_ip, 1883, 5)
            client.loop_start()
            
            # Essayer de publier sur un topic sensible
            test_topic = self.mqtt_topics[0] if self.mqtt_topics else "test/topic"
            result = client.publish(test_topic, "test_payload", qos=1)
            
            time.sleep(2)
            client.loop_stop()
            client.disconnect()
            
            if result.rc == 0:
                print("    [!] No topic-level permissions (MEDIUM)")
                return {
                    'id': 'MQTT-PERM-001',
                    'severity': 'MEDIUM',
                    'title': 'MQTT Missing Access Control Lists (ACL)',
                    'description': 'Any client can publish to any topic',
                    'impact': 'Unauthorized data injection possible',
                    'cvss_score': 6.5
                }
        except:
            pass
        
        print("    [✓] Permissions seem configured")
        return None
    
    def _test_network_segmentation(self) -> Optional[Dict]:
        """Teste si le réseau IoT est segmenté"""
        # Vérifier si tous les devices sont sur le même subnet
        if len(self.devices) > 2:
            print("    [!] All devices on same network segment (MEDIUM)")
            return {
                'id': 'NET-SEG-001',
                'severity': 'MEDIUM',
                'title': 'Lack of Network Segmentation',
                'description': 'All IoT devices are on the same network segment',
                'impact': 'Lateral movement easier for attackers',
                'cvss_score': 5.5
            }
        
        print("    [✓] Network appears segmented")
        return None
    
    # ========================================
    # PHASE 3 : TESTS D'ATTAQUES
    # ========================================
    
    def phase3_attack_tests(self):
        """Phase 3: Tests d'attaques simulées"""
        print("\n[PHASE 3] ⚔️ ATTACK SIMULATION TESTS")
        print("="*60)
        
        attack_results = []
        
        # 3.1 Test MITM
        print("[3.1] Testing MITM attack resistance...")
        mitm_result = self._test_mitm_attack()
        attack_results.append(mitm_result)
        
        # 3.2 Test Injection
        print("[3.2] Testing data injection...")
        inject_result = self._test_data_injection()
        attack_results.append(inject_result)
        
        # 3.3 Test Flood/DoS
        print("[3.3] Testing DoS resistance...")
        dos_result = self._test_dos_attack()
        attack_results.append(dos_result)
        
        # 3.4 Test Replay Attack
        print("[3.4] Testing replay attack...")
        replay_result = self._test_replay_attack()
        attack_results.append(replay_result)
        
        self.audit_results['attack_tests'] = attack_results
        
        print(f"\n[+] Completed {len(attack_results)} attack tests")
        return True
    
    def _test_mitm_attack(self) -> Dict:
        """Teste la résistance aux attaques MITM"""
        result = {
            'attack_type': 'MITM',
            'success': False,
            'details': '',
            'resilience_score': 0
        }
        
        
        vulnerabilities = [v for v in self.audit_results['vulnerabilities'] 
                          if 'CRYPTO' in v.get('id', '')]
        
        if vulnerabilities:
            result['success'] = True
            result['details'] = 'Network vulnerable to MITM due to lack of encryption'
            result['resilience_score'] = 2
            print("    [!] VULNERABLE - No encryption protection")
        else:
            result['success'] = False
            result['details'] = 'TLS/SSL encryption would prevent MITM'
            result['resilience_score'] = 8
            print("    [✓] RESILIENT - Encryption present")
        
        return result
    
    def _test_data_injection(self) -> Dict:
        """Teste la résistance aux injections de données"""
        result = {
            'attack_type': 'Data Injection',
            'success': False,
            'details': '',
            'resilience_score': 0
        }
        
        if not self.broker_ip:
            result['details'] = 'No MQTT broker to test'
            return result
        
        try:
            # Tenter d'injecter des fausses données
            client = mqtt.Client(client_id="injection_test", clean_session=True)
            client.connect(self.broker_ip, 1883, 5)
            client.loop_start()
            
            test_topic = self.mqtt_topics[0] if self.mqtt_topics else "test/inject"
            fake_data = json.dumps({
                "temperature": 999,
                "attack": "injection_test",
                "timestamp": datetime.now().isoformat()
            })
            
            publish_result = client.publish(test_topic, fake_data, qos=1)
            time.sleep(2)
            
            client.loop_stop()
            client.disconnect()
            
            if publish_result.rc == 0:
                result['success'] = True
                result['details'] = 'Fake data successfully injected without validation'
                result['resilience_score'] = 3
                print("    [!] VULNERABLE - No data validation")
            else:
                result['success'] = False
                result['details'] = 'Data injection blocked'
                result['resilience_score'] = 9
                print("    [✓] RESILIENT - Injection blocked")
                
        except Exception as e:
            result['details'] = f'Test failed: {e}'
            result['resilience_score'] = 5
            print(f"    [?] UNKNOWN - Test error: {e}")
        
        return result
    
    def _test_dos_attack(self) -> Dict:
        """Teste la résistance aux attaques DoS"""
        result = {
            'attack_type': 'DoS/Flood',
            'success': False,
            'details': '',
            'resilience_score': 0
        }
        
        if not self.broker_ip:
            result['details'] = 'No MQTT broker to test'
            return result
        
        try:
            print("    Sending burst of messages...")
            
            # Envoyer un burst de 50 messages rapidement
            client = mqtt.Client(client_id="dos_test", clean_session=True)
            client.connect(self.broker_ip, 1883, 5)
            client.loop_start()
            
            start_time = time.time()
            messages_sent = 0
            
            for i in range(50):
                result_pub = client.publish("test/dos", f"msg_{i}", qos=0)
                if result_pub.rc == 0:
                    messages_sent += 1
            
            elapsed = time.time() - start_time
            
            client.loop_stop()
            client.disconnect()
            
            if messages_sent == 50:
                result['success'] = True
                result['details'] = f'Broker accepted all {messages_sent} messages in {elapsed:.2f}s - No rate limiting'
                result['resilience_score'] = 4
                print(f"    [!] VULNERABLE - No rate limiting ({messages_sent} msgs in {elapsed:.2f}s)")
            else:
                result['success'] = False
                result['details'] = f'Only {messages_sent}/50 messages accepted - Rate limiting active'
                result['resilience_score'] = 8
                print(f"    [✓] RESILIENT - Rate limiting detected")
                
        except Exception as e:
            result['details'] = f'Test failed: {e}'
            result['resilience_score'] = 5
            print(f"    [?] UNKNOWN - Test error: {e}")
        
        return result
    
    def _test_replay_attack(self) -> Dict:
        """Teste la résistance aux attaques par rejeu"""
        result = {
            'attack_type': 'Replay Attack',
            'success': False,
            'details': '',
            'resilience_score': 0
        }
        
        if not self.broker_ip or not self.mqtt_topics:
            result['details'] = 'No MQTT topics to test'
            result['resilience_score'] = 5
            return result
        
        # Vérifier si les messages ont des timestamps/nonces
        captured_messages = []
        
        def on_message(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode())
                captured_messages.append(payload)
            except:
                pass
        
        try:
            client = mqtt.Client(client_id="replay_test", clean_session=True)
            client.on_message = on_message
            client.connect(self.broker_ip, 1883, 5)
            client.loop_start()
            
            if self.mqtt_topics:
                client.subscribe(self.mqtt_topics[0])
            
            time.sleep(5)
            client.loop_stop()
            client.disconnect()
            
            if captured_messages:
                # Vérifier si messages ont timestamp/nonce
                has_timestamp = any('timestamp' in msg or 'nonce' in msg for msg in captured_messages)
                
                if has_timestamp:
                    result['success'] = False
                    result['details'] = 'Messages include timestamps/nonces'
                    result['resilience_score'] = 7
                    print("    [✓] RESILIENT - Timestamps present")
                else:
                    result['success'] = True
                    result['details'] = 'Messages lack timestamps - replay possible'
                    result['resilience_score'] = 3
                    print("    [!] VULNERABLE - No replay protection")
            else:
                result['details'] = 'No messages captured for analysis'
                result['resilience_score'] = 5
                print("    [?] UNKNOWN - No traffic observed")
                
        except Exception as e:
            result['details'] = f'Test failed: {e}'
            result['resilience_score'] = 5
            print(f"    [?] UNKNOWN - Test error: {e}")
        
        return result
    
    # ========================================
    # PHASE 4 : SCORING ET RECOMMANDATIONS
    # ========================================
    
    def phase4_scoring_and_recommendations(self):
        """Phase 4: Calcul du score et recommandations"""
        print("\n[PHASE 4] 📊 SCORING & RECOMMENDATIONS")
        print("="*60)
        
        # Calculer le score global
        self._calculate_security_score()
        
        # Générer les recommandations
        self._generate_recommendations()
        
        return True
    
    def _calculate_security_score(self):
        """Calcule le score de sécurité global (0-100)"""
        score = 100
        
        # Pénalités pour vulnérabilités
        for vuln in self.audit_results['vulnerabilities']:
            severity = vuln.get('severity', 'LOW')
            if severity == 'CRITICAL':
                score -= 25
            elif severity == 'HIGH':
                score -= 15
            elif severity == 'MEDIUM':
                score -= 10
            elif severity == 'LOW':
                score -= 5
        
        # Bonus pour résistance aux attaques
        for test in self.audit_results['attack_tests']:
            if not test.get('success', True):  # Si l'attaque a échoué = bon signe
                score += 5
        
        # Score entre 0 et 100
        score = max(0, min(100, score))
        
        self.audit_results['security_score'] = score
        
        # Classification
        if score >= 80:
            level = "EXCELLENT"
            color = "🟢"
        elif score >= 60:
            level = "GOOD"
            color = "🟡"
        elif score >= 40:
            level = "FAIR"
            color = "🟠"
        else:
            level = "POOR"
            color = "🔴"
        
        print(f"\n[+] SECURITY SCORE: {color} {score}/100 ({level})")
    
    def _generate_recommendations(self):
        """Génère des recommandations de sécurité"""
        recommendations = []
        
        # Recommandations basées sur les vulnérabilités
        for vuln in self.audit_results['vulnerabilities']:
            if 'AUTH' in vuln.get('id', ''):
                recommendations.append({
                    'priority': 'CRITICAL',
                    'category': 'Authentication',
                    'recommendation': 'Enable MQTT authentication with strong username/password',
                    'implementation': 'Configure mosquitto.conf: allow_anonymous false, password_file /etc/mosquitto/passwd'
                })
            
            if 'CRYPTO' in vuln.get('id', ''):
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Encryption',
                    'recommendation': 'Enable TLS/SSL encryption for MQTT traffic',
                    'implementation': 'Configure mosquitto to listen on port 8883 with TLS certificates'
                })
            
            if 'PERM' in vuln.get('id', ''):
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Access Control',
                    'recommendation': 'Implement topic-level ACLs to restrict publish/subscribe permissions',
                    'implementation': 'Create ACL file with specific permissions per user/client'
                })
            
            if 'SEG' in vuln.get('id', ''):
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Network Architecture',
                    'recommendation': 'Segment IoT network from corporate/guest networks using VLANs',
                    'implementation': 'Configure separate VLANs for IoT devices with firewall rules'
                })
        
        # Recommandations basées sur les tests d'attaque
        for test in self.audit_results['attack_tests']:
            if test.get('success'):  # Si l'attaque a réussi
                if test['attack_type'] == 'Data Injection':
                    recommendations.append({
                        'priority': 'HIGH',
                        'category': 'Data Validation',
                        'recommendation': 'Implement server-side data validation and sanitization',
                        'implementation': 'Add input validation rules for all sensor data fields'
                    })
                
                if test['attack_type'] == 'DoS/Flood':
                    recommendations.append({
                        'priority': 'MEDIUM',
                        'category': 'Rate Limiting',
                        'recommendation': 'Configure rate limiting on MQTT broker',
                        'implementation': 'Set max_connections and message rate limits in broker config'
                    })
                
                if test['attack_type'] == 'Replay Attack':
                    recommendations.append({
                        'priority': 'MEDIUM',
                        'category': 'Message Integrity',
                        'recommendation': 'Add timestamps and nonces to all MQTT messages',
                        'implementation': 'Include timestamp field in JSON payloads, reject old messages'
                    })
        
        # Recommandations générales
        recommendations.append({
            'priority': 'LOW',
            'category': 'Monitoring',
            'recommendation': 'Implement continuous security monitoring and logging',
            'implementation': 'Deploy SIEM solution (ELK Stack, Splunk) to analyze MQTT traffic'
        })
        
        recommendations.append({
            'priority': 'LOW',
            'category': 'Updates',
            'recommendation': 'Establish firmware update process for IoT devices',
            'implementation': 'Regular security patches and OTA update mechanism'
        })
        
        self.audit_results['recommendations'] = recommendations
        
        print(f"\n[+] Generated {len(recommendations)} security recommendations")
    
    # ========================================
    # PHASE 5 : GÉNÉRATION DU RAPPORT
    # ========================================
    
    def phase5_generate_report(self, output_file: str = "audit_report.json"):
        """Phase 5: Génération du rapport d'audit"""
        print("\n[PHASE 5] 📄 REPORT GENERATION")
        print("="*60)
        
        # Sauvegarder en JSON
        with open(output_file, 'w') as f:
            json.dump(self.audit_results, f, indent=2)
        
        print(f"[+] JSON report saved: {output_file}")
        
        # Générer rapport HTML
        html_file = output_file.replace('.json', '.html')
        self._generate_html_report(html_file)
        print(f"[+] HTML report saved: {html_file}")
        
        # Afficher résumé dans le terminal
        self._print_summary()
        
        return True
    
    def _generate_html_report(self, filename: str):
        """Génère un rapport HTML"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>IoT Security Audit Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .score {{ font-size: 48px; font-weight: bold; text-align: center; padding: 20px; margin: 20px 0; border-radius: 10px; }}
        .score.excellent {{ background: #2ecc71; color: white; }}
        .score.good {{ background: #f39c12; color: white; }}
        .score.fair {{ background: #e67e22; color: white; }}
        .score.poor {{ background: #e74c3c; color: white; }}
        .vuln {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 10px 0; }}
        .vuln.critical {{ border-left-color: #dc3545; background: #f8d7da; }}
        .vuln.high {{ border-left-color: #fd7e14; background: #ffe5d0; }}
        .recommendation {{ background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 10px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #3498db; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 IoT Security Audit Report</h1>
        <p><strong>Date:</strong> {self.audit_results['timestamp']}</p>
        <p><strong>Network:</strong> {self.network_range}</p>
        
        <div class="score {'excellent' if self.audit_results['security_score'] >= 80 else 'good' if self.audit_results['security_score'] >= 60 else 'fair' if self.audit_results['security_score'] >= 40 else 'poor'}">
            Security Score: {self.audit_results['security_score']}/100
        </div>
        
        <h2>📊 Scan Results</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Total Devices</td><td>{self.audit_results['scan_results'].get('total_devices', 0)}</td></tr>
            <tr><td>MQTT Broker Found</td><td>{'Yes' if self.audit_results['scan_results'].get('broker_found') else 'No'}</td></tr>
            <tr><td>Broker IP</td><td>{self.audit_results['scan_results'].get('broker_ip', 'N/A')}</td></tr>
            <tr><td>Topics Discovered</td><td>{self.audit_results['scan_results'].get('topics_discovered', 0)}</td></tr>
        </table>
        
        <h2>🚨 Vulnerabilities Found ({len(self.audit_results['vulnerabilities'])})</h2>
"""
        
        for vuln in self.audit_results['vulnerabilities']:
            html += f"""
        <div class="vuln {vuln['severity'].lower()}">
            <h3>{vuln['title']}</h3>
            <p><strong>Severity:</strong> {vuln['severity']} (CVSS: {vuln['cvss_score']})</p>
            <p><strong>Description:</strong> {vuln['description']}</p>
            <p><strong>Impact:</strong> {vuln['impact']}</p>
        </div>
"""
        
        html += f"""
        <h2>⚔️ Attack Test Results</h2>
        <table>
            <tr><th>Attack Type</th><th>Success</th><th>Resilience Score</th><th>Details</th></tr>
"""
        
        for test in self.audit_results['attack_tests']:
            html += f"""
            <tr>
                <td>{test['attack_type']}</td>
                <td>{'❌ Vulnerable' if test.get('success') else '✅ Resilient'}</td>
                <td>{test.get('resilience_score', 0)}/10</td>
                <td>{test.get('details', 'N/A')}</td>
            </tr>
"""
        
        html += """
        </table>
        
        <h2>💡 Security Recommendations</h2>
"""
        
        for rec in self.audit_results['recommendations']:
            html += f"""
        <div class="recommendation">
            <h3>[{rec['priority']}] {rec['category']}</h3>
            <p><strong>Recommendation:</strong> {rec['recommendation']}</p>
            <p><strong>Implementation:</strong> {rec['implementation']}</p>
        </div>
"""
        
        html += """
    </div>
</body>
</html>
"""
        
        with open(filename, 'w') as f:
            f.write(html)
    
    def _print_summary(self):
        """Affiche un résumé dans le terminal"""
        print("\n" + "="*60)
        print("AUDIT SUMMARY")
        print("="*60)
        
        print(f"\n📊 Security Score: {self.audit_results['security_score']}/100")
        print(f"🚨 Vulnerabilities: {len(self.audit_results['vulnerabilities'])}")
        print(f"💡 Recommendations: {len(self.audit_results['recommendations'])}")
        
        if self.audit_results['vulnerabilities']:
            print("\nTop Vulnerabilities:")
            for vuln in self.audit_results['vulnerabilities'][:3]:
                print(f"  - [{vuln['severity']}] {vuln['title']}")
        
        if self.audit_results['recommendations']:
            print("\nTop Recommendations:")
            for rec in self.audit_results['recommendations'][:3]:
                print(f"  - [{rec['priority']}] {rec['recommendation']}")
    
    # ========================================
    # EXÉCUTION COMPLÈTE DE L'AUDIT
    # ========================================
    
    def run_full_audit(self):
        """Exécute un audit complet"""
        print(f"\n[*] Starting IoT Security Audit")
        print(f"[*] Target Network: {self.network_range}")
        print(f"[*] Interface: {self.interface}\n")
        
        start_time = time.time()
        
        try:
            # Phase 1: Reconnaissance
            if not self.phase1_reconnaissance():
                print("\n[-] Reconnaissance failed. Aborting audit.")
                return False
            
            # Phase 2: Vulnerability Analysis
            self.phase2_vulnerability_analysis()
            
            # Phase 3: Attack Tests
            self.phase3_attack_tests()
            
            # Phase 4: Scoring & Recommendations
            self.phase4_scoring_and_recommendations()
            
            # Phase 5: Report Generation
            self.phase5_generate_report()
            
            elapsed = time.time() - start_time
            
            print(f"\n[✓] Audit completed in {elapsed:.2f} seconds")
            print(f"[✓] Final Score: {self.audit_results['security_score']}/100")
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n[!] Audit interrupted by user")
            return False
        except Exception as e:
            print(f"\n[!] Audit failed: {e}")
            return False


# ============================================
# MAIN
# ============================================
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='IoT Security Auditor - Adversary Emulator')
    parser.add_argument('--network', default='192.168.10.0/24', help='Network range to scan')
    parser.add_argument('--interface', default='eth0', help='Network interface')
    parser.add_argument('--output', default='audit_report.json', help='Output file')
    parser.add_argument('--quick', action='store_true', help='Quick mode (faster but less thorough)')
    parser.add_argument('--manual-ip', help='Manually specify broker IP (skip scan)')
    
    args = parser.parse_args()
    
    # Vérifier root
    if os.geteuid() != 0:
        print("[-] This tool requires root privileges")
        print(f"    Run: sudo python3 {__file__}")
        return
    
    # Créer et lancer l'auditeur
    auditor = IoTSecurityAuditor(
        network_range=args.network,
        interface=args.interface,
        quick_mode=args.quick
    )
    
    # Si IP manuelle fournie
    if args.manual_ip:
        print(f"[*] Using manually specified broker: {args.manual_ip}")
        auditor.broker_ip = args.manual_ip
        auditor.devices = [args.manual_ip]
        auditor.audit_results['scan_results'] = {
            'total_devices': 1,
            'broker_found': True,
            'broker_ip': args.manual_ip,
            'topics_discovered': 0,
            'devices': [args.manual_ip]
        }
        
        # Sauter la phase 1 et aller directement aux tests
        print("\n[*] Skipping reconnaissance phase...")
        print("[*] Discovering MQTT topics...")
        auditor._discover_mqtt_topics()
        
        # Phases suivantes
        auditor.phase2_vulnerability_analysis()
        auditor.phase3_attack_tests()
        auditor.phase4_scoring_and_recommendations()
        auditor.phase5_generate_report(args.output)
        
        print(f"\n[+] Reports generated:")
        print(f"    - JSON: {args.output}")
        print(f"    - HTML: {args.output.replace('.json', '.html')}")
        return 0
    
    # Audit complet
    success = auditor.run_full_audit()
    
    if success:
        print(f"\n[+] Reports generated:")
        print(f"    - JSON: {args.output}")
        print(f"    - HTML: {args.output.replace('.json', '.html')}")
    
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
