"""
Nightingale-AI SNMP Poller
Continuously polls network devices and pushes telemetry to InfluxDB + MQTT.
"""

import asyncio
import logging
import yaml
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional

from pysnmp.hlapi.asyncio import (
    SnmpEngine, CommunityData, UdpTransportTarget,
    ContextData, ObjectType, ObjectIdentity, getCmd
)
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

@dataclass
class DeviceConfig:
    """Configuration for a single polled device."""
    device_id: str
    ip_address: str
    device_type: str
    profile: str
    community: str = "public"
    snmp_version: str = "2c"
    poll_interval: int = 60
    location: str = "unknown"
    department: str = "unknown"

@dataclass
class SNMPResult:
    """Result of a single SNMP poll."""
    device_id: str
    metric: str
    value: float | str
    timestamp: float
    success: bool
    error: Optional[str] = None

class SNMPPoller:
    """
    The silent observer. Polls devices and publishes telemetry.
    """
    
    def __init__(self, config_path: str = "config/devices.yaml"):
        self.devices = self._load_device_configs(config_path)
        self.profiles = self._load_device_profiles()
        self.snmp_engine = SnmpEngine()
        
        # InfluxDB client (for time-series storage)
        self.influx = InfluxDBClient(
            url="http://localhost:8086",
            token="nightingale-token",
            org="hospital"
        )
        self.influx_writer = self.influx.write_api(write_options=ASYNCHRONOUS)
        
        # MQTT client (for real-time alerting)
        self.mqtt = mqtt.Client(client_id="nightingale-poller")
        self.mqtt.connect("localhost", 1883)
        self.mqtt.loop_start()
    
    def _load_device_configs(self, path: str) -> list[DeviceConfig]:
        """Loads device list from YAML."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return [DeviceConfig(**d) for d in data["devices"]]
    
    def _load_device_profiles(self) -> dict:
        """Loads OID mappings for each device type."""
        profiles = {}
        for profile_file in Path("config/device_profiles").glob("*.yml"):
            with open(profile_file) as f:
                profiles[profile_file.stem] = yaml.safe_load(f)
        return profiles
    
    async def poll_all(self) -> list[SNMPResult]:
        """
        Polls every device in parallel. Returns list of results.
        """
        tasks = [self._poll_device(device) for device in self.devices]
        results_nested = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten and filter errors
        results = []
        for r in results_nested:
            if isinstance(r, Exception):
                logger.error(f"Poll task crashed: {r}")
                continue
            results.extend(r)
        
        return results
    
    async def _poll_device(self, device: DeviceConfig) -> list[SNMPResult]:
        """
        Polls a single device across all its configured OIDs.
        """
        profile = self.profiles.get(device.profile)
        if not profile:
            logger.warning(f"No profile found for {device.device_id} ({device.profile})")
            return []
        
        results = []
        for metric_name, oid in profile["oids"].items():
            result = await self._snmp_get(device, metric_name, oid)
            results.append(result)
            
            # Check for threshold violations and publish alerts
            if result.success:
                self._check_thresholds(device, result)
        
        # Write all results to InfluxDB
        self._write_to_influx(device, results)
        
        return results
    
    async def _snmp_get(self, device: DeviceConfig, metric: str, oid: str) -> SNMPResult:
        """
        Performs a single SNMP GET request.
        """
        try:
            error_indication, error_status, error_index, var_binds = await getCmd(
                self.snmp_engine,
                CommunityData(device.community, mpModel=1 if device.snmp_version == "2c" else 3),
                UdpTransportTarget((device.ip_address, 161), timeout=2.0, retries=2),
                ContextData(),
                ObjectType(ObjectIdentity(oid))
            )
            
            if error_indication or error_status:
                return SNMPResult(
                    device_id=device.device_id,
                    metric=metric,
                    value=0,
                    timestamp=datetime.now(timezone.utc).timestamp(),
                    success=False,
                    error=str(error_indication or error_status)
                )
            
            # Extract the value
            value = var_binds[0][1]
            
            return SNMPResult(
                device_id=device.device_id,
                metric=metric,
                value=str(value),
                timestamp=datetime.now(timezone.utc).timestamp(),
                success=True
            )
        
        except Exception as e:
            logger.error(f"SNMP GET failed for {device.device_id}/{metric}: {e}")
            return SNMPResult(
                device_id=device.device_id,
                metric=metric,
                value=0,
                timestamp=datetime.now(timezone.utc).timestamp(),
                success=False,
                error=str(e)
            )
    
    def _check_thresholds(self, device: DeviceConfig, result: SNMPResult):
        """
        Compares metric against thresholds and publishes MQTT alerts.
        """
        thresholds = {
            "cpu_load": 90.0,       # >90% = warning
            "memory_usage": 85.0,    # >85% = warning
            "fuser_temp": 200.0,     # >200°C = critical
            "toner_level": 10.0,     # <10% = warning
            "paper_level": 5.0,      # <5% = warning
        }
        
        if result.metric not in thresholds:
            return
        
        threshold = thresholds[result.metric]
        try:
            value = float(result.value)
        except (ValueError, TypeError):
            return
        
        # Direction of concern depends on metric
        if result.metric in ["toner_level", "paper_level"]:
            violated = value < threshold  # Low is bad
        else:
            violated = value > threshold  # High is bad
        
        if violated:
            alert = {
                "device_id": device.device_id,
                "device_type": device.device_type,
                "department": device.department,
                "location": device.location,
                "metric": result.metric,
                "value": value,
                "threshold": threshold,
                "severity": "CRITICAL" if result.metric == "fuser_temp" else "WARNING",
                "timestamp": result.timestamp
            }
            
            # Publish to MQTT topic — orchestrator subscribes to this
            self.mqtt.publish(
                topic=f"nightingale/alerts/{device.department}",
                payload=str(alert),
                qos=1
            )
            
            logger.warning(f"Threshold violated: {alert}")
    
    def _write_to_influx(self, device: DeviceConfig, results: list[SNMPResult]):
        """
        Writes batch of results to InfluxDB for historical trending.
        """
        points = []
        for r in results:
            if not r.success:
                continue
            
            point = (
                Point("device_metrics")
                .tag("device_id", r.device_id)
                .tag("device_type", device.device_type)
                .tag("department", device.department)
                .tag("location", device.location)
                .field(r.metric, self._coerce_value(r.value))
                .time(r.timestamp, write_precision="s")
            )
            points.append(point)
        
        if points:
            self.influx_writer.write(bucket="nightingale", record=points)
    
    @staticmethod
    def _coerce_value(value: str) -> float | int | str:
        """Tries to convert SNMP string values to numbers."""
        try:
            return float(value)
        except (ValueError, TypeError):
            return value


async def main():
    """Entry point: runs the poller on a continuous loop."""
    poller = SNMPPoller()
    
    while True:
        logger.info(f"Polling {len(poller.devices)} devices...")
        results = await poller.poll_all()
        
        success_count = sum(1 for r in results if r.success)
        logger.info(f"Poll complete: {success_count}/{len(results)} successful")
        
        await asyncio.sleep(60)  # Poll every 60 seconds


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
