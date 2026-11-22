"""
Nightingale-AI War Room Dashboard
The single-pane-of-glass for Warren (the lone ICT admin).
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ===== CONFIG =====
API_BASE = "http://localhost:8000/api"
API_KEY = st.secrets["api"]["warren_dashboard_key"]
REFRESH_INTERVAL_MS = 5000  # 5 seconds

st.set_page_config(
    page_title="Nightingale — War Room",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Auto-refresh every 5 seconds (live updates)
st_autorefresh(interval=REFRESH_INTERVAL_MS, key="war_room_refresh")


# ===== API HELPERS =====
@st.cache_data(ttl=5)
def fetch_devices():
    """Fetches device status from API."""
    resp = requests.get(
        f"{API_BASE}/devices",
        headers={"X-API-Key": API_KEY},
        timeout=5
    )
    return resp.json() if resp.ok else {"devices": [], "total": 0}


@st.cache_data(ttl=5)
def fetch_warren_packets():
    """Fetches pending Warren Packets (physical tasks)."""
    resp = requests.get(
        f"{API_BASE}/warren-packets",
        headers={"X-API-Key": API_KEY},
        timeout=5
    )
    return resp.json() if resp.ok else {"packets": [], "total": 0}


@st.cache_data(ttl=5)
def fetch_tickets():
    """Fetches open tickets (from department portal + AI)."""
    resp = requests.get(
        f"{API_BASE}/tickets",
        headers={"X-API-Key": API_KEY},
        timeout=5
    )
    return resp.json() if resp.ok else {"tickets": [], "total": 0}


@st.cache_data(ttl=10)
def fetch_ai_activity():
    """Fetches the live AI activity log."""
    resp = requests.get(
        f"{API_BASE}/activity",
        headers={"X-API-Key": API_KEY},
        timeout=5
    )
    return resp.json() if resp.ok else {"events": []}


# ===== HEADER =====
st.markdown("# 🏥 Nightingale — War Room")
st.markdown(
    f"*Last updated: {datetime.now().strftime('%H:%M:%S')} — auto-refresh every 5s*"
)

# Quick status bar
devices = fetch_devices()
packets = fetch_warren_packets()
tickets = fetch_tickets()

col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("Devices Online", f"{devices.get('total', 0)}")
col_b.metric("Warren Packets", f"{packets.get('total', 0)}", 
             delta="needs physical" if packets.get('total', 0) > 0 else "none")
col_c.metric("Open Tickets", f"{tickets.get('total', 0)}")
col_d.metric("System Health", "🟢 HEALTHY")


# ===== MAIN 2x2 GRID =====
st.markdown("---")

row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)


# --- QUADRANT 1: Network Topology (Placeholder) ---
with row1_col1:
    st.markdown("### 🌐 Network Topology")
    st.info("Live topology map goes here (see `topology.py` in future).")
    
    # Quick status per device type
    device_types = {}
    for d in devices.get("devices", []):
        dtype = d.get("type", "unknown")
        device_types[dtype] = device_types.get(dtype, 0) + 1
    
    for dtype, count in device_types.items():
        st.metric(dtype.capitalize(), count)


# --- QUADRANT 2: Warren Packets Queue ---
with row1_col2:
    st.markdown("### 📋 Pending Physical Tasks")
    packets_data = packets.get("packets", [])
    
    if not packets_data:
        st.success("✅ No physical tasks pending. Enjoy your coffee.")
    else:
        for pkt in packets_data[:3]:  # Show top 3
            priority = pkt.get("priority", "MEDIUM")
            icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(priority, "⚪")
            
            with st.expander(f"{icon} {pkt.get('summary', 'Unknown')}", expanded=True):
                st.write(f"**Device:** {pkt.get('device', {}).get('id', 'N/A')}")
                st.write(f"**Location:** {pkt.get('device', {}).get('location', 'N/A')}")
                st.write(f"**AI Confidence:** {pkt.get('root_cause', {}).get('confidence', 0.0):.0%}")
                st.write(f"**ETA:** {pkt.get('prescription', {}).get('estimated_fix_time_minutes', 'N/A')} min")
        
        if len(packets_data) > 3:
            st.caption(f"+ {len(packets_data) - 3} more. See **Warren Queue** page →")


# --- QUADRANT 3: Department Heatmap (link) ---
with row2_col1:
    st.markdown("### 🔥 Department Stress Levels")
    st.info("Click **Heatmap** in the sidebar for full view.")
    
    # Show top 3 stressed departments
    stressed = tickets.get("stressed_departments", [])
    if not stressed:
        st.success("✅ All departments below threshold.")
    else:
        for dept in stressed[:3]:
            st.warning(f"⚠️ **{dept['name']}** — Queue: {dept['queue_length']} patients")


# --- QUADRANT 4: AI Activity Log ---
with row2_col2:
    st.markdown("### 🤖 AI Activity Log")
    activity = fetch_ai_activity().get("events", [])
    
    if not activity:
        st.caption("No AI activity in the last 15 minutes.")
    else:
        for event in activity[-5:]:  # Show last 5 events
            timestamp = event.get("timestamp", "")
            status = event.get("status", "unknown")
            message = event.get("message", "")
            
            if status == "success":
                st.success(f"✅ `{timestamp}` — {message}")
            elif status == "failure":
                st.error(f"❌ `{timestamp}` — {message}")
            else:
                st.info(f"ℹ️ `{timestamp}` — {message}")


# ===== SIDEBAR NAVIGATION =====
with st.sidebar:
    st.markdown("# 🧭 Navigation")
    st.page_link("app.py", label="🏥 War Room", icon="🏥")
    st.page_link("pages/heatmap.py", label="🔥 Department Heatmap", icon="🔥")
    st.page_link("pages/warren_queue.py", label="📋 Warren Queue", icon="📋")
    
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    
    if st.button("🔄 Force Refresh"):
        st.cache_data.clear()
        st.rerun()
    
    if st.button("📥 Export Warren Packet (JSON)"):
        st.download_button(
            label="Download",
            data=json.dumps(packets, indent=2),
            file_name=f"warren_packets_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json"
        )
    
    st.markdown("---")
    st.caption("Nightingale-AI v1.0 | Built for Warren")
