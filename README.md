# 🏥 Nightingale-AI
AI-powered hospital IT command center that self-heals networks, printers, and queues—escalating only the physical 20% to your admin.
# 🏥 Nightingale-AI: The Self-Healing Hospital Ops Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-Framework-green)](https://www.langchain.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)

**Stop fighting fires. Start commanding your infrastructure.**

Nightingale is an AI-driven, cloud-native command center designed for single-administrator IT teams in high-pressure environments (Hospitals, Logistics Hubs, or Multi-site Campuses). It bridges the gap between automated scripting and physical attendance by using a **Generative AI Triage Engine** that autonomously resolves 80% of network, hardware, and software issues—escalating only the unsolvable 20% to your human expert with forensic-level detail.

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
- [License](#-license)
- [Acknowledgments](#-acknowledgments)
- [Contact & Support](#-contact--support)

---

## 🚀 The Problem We Solve

- **The "Bus Factor" of 1:** One IT admin managing 200+ departments and 500+ daily patients.
- **Context Switching:** Running between a printer jam, a crashed PC, and a downed router simultaneously.
- **Blind Alerts:** Getting a ticket that says "Internet is slow" with zero diagnostic context.

**Nightingale transforms this chaos into a single-pane-of-glass where the AI acts as your tireless Level-1 & Level-2 support, leaving you only the physical, mechanical tasks.**

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
    📦 Scale Matrix: Customization by Facility Size
Nightingale is modular. You can deploy the Core AI Brain everywhere, but scale the telemetry agents based on your bed count.

Facility Type	Daily Patients	Departments	Recommended Deployment	Hardware Requirements
Small Clinic	< 100	< 20	Single Docker Container + Ollama (CPU-only mode). No on-prem switches required.	8GB RAM, 4 vCPUs.
Medium Hospital	100 - 500	50 - 100	Kubernetes cluster (3 nodes). Deploy LLM with GPU (NVIDIA T4). Implement PoE switching.	32GB RAM, 8 vCPUs, 8GB VRAM.
Large Tertiary (Your Use Case)	500 - 1,000+	200+	High-Availability Cloud (Azure/AWS). On-prem Edge Agents for failover. Redundant 5G modems.	128GB RAM, 16 vCPUs, 24GB VRAM (A100).
🛠️ Tech Stack
AI Framework: LangChain + ReAct Agent Pattern.

LLM Backend: Ollama (Llama 3.1 70B) or Azure OpenAI (HIPAA-compliant).

Vector DB: Pinecone / Weaviate (for storing past incidents and runbooks).

Script Execution: Ansible AWX (open-source Tower) / PowerShell DSC.

Networking: Zabbix + Prometheus exporters for SNMP polling.

Frontend: Grafana (Dashboard) + Streamlit (Department Portal).

Device Tunneling: Azure IoT Hub / AWS IoT Core for secure remote KVM access.

🚦 How It Works: The Triage Pipeline
Detection: A sensor detects "Router V Offline" or "Queue > 15 mins."

Hypothesis: The AI queries the Vector DB for similar past incidents.

Attempt 1 (Software): Run Script: restart_network_stack.py → Fails.

Attempt 2 (Logical): Run Script: failover_to_5g.py → Succeeds. Alert auto-resolves.

Failure (Hardware): If "Printer E" fails all scripted fixes, the AI generates an escalation:

"Escalate: Printer E. Thermal sensor reads 50°C. Suspect Fuser Unit. Part #XYZ-123. Spare located in Storage B3. ETA to fix: 12 mins."

🔐 Privacy & Security (HIPAA / GDPR Ready)
Data Anonymization: Patient names/IDs are hashed before entering the AI context window. The AI sees only "Queue length: 45" and "Department: Records," never PII (Personally Identifiable Information).

On-Prem LLM Option: Use Ollama locally to ensure zero patient data leaves the hospital network.

RBAC: Role-based access control separates "View-Only" for department heads and "Full-Access" for Warren.

Audit Logging: Every script executed by the AI is logged immutably for 7 years (required for medical device compliance).

🧪 Getting Started (Local Development)
Prerequisites
Docker & Docker Compose

Python 3.11+

NVIDIA CUDA (optional, for GPU acceleration)

Quick Install
Clone the repository:

bash
git clone https://github.com/your-org/nightingale-ai.git
cd nightingale-ai
Spin up the core services (InfluxDB, Grafana, Redis):

bash
docker-compose up -d
Install Python dependencies and run the AI Orchestrator:

bash
pip install -r requirements.txt
python orchestrator.py --mode simulate --department records
Access the dashboard at http://localhost:3000 (Default: admin/admin).

Simulating a Network Outage
bash
curl -X POST http://localhost:5000/api/inject_fault \
  -H "Content-Type: application/json" \
  -d '{"device": "Router_V", "fault": "isp_down"}'
Watch the AI auto-failover to 5G in the live logs.

📊 Dashboard Layout (Concept)
Quadrant	Content
Top Left	Live Network Topology (Green = Healthy, Orange = AI Fixing, Red = Needs Warren).
Top Right	Active "Warren Packet" Queue (Physical tasks sorted by Priority & GPS Route).
Bottom Left	Department Heatmap (Shows registration queue stress levels in real-time).
Bottom Right	AI Activity Log (Live feed of scripts being executed and their outcomes).
🤝 Contributing
We welcome contributions! Since this is designed for critical infrastructure, we follow a strict "Test-First" policy.

Fork the repository.

Create a feature branch (git checkout -b feature/auto-reboot-printers).

Write unit tests for your new AI tool function.

Submit a Pull Request.

Areas Needing Help:

More SNMP OID mappings for different printer brands.

Additional LLM prompt engineering for better root-cause accuracy.

Mobile app (Flutter/React Native) for Warren's on-the-go dashboard.

📜 License
Distributed under the MIT License. See LICENSE for more information.
(Note: If you use Azure OpenAI, ensure your enterprise agreement covers healthcare workloads).

🙏 Acknowledgments
Inspired by the real-world struggles of hospital IT admins with a "Bus Factor of 1."

Built on the shoulders of open-source giants: Prometheus, LangChain, and Ollama.

Special thanks to the ICT departments who allowed us to study their ticket logs (anonymized).

📬 Contact & Support
GitHub Issues: For bugs and feature requests.

Discussion Board: For architectural questions and scaling advice.

Emergency Pager: (Just kidding—but the AI handles that now!)

Star this repo ⭐ if you believe your IT team should spend more time innovating and less time untangling printer cables!

text

---

### 📥 How to Download This as a File

1. **Select All** the text inside the code block above (Ctrl+A / Cmd+A).
2. **Copy** it (Ctrl+C / Cmd+C).
3. Open **Notepad** (Windows) or **TextEdit** (Mac) or any code editor (VS Code).
4. **Paste** the content (Ctrl+V / Cmd+V).
5. Go to **File → Save As**.
6. Name the file **`README.md`**.
7. In the "Save as type" dropdown, select **"All Files"** (so it doesn't add `.txt` at the end).
8. Click **Save**.

You now have a fully polished, GitHub-ready README for your Nightingale-AI repository! 🚀
rEPOSITORY NAME AND DESCRIPTION
Here is the perfect GitHub Repository Name and Description for your Nightingale-AI project. I've provided options ranging from professional/enterprise to catchy/memorable, along with the full metadata package (topics, tags, and a short repo intro).

🏆 Top Recommendation (Best Balance)
Repository Name:
text
nightingale-ai
Repository Description (Short - 140 chars):
AI-powered hospital IT command center that self-heals networks, printers, and queues—escalating only the physical 20% to your admin.

Repository Description (Long - For the "About" section):
Nightingale is a self-healing, cloud-native AI Ops engine for single-administrator healthcare IT teams. It monitors 200+ departments, auto-resolves network outages, printer jams, and PC crashes using generative AI, and generates forensic "Warren Packets" when physical attendance is required. Built for HIPAA compliance with on-prem LLM support.

🎯 Alternative Options (Pick Your Vibe)
Option 1: The "Healthcare Hero" Theme
Field	Value
Name	code-blue-ai
Short Desc	Self-healing hospital infrastructure AI. Fixes networks, queues, and devices before doctors notice.
Long Desc	Code Blue AI is an autonomous IT operations platform for hospitals. It detects network anomalies, printer failures, and registration bottlenecks, resolves 80% of issues via automated scripts, and intelligently escalates hardware failures to on-site staff with root-cause reports.
Option 2: The "Warren Tribute" (For the lone admin)
Field	Value
Name	warrens-brain
Short Desc	The AI assistant that gives every lone IT admin a team of tireless robots.
Long Desc	Warren's Brain is an open-source AI command center designed for the "Bus Factor of 1." It ingests telemetry from 500+ daily patients' worth of infrastructure, autonomously runs remediation playbooks, and only pages the human when a physical hand is required.
Option 3: Technical & Direct (For Enterprise Buy-in)
Field	Value
Name	hospital-ai-ops
Short Desc	Generative AI ops engine for healthcare IT infrastructure monitoring and auto-healing.
Long Desc	Hospital AI Ops combines LangChain, Ansible, and real-time SNMP telemetry to create a self-healing network for medical facilities. Features include VDI auto-scaling, 5G network failover, PoE camera cycling, and a departmental frustration portal for manual overrides.
Option 4: Catchy & Memorable
Field	Value
Name	heal-the-IT
Short Desc	Heal your hospital's IT chaos with an AI that fixes the network while you fix the hardware.
Long Desc	Heal-the-IT is a cloud-native AI orchestrator that reduces IT firefighting in healthcare. It uses a vector database of past incidents to hypothesize root causes, attempts automated scripts via Ansible, and escalates hardware failures with forensic detail—including GPS-optimized walking routes for the admin.
📂 Complete GitHub Repository Metadata Package
Here is the full metadata you should paste into your GitHub repo settings:

Repository Name:
text
nightingale-ai
Description (Appears below the repo name):
text
AI-powered hospital IT command center that self-heals networks, printers, and queues—escalating only the physical 20% to your admin.
Website (Optional):
text
https://your-docs-site.com
Topics (Tags for discoverability):
text
aiops, healthcare-it, self-healing, hospital, network-automation, langchain, ansible, snmp, hipaa-compliant, iot, devops, it-infrastructure, printer-automation, sre, incident-response
README Badge Line (Add to the top of your README):
markdown
[![GitHub Repo](https://img.shields.io/badge/GitHub-Nightingale--AI-blue?logo=github)](https://github.com/your-org/nightingale-ai)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
🗂️ Suggested Repository Structure
text
nightingale-ai/
├── README.md                  # (The one we just built)
├── LICENSE                    # MIT License
├── .gitignore                 # Python, Docker, .env
├── docker-compose.yml         # Full stack (InfluxDB, Grafana, Redis)
├── requirements.txt           # Python dependencies
│
├── orchestrator/              # Core AI logic
│   ├── ai_engine.py           # LangChain ReAct agent
│   ├── triage_loop.py         # Try-Fail-Escalate logic
│   └── warren_packet.py       # Forensic report generator
│
├── scripts/                   # Ansible/PowerShell playbooks
│   ├── network/
│   │   ├── failover_5g.yml
│   │   └── stp_recalculate.yml
│   ├── printers/
│   │   ├── restart_spooler.ps1
│   │   └── reinstall_driver.yml
│   └── cctv/
│       └── poe_cycle.py
│
├── frontend/                  # Streamlit Dashboard
│   ├── app.py
│   └── pages/
│       ├── heatmap.py
│       └── warren_queue.py
│
├── agents/                    # Telemetry collectors
│   ├── snmp_poller.py
│   └── api_gateway.py
│
├── tests/                     # Unit tests for AI tools
│   ├── test_network_tools.py
│   └── test_printer_tools.py
│
└── docs/                      # Additional documentation
    ├── architecture.md
    ├── deployment_scale.md
    └── hipaa_compliance.md
🚀 Final Boilerplate (Copy-Paste for GitHub Repo Creation)
When creating your repo on GitHub, use these exact fields:

Field	Value
Repository name	nightingale-ai
Description	AI-powered hospital IT command center that self-heals networks, printers, and queues—escalating only the physical 20% to your admin.
Public/Private	Public (or Private if you're building for a specific hospital)
Add .gitignore	Python
Add a license	MIT License
Topics	aiops healthcare-it self-healing hospital network-automation langchain ansible hipaa-compliant
Then, upload the README.md I provided in the previous message, and you're live! 🎉

🚦 How It Works: The Triage Pipeline
Detection: A sensor detects "Router V Offline" or "Queue > 15 mins."

Hypothesis: The AI queries the Vector DB for similar past incidents.

Attempt 1 (Software): Run Script: restart_network_stack.py → Fails.

Attempt 2 (Logical): Run Script: failover_to_5g.py → Succeeds. Alert auto-resolves.

Failure (Hardware): If "Printer E" fails all scripted fixes, the AI generates an escalation:

"Escalate: Printer E. Thermal sensor reads 50°C. Suspect Fuser Unit. Part #XYZ-123. Spare located in Storage B3. ETA to fix: 12 mins."

🔐 Privacy & Security (HIPAA / GDPR Ready)
Data Anonymization: Patient names/IDs are hashed before entering the AI context window. The AI sees only "Queue length: 45" and "Department: Records," never PII (Personally Identifiable Information).

On-Prem LLM Option: Use Ollama locally to ensure zero patient data leaves the hospital network.

RBAC: Role-based access control separates "View-Only" for department heads and "Full-Access" for Warren.

Audit Logging: Every script executed by the AI is logged immutably for 7 years (required for medical device compliance).

🧪 Getting Started (Local Development)
Prerequisites
Docker & Docker Compose

Python 3.11+

NVIDIA CUDA (optional, for GPU acceleration)

Quick Install
Clone the repository:

bash
git clone https://github.com/your-org/nightingale-ai.git
cd nightingale-ai
Spin up the core services (InfluxDB, Grafana, Redis):

bash
docker-compose up -d
Install Python dependencies and run the AI Orchestrator:

bash
pip install -r requirements.txt
python orchestrator.py --mode simulate --department records
Access the dashboard at http://localhost:3000 (Default: admin/admin).

Simulating a Network Outage
bash
curl -X POST http://localhost:5000/api/inject_fault \
  -H "Content-Type: application/json" \
  -d '{"device": "Router_V", "fault": "isp_down"}'
Watch the AI auto-failover to 5G in the live logs.

📊 Dashboard Layout (Concept)
Quadrant	Content
Top Left	Live Network Topology (Green = Healthy, Orange = AI Fixing, Red = Needs Warren).
Top Right	Active "Warren Packet" Queue (Physical tasks sorted by Priority & GPS Route).
Bottom Left	Department Heatmap (Shows registration queue stress levels in real-time).
Bottom Right	AI Activity Log (Live feed of scripts being executed and their outcomes).
🤝 Contributing
We welcome contributions! Since this is designed for critical infrastructure, we follow a strict "Test-First" policy.

Fork the repository.

Create a feature branch (git checkout -b feature/auto-reboot-printers).

Write unit tests for your new AI tool function.

Submit a Pull Request.

Areas Needing Help:

More SNMP OID mappings for different printer brands.

Additional LLM prompt engineering for better root-cause accuracy.

Mobile app (Flutter/React Native) for Warren's on-the-go dashboard.

📜 License
Distributed under the MIT License. See LICENSE for more information.
(Note: If you use Azure OpenAI, ensure your enterprise agreement covers healthcare workloads).

🙏 Acknowledgments
Inspired by the real-world struggles of hospital IT admins with a "Bus Factor of 1."

Built on the shoulders of open-source giants: Prometheus, LangChain, and Ollama.

Special thanks to the ICT departments who allowed us to study their ticket logs (anonymized).


    
    K[Admin Dashboard - Grafana] -->|Visualizes| E
    K -->|Thumbs Up/Down| I
