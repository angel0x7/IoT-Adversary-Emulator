# 🛰️ Prototype d’Outil d’Émulation d’un Adversaire IoT — PPE ING4-Cyber

##  Description
Ce projet consiste à développer un **prototype d’outil capable de simuler le comportement d’un adversaire ciblant des dispositifs IoT** (Internet des Objets).  
L’objectif est de reproduire différents scénarios d’attaques (intrusions, manipulations de données, dénis de service, compromission de capteurs, etc.) dans un environnement **contrôlé et reproductible**, afin d’évaluer la **résilience, la sécurité et la robustesse** des systèmes IoT.  

Cet outil s’adresse aux **chercheurs** et **professionnels de la cybersécurité** pour :
- tester des contre-mesures,  
- entraîner et valider des mécanismes de détection,  
- renforcer la protection des infrastructures connectées.

Projet réalisé dans le cadre du **PPE (Projet Pluridisciplinaire en Équipe)** à l’**ECE Paris** en majeure **Cyber & Data**.

---
##  Documents inclus
| Fichier | Description |
|----------|-------------|
| [`note-de-cadrage-ppe.pdf`](note-de-cadrage-ppe.pdf) | Note de cadrage du projet |
| [`Topologie_PPE.png`](Topologie_PPE.png) | Schéma réseau OT/IT du prototype |
| [`PPE Soutenance finale.pdf`](PPE_Soutenance_finale.pdf) | Présentation Finale |
---

##  Objectifs
- Développer un **émulateur d’attaques IoT** modulable et extensible.  
- Proposer une **plateforme de simulation** pour différents scénarios :  
  - reconnaissance réseau,  
  - injection de données,  
  - replay attack,  
  - déni de service,  
  - compromission de capteurs et passerelles.  
- Intégrer un **pipeline de détection et visualisation** des anomalies.  
- Garantir un cadre **éthique et sécurisé** pour l’expérimentation.  

---

##  Architecture du Système IoT

### 🔹 Schéma de topologie OT / IT
Ce schéma illustre la séparation logique entre les couches **IT (niveau 3-5)** et **OT (niveau 0-2)** du réseau industriel, avec les VLANs correspondants et les protocoles utilisés.

![Topologie du Réseau IoT](Topologie_PPE.png)

| Couche | VLAN | Rôle | Protocoles principaux |
|--------|------|------|-----------------------|
| IT – Enterprise | VLAN 40 | ERP / MES / Admin | HTTPS, REST API, SQL |
| IT – SCADA | VLAN 30 | Supervision & passerelle | MQTT, OPC-UA, HTTP |
| OT – Process Control | VLAN 20 | PLC, HMI, Stations d’ingénierie | Modbus TCP, MQTT |
| OT – Field Level | VLAN 10 | Capteurs et actionneurs | Modbus RTU, I²C, BLE, MQTT |

---

##  Note de cadrage du projet
La note de cadrage définit le **contexte**, le **périmètre**, les **objectifs**, les **contraintes éthiques** et les **livrables** du projet.

 [Consulter la note de cadrage (PDF)](note-de-cadrage-ppe.pdf)

---

##  Équipe & Collaboration
Projet mené par une **équipe pluridisciplinaire d’étudiants** en :
- Cybersécurité offensive & défensive,  
- Réseaux IoT,  
- Analyse de données & Intelligence Artificielle.  

Méthodologie : **Agile (Scrum / Kanban)** avec sprints, suivi régulier et validation par le coach référent.

---

##  Planning (6+ mois)
![Déroulement](images/deroulement.png)
![Valorisation](images/valorisation.png)
![Calendrier](images/calendrier.png)

---

##  Contraintes Éthiques & Réglementaires
- **Usage strictement académique et expérimental** (lab fermé, réseau isolé).  
- Respect du **cadre légal** (aucune attaque sur des infrastructures réelles ou publiques).  
- Mise en place de **procédures d’arrêt d’urgence (kill-switch)**.  
- **Documentation claire** sur les limites d’utilisation et le périmètre autorisé.  

---

##  Valorisation & Communication
- Documentation technique et pédagogique.  
- Démonstrations lors des soutenances PPE.  
- Publication possible de jeux de données (logs anonymisés).  
- Perspectives d’extension : intégration dans des plateformes de **cyber range IoT**.  

---

© 2025 — PPE ING4 Cyber & Data — ECE Paris
