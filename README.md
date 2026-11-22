🏥 Nightingale-AI: The Self-Healing Hospital Ops Engine
https://img.shields.io/badge/License-MIT-yellow.svg
https://img.shields.io/badge/python-3.11+-blue.svg
https://img.shields.io/badge/LangChain-Framework-green
https://img.shields.io/badge/Docker-Ready-blue

Stop fighting fires. Start commanding your infrastructure.

Nightingale is an AI-driven, cloud-native command center designed for single-administrator IT teams in high-pressure environments (Hospitals, Logistics Hubs, or Multi-site Campuses). It bridges the gap between automated scripting and physical attendance by using a Generative AI Triage Engine that autonomously resolves 80% of network, hardware, and software issues—escalating only the unsolvable 20% to your human expert with forensic-level detail.

📌 Table of Contents
The Problem We Solve

Core Features

System Architecture

Repository Structure

Deep Dive: The Orchestrator

Deep Dive: The Agents

Deep Dive: The Scripts

Deep Dive: The Frontend

Scale Matrix: Customization by Facility Size

Tech Stack

How It Works: The Triage Pipeline

Privacy & Security (HIPAA / GDPR Ready)

Getting Started (Local Development)

Contributing

License

Acknowledgments

🚀 The Problem We Solve
The "Bus Factor" of 1: One IT admin managing 200+ departments and 500+ daily patients.

Context Switching: Running between a printer jam, a crashed PC, and a downed router simultaneously.

Blind Alerts: Getting a ticket that says "Internet is slow" with zero diagnostic context.

Nightingale transforms this chaos into a single-pane-of-glass where the AI acts as your tireless Level-1 & Level-2 support, leaving you only the physical, mechanical tasks.

✨ Core Features
1. Generative AI Root-Cause Analysis
Uses Chain-of-Thought (CoT) reasoning via a locally-hosted LLM (Ollama/LLaMA) or Azure OpenAI.

Instead of hardcoded "If/Then" rules, the AI reads live telemetry, hypothesizes the fault (e.g., "Broadcast Storm" vs. "ISP Outage"), and selects the correct remediation script.

2. The "Try-Fail-Escalate" Loop
The AI executes up to 3 automated attempts (e.g., Restart Service → Reinstall Driver → Network Stack Reset).

If attempts fail, the AI halts automation and generates a "Warren Packet"—a forensic report including root cause probability, suggested spare parts, and estimated physical fix time.

3. Automated Network Failover & Device Resuscitation
SD-WAN Auto-Failover: Detects ISP failure and instantly routes traffic through a 4G/5G USB dongle.

PoE Cycling: Remotely power-cycles CCTV cameras and dead access points via managed switch APIs.

VDI Auto-Scaling: Spins up temporary cloud desktops during patient registration spikes to eliminate queues.

4. Department Self-Service "Frustration Portal"
A lightweight web/mobile interface for nurses and doctors to report issues the AI hasn't detected (e.g., "My mouse is lagging").

The AI runs instant diagnostics and either fixes the issue (e.g., switching Wi-Fi bands) or adds context to Warren's physical route.

5. Self-Learning Feedback Loop
Warren tags resolved tickets as "AI was Right" or "AI was Wrong."

The system vectorizes voice/text notes and updates the AI's knowledge base overnight, ensuring it gets smarter every day.

🏗️ System Architecture

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
    
    K[Admin Dashboard - Streamlit] -->|Visualizes| E
    K -->|Thumbs Up/Down| I
    
📂 Repository Structure
text
nightingale-ai/
├── README.md                  # This file
├── LICENSE                    # MIT License
├── .gitignore                 # Python, Docker, .env
├── docker-compose.yml         # Full stack (InfluxDB, Grafana, Redis, Mosquitto)
├── requirements.txt           # Python dependencies
│
├── orchestrator/              # 🧠 Core AI Logic
│   ├── ai_engine.py           # LangChain ReAct agent (thinking layer)
│   ├── triage_loop.py         # Try-Fail-Escalate logic (doing layer)
│   └── warren_packet.py       # Forensic report generator (confession layer)
│
├── agents/                    # 👁️ Telemetry Collectors
│   ├── snmp_poller.py         # Silent observer (polls devices every 60s)
│   └── api_gateway.py         # Front door (REST API for tickets & webhooks)
│
├── scripts/                   # 🛠️ Remediation Playbooks
│   ├── network/
│   │   ├── failover_5g.yml    # Reroute traffic to cellular backup
│   │   └── stp_recalculate.yml # Fix network loops via Spanning Tree
│   ├── printers/
│   │   ├── restart_spooler.ps1 # Restart Windows Print Spooler
│   │   └── reinstall_driver.yml # Nuke and reinstall printer driver
│   └── cctv/
│       └── poe_cycle.py       # Power-cycle PoE cameras via switch API
│
├── frontend/                  # 🖥️ Streamlit Dashboard
│   ├── app.py                 # War Room (4-quadrant overview)
│   └── pages/
│       ├── heatmap.py         # Department stress heatmap
│       └── warren_queue.py    # Physical task queue + GPS route
│
├── config/                    # ⚙️ Configuration
│   ├── devices.yaml           # Device inventory (IPs, types, locations)
│   ├── device_profiles/       # Vendor-specific OID mappings
│   └── scripts.yaml           # Script registry (metadata, timeouts)
│
├── tests/                     # 🧪 Unit Tests
│   ├── test_network_tools.py
│   └── test_printer_tools.py
│
└── docs/                      # 📚 Documentation
    ├── architecture.md
    ├── deployment_scale.md
    └── hipaa_compliance.md
