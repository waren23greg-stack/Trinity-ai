"""
Nightingale-AI: PoE Port Cycling
Power-cycles a PoE port on a managed switch to reboot a CCTV camera.
Supports Cisco, Ubiquiti, and HP switches via their respective APIs.
Returns structured JSON for orchestrator consumption.
"""

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass, asdict
from typing import Optional

import requests
from netmiko import ConnectHandler

logger = logging.getLogger(__name__)


@dataclass
class PoECycleResult:
    """Structured result returned to the orchestrator."""
    status: str  # "success" | "failure"
    action: str = "poe_cycle"
    switch: str = ""
    port: str = ""
    camera_ip: str = ""
    power_off_duration_seconds: int = 10
    camera_online_after_cycle: bool = False
    error: Optional[str] = None
    duration_seconds: float = 0.0


class PoECycler:
    """Base class for PoE cycling across switch vendors."""
    
    def __init__(self, switch_ip: str, username: str, password: str, port: str):
        self.switch_ip = switch_ip
        self.username = username
        self.password = password
        self.port = port
    
    def power_off(self) -> bool:
        raise NotImplementedError
    
    def power_on(self) -> bool:
        raise NotImplementedError
    
    def get_port_status(self) -> str:
        raise NotImplementedError


class CiscoPoECycler(PoECycler):
    """Cisco switch PoE cycling via SSH."""
    
    def _connect(self):
        return ConnectHandler(
            device_type="cisco_ios",
            host=self.switch_ip,
            username=self.username,
            password=self.password,
        )
    
    def power_off(self) -> bool:
        try:
            with self._connect() as conn:
                conn.send_config_set([
                    f"interface {self.port}",
                    "power inline never",  # Disable PoE
                    "shutdown",            # Also shut the port
                ])
            return True
        except Exception as e:
            logger.error(f"Cisco power_off failed: {e}")
            return False
    
    def power_on(self) -> bool:
        try:
            with self._connect() as conn:
                conn.send_config_set([
                    f"interface {self.port}",
                    "no shutdown",
                    "power inline auto",  # Re-enable PoE
                ])
            return True
        except Exception as e:
            logger.error(f"Cisco power_on failed: {e}")
            return False
    
    def get_port_status(self) -> str:
        try:
            with self._connect() as conn:
                output = conn.send_command(f"show interfaces {self.port} status")
                if "connected" in output.lower():
                    return "connected"
                return "down"
        except Exception:
            return "unknown"


