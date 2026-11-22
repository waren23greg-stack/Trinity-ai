"""
Nightingale-AI Warren Packet Generator
Creates forensic escalation reports for human IT staff.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

class WarrenPacketGenerator:
    """
    Generates a "Warren Packet" when the AI gives up.
    The packet contains everything Warren needs to fix the issue physically.
    """
    
    def __init__(self):
        self.packet_counter = 0
    
    def generate(
        self,
        incident_id: str,
        device_id: str,
        telemetry: dict,
        attempts: list,
        reason: str
    ) -> dict:
        """
        Main entry point. Builds a complete Warren Packet.
        """
        self.packet_counter += 1
        packet_id = f"WP-{datetime.now().strftime('%Y-%m-%d')}-{self.packet_counter:03d}"
        
        packet = {
            "packet_id": packet_id,
            "incident_id": incident_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "priority": self._calculate_priority(telemetry),
            "device": self._build_device_info(device_id, telemetry),
            "summary": self._build_summary(device_id, reason),
            "root_cause": self._build_root_cause(telemetry),
            "attempts": self._format_attempts(attempts),
            "prescription": self._build_prescription(device_id, telemetry),
            "workaround": self._build_workaround(telemetry),
            "route": self._build_route(device_id, telemetry),
            "notification": self._build_notification(device_id, reason)
        }
        
        logger.info(f"Generated Warren Packet {packet_id} for {device_id}")
        return packet
    
    def _calculate_priority(self, telemetry: dict) -> str:
        """Determines priority based on department and impact."""
        dept = telemetry.get("department", "").lower()
        if dept in ["er", "icu", "maternity", "surgery"]:
            return "CRITICAL"
        elif dept in ["radiology", "lab", "pharmacy"]:
            return "HIGH"
        else:
            return "MEDIUM"
    
    def _build_device_info(self, device_id: str, telemetry: dict) -> dict:
        """Extracts device metadata."""
        return {
            "id": device_id,
            "type": telemetry.get("device_type", "unknown"),
            "location": telemetry.get("location", "unknown"),
            "department": telemetry.get("department", "unknown"),
            "ip_address": telemetry.get("ip_address", "unknown")
        }
    
    def _build_summary(self, device_id: str, reason: str) -> str:
        """One-line summary for the push notification."""
        return f"{device_id}: {reason}. Automated remediation failed after 3 attempts."
    
    def _build_root_cause(self, telemetry: dict) -> dict:
        """
        Uses telemetry to build a root cause hypothesis.
        In production: call the AI engine to get a confidence score.
        """
        return {
            "hypothesis": telemetry.get("suspected_fault", "unknown"),
            "confidence": telemetry.get("ai_confidence", 0.0),
            "evidence": telemetry.get("evidence", [])
        }
    
    def _format_attempts(self, attempts: list) -> list:
        """Formats the attempts list for the packet."""
        return [
            {
                "attempt": a.attempt_number,
                "script": a.script_name,
                "result": a.result,
                "error": a.error_output,
                "duration_seconds": round(a.duration_seconds, 2)
            }
            for a in attempts
        ]
    
    def _build_prescription(self, device_id: str, telemetry: dict) -> dict:
        """
        Suggests the physical fix, including part numbers and spare locations.
        In production: query a hardware inventory database.
        """
        return {
            "action": telemetry.get("suggested_fix", "Manual inspection required"),
            "part_number": telemetry.get("part_number", "N/A"),
            "spare_location": telemetry.get("spare_location", "N/A"),
            "estimated_fix_time_minutes": telemetry.get("estimated_fix_time", 15),
            "tools_required": telemetry.get("tools_required", [])
        }
    
    def _build_workaround(self, telemetry: dict) -> dict:
        """Describes any active workarounds (e.g., VDI failover)."""
        return {
            "active": telemetry.get("workaround_active", False),
            "description": telemetry.get("workaround_description", "None"),
            "expires_at": telemetry.get("workaround_expires_at", None)
        }
    
    def _build_route(self, device_id: str, telemetry: dict) -> dict:
        """
        Builds a GPS-optimized route for Warren.
        In production: query all pending Warren Packets and sort by priority + proximity.
        """
        return {
            "current_location": "ICT Office",
            "waypoints": [
                {
                    "device": device_id,
                    "location": telemetry.get("location", "unknown"),
                    "priority": self._calculate_priority(telemetry),
                    "estimated_time": telemetry.get("estimated_fix_time", 15)
                }
            ],
            "total_estimated_time_minutes": telemetry.get("estimated_fix_time", 15)
        }
    
    def _build_notification(self, device_id: str, reason: str) -> str:
        """
        Builds the push notification text for Warren's phone.
        """
        return (
            f"🚨 ESCALATION: {device_id}\n"
            f"Reason: {reason}\n"
            f"AI Confidence: {telemetry.get('ai_confidence', 0.0):.0%}\n"
            f"Attempts: 3 (all failed)\n"
            f"Action: Open Nightingale Dashboard for full report."
        )


def generate_packet(incident_id: str, device_id: str, telemetry: dict, attempts: list, reason: str) -> dict:
    """
    Convenience function for triage_loop.py to call.
    """
    generator = WarrenPacketGenerator()
    return generator.generate(incident_id, device_id, telemetry, attempts, reason)
