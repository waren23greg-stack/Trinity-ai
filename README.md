# 🏥 TRINITY AI: The Self-Healing Hospital Ops Engine

[![License: MIT](https://shields.io)](https://opensource.org)
[![Python 3.11+](https://shields.io)](https://python.org)
[![LangChain](https://shields.io)](https://langchain.com)
[![Docker](https://shields.io)](https://docker.com)

**Stop fighting fires. Start commanding your infrastructure.**

TRINITY AI is an AI-driven, cloud-native command center designed for single-administrator IT teams in high-pressure environments (Hospitals, Logistics Hubs, or Multi-site Campuses). It bridges the gap between automated scripting and physical attendance by using a **Generative AI Triage Engine** that autonomously resolves 80% of network, hardware, and software issues—escalating only the unsolvable 20% to your human expert with forensic-level detail.

---

## 📌 Table of Contents
- [The Problem We Solve](#-the-problem-we-solve)
- [Core Features](#-core-features)
- [System Architecture](#-system-architecture)
- [Scale Matrix: Customization by Facility Size](#-scale-matrix-customization-by-facility-size)
- [Tech Stack](#-tech-stack)
- [How It Works: The Triage Pipeline](#-how-it-works-the-triage-pipeline)
- [Privacy & Security (HIPAA / GDPR Ready)](#-privacy--security-hipaa--gdpr-ready)
- [Getting Started (Local Development)](#-getting-started-local-development)
- [Dashboard Layout](#-dashboard-layout-concept)
- [Contributing](#-contributing)

---

## 🚀 The Problem We Solve

- **The "Bus Factor" of 1:** One IT admin managing 200+ departments and 500+ daily patients.
- **Context Switching:** Running between a printer jam, a crashed PC, and a downed router simultaneously.
- **Blind Alerts:** Getting a ticket that says "Internet is slow" with zero diagnostic context.

**TRINITY AI transforms this chaos into a single-pane-of-glass where the AI acts as your tireless Level-1 & Level-2 support, leaving you only the physical, mechanical tasks.**

---

## ✨ Core Features

### 1. Generative AI Root-Cause Analysis
- Uses **Chain-of-Thought (CoT)** reasoning via a locally-hosted LLM (Ollama/LLaMA) or Azure OpenAI.
- Instead of hardcoded "If/Then" rules, the AI reads live telemetry, hypothesizes the fault (e.g., "Broadcast Storm" vs. "ISP Outage"), and selects the correct remediation script.

### 2. The "Try-Fail-Escalate" Loop
- The AI executes up to **3 automated attempts** (e.g., Restart Service → Reinstall Driver → Network Stack Reset).
- If attempts fail, the AI **halts automation** and generates a **"Warren Packet"**—a forensic report including root cause probability, suggested spare parts, and estimated physical fix time.

### 3. Automated Network Failover & Device Resuscitation
- **SD-WAN Auto-Failover:** Detects ISP failure on Router V and instantly routes traffic through a 4G/5G USB dongle.
- **PoE Cycling:** Remotely power-cycles CCTV cameras and dead access points via managed switch APIs.
- **VDI Auto-Scaling:** Spins up temporary cloud desktops during patient registration spikes to eliminate queues.

### 4. Department Self-Service "Frustration Portal"
- A lightweight web/mobile interface for nurses and doctors to report issues the AI hasn't detected (e.g., "My mouse is lagging").
- The AI runs instant diagnostics and either fixes the issue (e.g., switching Wi-Fi bands) or adds context to Warren's physical route.

### 5. Self-Learning Feedback Loop
- Warren tags resolved tickets as "AI was Right" or "AI was Wrong."
- The system vectorizes voice/text notes and updates the AI's knowledge base overnight, ensuring it gets smarter every day.

---

## 🏗️ System Architecture

```mermaid
graph TD
    A[Endpoints: PCs, Printers, CCTV, Routers] -->|Telemetry via MQTT/SNMP| B(IoT Gateway)
    C[Department Portal] -->|Manual Tickets| D(AI Orchestrator - LangChain)
    B --> D
    
    D --> E{AI Triage Engine}
    E -->|Execute Script| F[Ansible AWX / PowerShell]
    F -->|Remediation| A
    
    E -->|3 Failures| G[Generate "Warren Packet"]
    G --> H[Push Notification / Dashboard]
    
    I[Vector Database - Pinecone] <--> E
    J[Time-Series DB - InfluxDB] <--> E
```

---

## 📦 Scale Matrix: Customization by Facility Size

TRINITY AI is modular. You can deploy the Core AI Brain everywhere, but scale the telemetry agents based on your bed count.

| Facility Type | Daily Patients | Departments | Recommended Deployment | Hardware Requirements |
| :--- | :--- | :--- | :--- | :--- |
| **Small Clinic** | < 100 | < 20 | Single Docker Container + Ollama (CPU-only mode). No on-prem switches required. | 8GB RAM, 4 vCPUs. |
| **Medium Hospital** | 100 - 500 | 50 - 100 | Kubernetes cluster (3 nodes). Deploy LLM with GPU (NVIDIA T4). Implement PoE switching. | 32GB RAM, 8 vCPUs, 8GB VRAM. |
| **Large Tertiary** | 500 - 1,000+ | 200+ | High-Availability Cloud (Azure/AWS). On-prem Edge Agents for failover. Redundant 5G modems. | 128GB RAM, 16 vCPUs, 24GB VRAM (A100). |

---

## 🛠️ Tech Stack

* **AI Framework:** LangChain + ReAct Agent Pattern.
* **LLM Backend:** Ollama (Llama 3.1 70B) or Azure OpenAI (HIPAA-compliant).
* **Vector DB:** Pinecone / Weaviate (for storing past incidents and runbooks).
* **Script Execution:** Ansible AWX (open-source Tower) / PowerShell DSC.
* **Networking:** Zabbix + Prometheus exporters for SNMP polling.
* **Frontend:** Grafana (Dashboard) + Streamlit (Department Portal).
* **Device Tunneling:** Azure IoT Hub / AWS IoT Core for secure remote KVM access.

---

## 🚦 How It Works: The Triage Pipeline

1. **Detection**: A sensor detects "Router V Offline" or "Queue > 15 mins."
2. **Hypothesis**: The AI queries the Vector DB for similar past incidents.
3. **Attempt 1 (Software)**: Run Script: `restart_network_stack.py` → Fails.
4. **Attempt 2 (Logical)**: Run Script: `failover_to_5g.py` → Succeeds. Alert auto-resolves.
5. **Failure (Hardware)**: If "Printer E" fails all scripted fixes, the AI generates an escalation:
   > "Escalate: Printer E. Thermal sensor reads 50°C. Suspect Fuser Unit. Part #XYZ-123. Spare located in Storage B3. ETA to fix: 12 mins."

---

## 🔐 Privacy & Security (HIPAA / GDPR Ready)

- **Data Anonymization**: Patient names/IDs are hashed before entering the AI context window. The AI sees only "Queue length: 45" and "Department: Records," never PII (Personally Identifiable Information).
- **On-Prem LLM Option**: Use Ollama locally to ensure zero patient data leaves the hospital network.
- **RBAC**: Role-based access control separates "View-Only" for department heads and "Full-Access" for the admin team.
- **Audit Logging**: Every script executed by the AI is logged immutably for 7 years (required for medical device compliance).

---

## 🧪 Getting Started (Local Development)

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- NVIDIA CUDA (optional, for GPU acceleration)

### Quick Install

```bash
# Clone the repository
git clone https://github.com
cd trinity-ai

# Spin up the core services (InfluxDB, Grafana, Redis)
docker-compose up -d

# Install Python dependencies and run the AI Orchestrator
pip install -r requirements.txt
python orchestrator.py --mode simulate --department records
```

Access the dashboard at `http://localhost:3000` (Default: `admin/admin`).

### Simulating a Network Outage
```bash
curl -X POST http://localhost:5000/api/inject_fault \
  -H "Content-Type: application/json" \
  -d '{"device": "Router_V", "fault": "isp_down"}'
```
Watch TRINITY AI auto-failover to 5G in the live logs.

---

## 📊 Dashboard Layout (Concept)

| Quadrant | Content |
| :--- | :--- |
| **Top Left** | Live Network Topology (Green = Healthy, Orange = AI Fixing, Red = Needs Admin). |
| **Top Right** | Active "Warren Packet" Queue (Physical tasks sorted by Priority & GPS Route). |
| **Bottom Left** | Department Heatmap (Shows registration queue stress levels in real-time). |
| **Bottom Right** | AI Activity Log (Live feed of scripts being executed and their outcomes). |

---

## 🤝 Contributing

We welcome contributions! Since this is designed for critical infrastructure, we follow a strict "Test-First" policy. Please fork the repo and submit a PR.