🧠 Deep Dive: The Orchestrator
The orchestrator/ directory is the brain of the entire operation. Without it, Nightingale is just a fancy dashboard. With it, Nightingale becomes a tireless digital teammate that thinks, acts, fails, learns, and—when all else fails—writes a beautifully detailed "I give up" letter to Warren.

ai_engine.py — The LangChain ReAct Agent
Receives raw telemetry (e.g., "Router V offline," "Printer E error code 0x8F")

Retrieves similar past incidents from the vector database

Uses Chain-of-Thought reasoning to hypothesize root cause and select remediation script

Guardrails: Never executes destructive scripts without human approval

Tool-Based Architecture: Only interacts with the world through registered tools

triage_loop.py — The Try-Fail-Escalate Logic
Takes the AI's diagnosis, runs the recommended script, evaluates the result

Maximum 3 attempts before escalation

Verification step: Never declares victory without proof (ping, service status, error code check)

Session tracking: Every incident has a full audit trail

warren_packet.py — The Forensic Report Generator
When AI exhausts attempts, generates a Warren Packet for physical intervention

Includes: root cause probability, all attempted fixes, suggested spare parts, estimated fix time, GPS-optimized route

Push notification ready: SMS/email summary for Warren's phone

👁️ Deep Dive: The Agents
The agents/ directory is the nervous system—how Nightingale perceives the world.

snmp_poller.py — The Silent Observer
Polls every network-connected device every 60 seconds via SNMP

Vendor-agnostic: Device Profile YAML files map friendly metric names to vendor-specific OIDs

Async & parallel: Polls 200+ devices in ~2 seconds

Dual output: Time-series data (InfluxDB) for trending; MQTT alerts for immediate action

Threshold intelligence: Detects violations before the AI needs to diagnose (predictive maintenance)

api_gateway.py — The Front Door
REST API for manual tickets, webhooks, and status queries

Endpoints: /api/tickets, /api/devices, /api/warren-packets, /api/webhooks/zabbix, /api/webhooks/prometheus

Rate limiting: Prevents ticket spam

API key auth: Separates Department Portal, Warren Dashboard, and monitoring webhooks

Webhook normalization: Zabbix and Prometheus alerts become indistinguishable to the orchestrator

Async by default: Returns 202 Accepted immediately—AI diagnosis happens in background

🛠️ Deep Dive: The Scripts
The scripts/ directory is the muscle—where the AI stops thinking and starts doing.

The "Script Contract" (Every Script Must Follow)
Rule	Rationale
Return structured JSON	Orchestrator needs status, error, and metadata to make decisions
Be idempotent	Running twice must not cause double-restarts or data loss
Verify your own work	Never return success without proof
Fail loudly	Never swallow errors. Return the exact error message
Timeout gracefully	Never hang indefinitely
No destructive operations	No rm -rf, no format without explicit human approval
Log everything	Every action is logged for auditing
Script Inventory
Script	Purpose	Idempotent?	Self-Verifying?
network/failover_5g.yml	Reroute traffic to 5G when ISP drops	✅ Checks current route	✅ Pings internet via backup
network/stp_recalculate.yml	Fix network loops via STP	✅ Only if topology changes > 10	✅ Pings downstream cameras
printers/restart_spooler.ps1	Restart Windows Print Spooler	✅ Checks if already running	✅ Verifies service state
printers/reinstall_driver.yml	Nuke and reinstall printer driver	✅ Full rebuild	✅ Prints test page
cctv/poe_cycle.py	Power-cycle PoE cameras	✅ Pings camera first	✅ Waits for camera boot
🖥️ Deep Dive: The Frontend
The frontend/ directory is Warren's Second Brain—a single-pane-of-glass that tells him exactly three things:

What is the AI fixing right now? (so he can relax)

What does the AI need him to physically do? (so he can plan his walk)

What is about to explode? (so he can preemptively put out the fire)

app.py — The War Room
Four quadrants: Network topology, Warren Packets queue, Department heatmap, AI activity log

5-second scan: Everything fits on one screen. No scrolling required.

Auto-refresh every 5 seconds: No stale data

Color-coded severity: 🔴 CRITICAL, 🟠 HIGH, 🟡 MEDIUM, 🟢 LOW

pages/heatmap.py — Department Stress Map
Treemap visualization: Size = queue length, color = stress level

Drill-down: Click any department to see individual tickets and device status

Live refresh: 10-second auto-refresh

Answers: "Which department is under pressure right now?"

pages/warren_queue.py — Physical Task Queue
Priority sorting: CRITICAL → HIGH → MEDIUM → LOW

