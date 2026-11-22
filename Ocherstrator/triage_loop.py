"""
Nightingale-AI Try-Fail-Escalate Loop
Executes remediation scripts and evaluates results.
Maximum 3 attempts before escalation.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Optional
from .ai_engine import NightingaleEngine
from .warren_packet import generate_packet

logger = logging.getLogger(__name__)

@dataclass
class TriageAttempt:
    """Records a single remediation attempt."""
    attempt_number: int
    script_name: str
    executed_at: float
    result: str  # "success" | "failure" | "partial"
    error_output: Optional[str] = None
    duration_seconds: float = 0.0

@dataclass
class TriageSession:
    """Tracks the full lifecycle of an incident."""
    incident_id: str
    device_id: str
    telemetry: dict
    attempts: list = field(default_factory=list)
    max_attempts: int = 3
    escalated: bool = False
    resolved: bool = False

class TriageLoop:
    """
    The execution engine. Runs scripts, evaluates results, escalates when needed.
    """
    
    def __init__(self, ai_engine: NightingaleEngine):
        self.ai = ai_engine
        self.active_sessions = {}
    
    def run(self, incident_id: str, device_id: str, telemetry: dict) -> dict:
        """
        Main entry point. Runs the full triage loop for an incident.
        Returns a dict with final status and (if escalated) Warren Packet.
        """
        session = TriageSession(
            incident_id=incident_id,
            device_id=device_id,
            telemetry=telemetry
        )
        self.active_sessions[incident_id] = session
        
        logger.info(f"[{incident_id}] Starting triage for {device_id}")
        
        for attempt_num in range(1, session.max_attempts + 1):
            logger.info(f"[{incident_id}] Attempt {attempt_num}/{session.max_attempts}")
            
            # Step 1: Ask AI to diagnose (first attempt) or suggest alternative (subsequent)
            if attempt_num == 1:
                diagnosis = self.ai.diagnose(telemetry)
            else:
                diagnosis = self.ai.diagnose_with_context(
                    telemetry,
                    previous_attempts=session.attempts
                )
            
            # Step 2: Check if AI has already given up
            if diagnosis.get("should_escalate"):
                logger.warning(f"[{incident_id}] AI recommends immediate escalation")
                return self._escalate(session, reason=diagnosis.get("reason", "AI gave up"))
            
            # Step 3: Execute the recommended script
            script = diagnosis.get("script")
            if not script:
                logger.error(f"[{incident_id}] AI returned no script. Escalating.")
                return self._escalate(session, reason="No script returned by AI")
            
            attempt = self._execute_script(
                incident_id=incident_id,
                script_name=script,
                attempt_number=attempt_num
            )
            session.attempts.append(attempt)
            
            # Step 4: Evaluate success
            if attempt.result == "success":
                logger.info(f"[{incident_id}] RESOLVED on attempt {attempt_num} via {script}")
                session.resolved = True
                return {
                    "status": "resolved",
                    "incident_id": incident_id,
                    "attempts": attempt_num,
                    "script_used": script,
                    "duration": sum(a.duration_seconds for a in session.attempts)
                }
            
            # Step 5: Brief pause before next attempt (avoid hammering the device)
            time.sleep(5)
        
        # All attempts failed — escalate
        logger.error(f"[{incident_id}] All {session.max_attempts} attempts failed. Escalating.")
        return self._escalate(session, reason="Max attempts exhausted")
    
    def _execute_script(self, incident_id: str, script_name: str, attempt_number: int) -> TriageAttempt:
        """
        Executes a script via Ansible AWX or local subprocess.
        Returns a TriageAttempt with the result.
        """
        start_time = time.time()
        
        try:
            # In production: call Ansible AWX API or run subprocess
            # For now, simulate execution
            if script_name.endswith(".yml"):
                output = self._run_ansible_playbook(script_name)
            elif script_name.endswith(".ps1"):
                output = self._run_powershell(script_name)
            elif script_name.endswith(".py"):
                output = self._run_python(script_name)
            else:
                raise ValueError(f"Unknown script type: {script_name}")
            
            duration = time.time() - start_time
            
            # Evaluate success (in production: check service status, ping device, etc.)
            success = self._verify_fix(script_name, output)
            
            return TriageAttempt(
                attempt_number=attempt_number,
                script_name=script_name,
                executed_at=start_time,
                result="success" if success else "failure",
                error_output=None if success else output,
                duration_seconds=duration
            )
        
        except Exception as e:
            logger.error(f"[{incident_id}] Script {script_name} crashed: {e}")
            return TriageAttempt(
                attempt_number=attempt_number,
                script_name=script_name,
                executed_at=start_time,
                result="failure",
                error_output=str(e),
                duration_seconds=time.time() - start_time
            )
    
    def _verify_fix(self, script_name: str, output: str) -> bool:
        """
        Verifies that the script actually fixed the issue.
        This is the CRITICAL step that prevents false positives.
        """
        # Implementation: ping the device, query service status, check error codes
        # For now, return True if output doesn't contain "ERROR"
        return "ERROR" not in output.upper()
    
    def _escalate(self, session: TriageSession, reason: str) -> dict:
        """
        Generates a Warren Packet and returns the escalation result.
        """
        session.escalated = True
        packet = generate_packet(
            incident_id=session.incident_id,
            device_id=session.device_id,
            telemetry=session.telemetry,
            attempts=session.attempts,
            reason=reason
        )
        
        logger.warning(f"[{session.incident_id}] ESCALATED: {packet['summary']}")
        
        return {
            "status": "escalated",
            "incident_id": session.incident_id,
            "warren_packet": packet
        }
    
    # ===== SCRIPT EXECUTION HELPERS =====
    
    def _run_ansible_playbook(self, playbook: str) -> str:
        """Runs an Ansible playbook via AWX API."""
        pass
    
    def _run_powershell(self, script: str) -> str:
        """Runs a PowerShell script on a remote Windows machine."""
        pass
    
    def _run_python(self, script: str) -> str:
        """Runs a Python script (e.g., PoE cycling)."""
        pass
