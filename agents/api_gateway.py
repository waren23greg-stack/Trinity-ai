# agents/api_gateway.py
"""
Nightingale-AI API Gateway
The front door for manual tickets, webhooks, and status queries.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from enum import Enum

from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, field_validator
import paho.mqtt.client as mqtt
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)

# ===== PYDANTIC MODELS =====

class Priority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class TicketCategory(str, Enum):
    HARDWARE = "HARDWARE"
    SOFTWARE = "SOFTWARE"
    NETWORK = "NETWORK"
    PRINTER = "PRINTER"
    CCTV = "CCTV"
    OTHER = "OTHER"

class TicketSubmission(BaseModel):
    """Payload from Department Portal when a user submits a ticket."""
    department: str = Field(..., min_length=1, max_length=100)
    submitter_name: str = Field(..., min_length=1, max_length=100)
    submitter_email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    category: TicketCategory
    priority: Priority
    description: str = Field(..., min_length=10, max_length=2000)
    device_id: Optional[str] = None
    symptoms: list[str] = Field(default_factory=list)
    
    @field_validator("description")
    @classmethod
    def description_must_not_be_spam(cls, v: str) -> str:
        """Blocks the classic 'asdfasdf' tickets."""
        if v.lower().strip() in ["asdf", "test", "hello", "help", "..."]:
            raise ValueError("Please provide a real description of the issue.")
        return v

class TicketResponse(BaseModel):
    """Response returned after ticket submission."""
    ticket_id: str
    status: str
    message: str
    ai_diagnosis_eta_seconds: int = 30

class ZabbixWebhook(BaseModel):
    """Payload from Zabbix alert webhook."""
    host: str
    trigger_name: str
    severity: str
    description: str
    event_id: str
    timestamp: Optional[str] = None

class PrometheusAlert(BaseModel):
    """Payload from Prometheus Alertmanager."""
    status: str
    alerts: list[dict]
    groupLabels: dict
    commonLabels: dict
    commonAnnotations: dict

# ===== APPLICATION SETUP =====

app = FastAPI(
    title="Nightingale-AI API Gateway",
    description="The front door for hospital IT operations",
    version="1.0.0"
)

# Rate limiter (prevents API abuse)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS (allow Streamlit dashboard to call this API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "https://nightingale.hospital.local"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API key auth (simple for now; swap for JWT in production)
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=True)
VALID_API_KEYS = {
    "department-portal": "dept-portal-secret-key",
    "warren-dashboard": "warren-dashboard-key",
    "zabbix-webhook": "zabbix-secret-key",
}

async def verify_api_key(api_key: str = Depends(API_KEY_HEADER)) -> str:
    """Validates the API key and returns the calling client name."""
    for client_name, valid_key in VALID_API_KEYS.items():
        if api_key == valid_key:
            return client_name
    raise HTTPException(status_code=401, detail="Invalid API key")

# MQTT client (publishes tickets to orchestrator queue)
mqtt_client = mqtt.Client(client_id="nightingale-api")
mqtt_client.connect("localhost", 1883)
mqtt_client.loop_start()

# ===== ENDPOINTS =====

@app.get("/api/health")
async def health_check():
    """Liveness probe for load balancer."""
    return {
        "status": "healthy",
        "service": "nightingale-api-gateway",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/api/tickets", response_model=TicketResponse, status_code=202)
@limiter.limit("10/minute")  # Prevent ticket spam
async def submit_ticket(
    ticket: TicketSubmission,
    background_tasks: BackgroundTasks,
    client_name: str = Depends(verify_api_key)
):
    """
    Accepts a manual ticket from the Department Portal.
    Publishes to MQTT, returns immediately (async processing).
    """
    ticket_id = f"TKT-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{hash(ticket.description) % 10000:04d}"
    
    logger.info(f"[{ticket_id}] Ticket from {ticket.department}: {ticket.category} - {ticket.priority}")
    
    # Publish to orchestrator queue
    message = {
        "type": "manual_ticket",
        "ticket_id": ticket_id,
        "source": "department_portal",
        "submitted_by": client_name,
        "payload": ticket.model_dump()
    }
    mqtt_client.publish(
        topic=f"nightingale/tickets/{ticket.department}",
        payload=str(message),
        qos=1
    )
    
    return TicketResponse(
        ticket_id=ticket_id,
        status="queued",
        message=f"Ticket received. AI is diagnosing now. You'll be notified at {ticket.submitter_email}.",
        ai_diagnosis_eta_seconds=30
    )

@app.get("/api/tickets/{ticket_id}")
async def get_ticket_status(ticket_id: str, client_name: str = Depends(verify_api_key)):
    """Queries the status of a specific ticket."""
    # In production: query the orchestrator's ticket database
    return {
        "ticket_id": ticket_id,
        "status": "in_progress",
        "ai_diagnosis": "Pending AI analysis...",
        "warren_packet": None
    }

@app.get("/api/tickets")
async def list_tickets(
    status: Optional[str] = None,
    department: Optional[str] = None,
    limit: int = 50,
    client_name: str = Depends(verify_api_key)
):
    """Lists open tickets with optional filters."""
    # In production: query the ticket database with filters
    return {"tickets": [], "total": 0, "filters": {"status": status, "department": department}}

@app.get("/api/devices")
async def list_devices(client_name: str = Depends(verify_api_key)):
    """
    Returns live status of all devices (sourced from InfluxDB).
    """
    # In production: query InfluxDB for latest metrics per device
    return {"devices": [], "total": 0}

@app.get("/api/devices/{device_id}")
async def get_device(device_id: str, client_name: str = Depends(verify_api_key)):
    """Returns full details for a single device."""
    return {"device_id": device_id, "status": "unknown"}

@app.post("/api/webhooks/zabbix", status_code=202)
async def receive_zabbix_alert(alert: ZabbixWebhook, client_name: str = Depends(verify_api_key)):
    """
    Receives alerts from Zabbix. Forwards to orchestrator.
    """
    logger.warning(f"Zabbix alert: {alert.trigger_name} on {alert.host} ({alert.severity})")
    
    message = {
        "type": "monitoring_alert",
        "source": "zabbix",
        "severity": alert.severity,
        "host": alert.host,
        "trigger": alert.trigger_name,
        "description": alert.description,
        "payload": alert.model_dump()
    }
    mqtt_client.publish(topic="nightingale/alerts", payload=str(message), qos=1)
    
    return {"status": "received", "alert_id": alert.event_id}

@app.post("/api/webhooks/prometheus", status_code=202)
async def receive_prometheus_alert(alert: PrometheusAlert, client_name: str = Depends(verify_api_key)):
    """
    Receives alerts from Prometheus Alertmanager.
    """
    logger.warning(f"Prometheus alert: {alert.status} — {len(alert.alerts)} alerts")
    
    for a in alert.alerts:
        message = {
            "type": "monitoring_alert",
            "source": "prometheus",
            "status": alert.status,
            "labels": alert.commonLabels,
            "annotations": alert.commonAnnotations,
            "alert": a
        }
        mqtt_client.publish(topic="nightingale/alerts", payload=str(message), qos=1)
    
    return {"status": "received", "alert_count": len(alert.alerts)}

@app.get("/api/warren-packets")
async def list_warren_packets(
    resolved: bool = False,
    client_name: str = Depends(verify_api_key)
):
    """Lists all Warren Packets (pending physical fixes)."""
    return {"packets": [], "total": 0}

@app.get("/api/warren-packets/{packet_id}")
async def get_warren_packet(packet_id: str, client_name: str = Depends(verify_api_key)):
    """Returns full Warren Packet details for Warren's dashboard."""
    return {"packet_id": packet_id, "status": "pending"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