GPS-optimized route: Single-trip plan to fix all tasks

Full context: Root cause hypothesis, attempted fixes, exact prescription

One-click resolve: Feeds the AI's self-learning loop

📦 Scale Matrix: Customization by Facility Size
Nightingale is modular. You can deploy the Core AI Brain everywhere, but scale the telemetry agents based on your bed count.

Facility Type	Daily Patients	Departments	Recommended Deployment	Hardware Requirements
Small Clinic	< 100	< 20	Single Docker Container + Ollama (CPU-only mode). No on-prem switches required.	8GB RAM, 4 vCPUs
Medium Hospital	100 - 500	50 - 100	Kubernetes cluster (3 nodes). Deploy LLM with GPU (NVIDIA T4). Implement PoE switching.	32GB RAM, 8 vCPUs, 8GB VRAM
Large Tertiary	500 - 1,000+	200+	High-Availability Cloud (Azure/AWS). On-prem Edge Agents for failover. Redundant 5G modems.	128GB RAM, 16 vCPUs, 24GB VRAM (A100)
🛠️ Tech Stack
AI Framework: LangChain + ReAct Agent Pattern

LLM Backend: Ollama (Llama 3.1 70B) or Azure OpenAI (HIPAA-compliant)

Vector DB: Pinecone / Weaviate (for storing past incidents and runbooks)

Script Execution: Ansible AWX (open-source Tower) / PowerShell DSC

Networking: Zabbix + Prometheus exporters for SNMP polling

Message Bus: Mosquitto (MQTT)

Time-Series DB: InfluxDB

Frontend: Streamlit (Dashboard) + Plotly (Visualizations)

Device Tunneling: Azure IoT Hub / AWS IoT Core for secure remote KVM access

🚦 How It Works: The Triage Pipeline
Detection: A sensor detects "Router V Offline" or "Queue > 15 mins."

Hypothesis: The AI queries the Vector DB for similar past incidents.

Attempt 1 (Software): Run Script: restart_network_stack.py → Fails.

Attempt 2 (Logical): Run Script: failover_to_5g.py → Succeeds. Alert auto-resolves.

Failure (Hardware): If "Printer E" fails all scripted fixes, the AI generates an escalation:

"Escalate: Printer E. Thermal sensor reads 50°C. Suspect Fuser Unit. Part #XYZ-123. Spare located in Storage B3. ETA to fix: 12 mins."

🔐 Privacy & Security (HIPAA / GDPR Ready)
Data Anonymization: Patient names/IDs are hashed before entering the AI context window. The AI sees only "Queue length: 45" and "Department: Records," never PII.

On-Prem LLM Option: Use Ollama locally to ensure zero patient data leaves the hospital network.

RBAC: Role-based access control separates "View-Only" for department heads and "Full-Access" for Warren.

Audit Logging: Every script executed by the AI is logged immutably for 7 years (required for medical device compliance).

API Key Rotation: Static keys should be replaced with JWT with 24-hour expiry in production.

Secrets Management: Passwords should come from a secrets manager (Vault, AWS Secrets Manager), not config files.

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
Spin up the core services (InfluxDB, Grafana, Redis, Mosquitto):

bash
docker-compose up -d
Install Python dependencies and run the AI Orchestrator:

bash
pip install -r requirements.txt
python orchestrator.py --mode simulate --department records
Access the dashboard at http://localhost:8501 (Streamlit default).

Simulating a Network Outage
bash
curl -X POST http://localhost:8000/api/inject_fault \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"device": "Router_V", "fault": "isp_down"}'
Watch the AI auto-failover to 5G in the live logs.

Running the Poller
bash
python agents/snmp_poller.py --config config/devices.yaml
Running the API Gateway
bash
uvicorn agents.api_gateway:app --host 0.0.0.0 --port 8000
🤝 Contributing
We welcome contributions! Since this is designed for critical infrastructure, we follow a strict "Test-First" policy.

Fork the repository.

Create a feature branch (git checkout -b feature/auto-reboot-printers).

Write unit tests for your new AI tool function.

Submit a Pull Request.

Areas Needing Help:

More SNMP OID mappings for different printer brands

Additional LLM prompt engineering for better root-cause accuracy

Mobile app (Flutter/React Native) for Warren's on-the-go dashboard

WebSocket support for real-time dashboard updates

SSO integration (Active Directory / OAuth)

📜 License
Distributed under the MIT License. See LICENSE for more information.

(Note: If you use Azure OpenAI, ensure your enterprise agreement covers healthcare workloads).

🙏 Acknowledgments
Inspired by the real-world struggles of hospital IT admins with a "Bus Factor of 1."

Built on the shoulders of open-source giants: Prometheus, LangChain, and Ollama.

Special thanks to the ICT departments who allowed us to study their ticket logs (anonymized).

The Patients of Learning: Every IT admin who owns their mistakes, keeps their cool, and smiles at the impatient boss while swallowing their own disappointment. This is for you.

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

You now have a fully polished, GitHub-ready README with **deep-dive sections for every directory** in your repository. 🚀