class UbiquitiPoECycler(PoECycler):
    """Ubiquiti UniFi switch PoE cycling via REST API."""
    
    BASE_URL = "https://{switch}/api"
    
    def _api_call(self, method: str, endpoint: str, payload: dict = None) -> dict:
        url = self.BASE_URL.format(switch=self.switch_ip) + endpoint
        resp = requests.request(
            method, url,
            json=payload,
            auth=(self.username, self.password),
            verify=False,  # UniFi uses self-signed certs
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()
    
    def power_off(self) -> bool:
        try:
            # UniFi API: set PoE mode to "off"
            self._api_call(
                "PUT",
                f"/s/default/rest/device/{self.port}",
                {"poe_mode": "off"}
            )
            return True
        except Exception as e:
            logger.error(f"UniFi power_off failed: {e}")
            return False
    
    def power_on(self) -> bool:
        try:
            self._api_call(
                "PUT",
                f"/s/default/rest/device/{self.port}",
                {"poe_mode": "auto"}
            )
            return True
        except Exception as e:
            logger.error(f"UniFi power_on failed: {e}")
            return False
    
    def get_port_status(self) -> str:
        try:
            data = self._api_call("GET", f"/s/default/stat/device/{self.port}")
            return "connected" if data.get("state") == 1 else "down"
        except Exception:
            return "unknown"


# Vendor registry
VENDOR_CYCLERS = {
    "cisco": CiscoPoECycler,
    "ubiquiti": UbiquitiPoECycler,
}


def ping_host(ip: str, count: int = 3, timeout: int = 1) -> bool:
    """Pings a host to verify it's online. Returns True if reachable."""
    import subprocess
    try:
        result = subprocess.run(
            ["ping", "-c", str(count), "-W", str(timeout), ip],
            capture_output=True,
            timeout=count * timeout + 5
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False


def cycle_poe(
    vendor: str,
    switch_ip: str,
    username: str,
    password: str,
    port: str,
    camera_ip: str,
    power_off_duration: int = 10,
) -> PoECycleResult:
    """
    Main entry point. Power-cycles a PoE port and verifies camera recovery.
    """
    start_time = time.time()
    result = PoECycleResult(
        status="failure",
        switch=switch_ip,
        port=port,
        camera_ip=camera_ip,
        power_off_duration_seconds=power_off_duration,
    )
    
    # ===== STEP 1: CHECK CAMERA IS ACTUALLY OFFLINE =====
    # Idempotency: don't cycle a camera that's already working.
    if ping_host(camera_ip, count=2, timeout=1):
        logger.info(f"Camera {camera_ip} is already online. No action needed.")
        result.status = "success"
        result.camera_online_after_cycle = True
        result.duration_seconds = time.time() - start_time
        return result
    
    # ===== STEP 2: GET VENDOR-SPECIFIC CYCLER =====
    cycler_class = VENDOR_CYCLERS.get(vendor.lower())
    if not cycler_class:
        result.error = f"Unsupported vendor: {vendor}"
        result.duration_seconds = time.time() - start_time
        return result
    
    cycler = cycler_class(switch_ip, username, password, port)
    
    # ===== STEP 3: POWER OFF =====
    logger.info(f"Powering OFF PoE port {port} on {switch_ip}")
    if not cycler.power_off():
        result.error = "Failed to power off PoE port"
        result.duration_seconds = time.time() - start_time
        return result
    
    # ===== STEP 4: WAIT =====
    logger.info(f"Waiting {power_off_duration}s for camera to fully discharge...")
    time.sleep(power_off_duration)
    
    # ===== STEP 5: POWER ON =====
    logger.info(f"Powering ON PoE port {port} on {switch_ip}")
    if not cycler.power_on():
        result.error = "Failed to power on PoE port"
        result.duration_seconds = time.time() - start_time
        return result
    
    # ===== STEP 6: WAIT FOR CAMERA BOOT =====
    # Cameras take 20-60 seconds to boot after power restoration.
    logger.info(f"Waiting for camera {camera_ip} to boot...")
    for attempt in range(6):  # Up to 60 seconds
        time.sleep(10)
        if ping_host(camera_ip, count=2, timeout=1):
            logger.info(f"Camera {camera_ip} is back online after {(attempt + 1) * 10}s")
            result.status = "success"
            result.camera_online_after_cycle = True
            result.duration_seconds = time.time() - start_time
            return result
        logger.info(f"Camera not yet online (attempt {attempt + 1}/6)")
    
    # ===== STEP 7: FAILURE =====
    result.error = f"Camera {camera_ip} did not come online after PoE cycle. Likely hardware failure."
    result.duration_seconds = time.time() - start_time
    return result


def main():
    parser = argparse.ArgumentParser(description="Nightingale PoE Cycler")
    parser.add_argument("--vendor", required=True, choices=["cisco", "ubiquiti"])
    parser.add_argument("--switch-ip", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--port", required=True, help="Port ID (e.g., 'Gi1/0/5' or '5')")
    parser.add_argument("--camera-ip", required=True)
    parser.add_argument("--power-off-duration", type=int, default=10)
    
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    
    result = cycle_poe(
        vendor=args.vendor,
        switch_ip=args.switch_ip,
        username=args.username,
        password=args.password,
        port=args.port,
        camera_ip=args.camera_ip,
        power_off_duration=args.power_off_duration,
    )
    
    # Output JSON for orchestrator
    print(json.dumps(asdict(result), indent=2))
    sys.exit(0 if result.status == "success" else 1)


if __name__ == "__main__":
    main()
