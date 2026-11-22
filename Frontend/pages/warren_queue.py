"""
Nightingale-AI Warren Queue
Physical task list for Warren, sorted by priority and GPS route.
"""

import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from datetime import datetime

API_BASE = "http://localhost:8000/api"
API_KEY = st.secrets["api"]["warren_dashboard_key"]

st.set_page_config(
    page_title="Nightingale — Warren Queue",
    page_icon="📋",
    layout="wide"
)

st.markdown("# 📋 Warren Queue — Physical Tasks")
st.markdown("*Tasks that need your hands. Sorted by priority and optimal walking route.*")


# ===== FETCH PACKETS =====
@st.cache_data(ttl=5)
def fetch_packets():
    resp = requests.get(
        f"{API_BASE}/warren-packets",
        headers={"X-API-Key": API_KEY},
        timeout=5
    )
    return resp.json() if resp.ok else {"packets": []}


data = fetch_packets()
packets = data.get("packets", [])


# ===== EMPTY STATE =====
if not packets:
    st.balloons()
    st.success("🎉 No physical tasks pending. The AI is handling everything remotely.")
    st.caption("Enjoy your coffee. You've earned it.")
    st.stop()


# ===== SUMMARY METRICS =====
df_meta = {
    "total": len(packets),
    "critical": sum(1 for p in packets if p.get("priority") == "CRITICAL"),
    "high": sum(1 for p in packets if p.get("priority") == "HIGH"),
    "total_time": sum(p.get("prescription", {}).get("estimated_fix_time_minutes", 0) for p in packets)
}

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Tasks", df_meta["total"])
col2.metric("🔴 Critical", df_meta["critical"])
col3.metric("🟠 High", df_meta["high"])
col4.metric("Estimated Time", f"{df_meta['total_time']} min")


# ===== GPS-OPTIMIZED ROUTE =====
st.markdown("---")
st.markdown("### 🗺️ Optimized Walking Route")

st.info(
    f"💡 **Suggested order:** Follow the route below to fix all {df_meta['total']} "
    f"tasks in ~{df_meta['total_time']} minutes with a single trip."
)

# Build the route (sorted by priority, then estimated time)
priority_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
packets_sorted = sorted(
    packets,
    key=lambda p: (
        priority_rank.get(p.get("priority", "MEDIUM"), 2),
        p.get("prescription", {}).get("estimated_fix_time_minutes", 999)
    )
)

# Show the route as a numbered list
for idx, pkt in enumerate(packets_sorted, start=1):
    device = pkt.get("device", {})
    prescription = pkt.get("prescription", {})
    priority = pkt.get("priority", "MEDIUM")
    icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(priority, "⚪")
    
    st.markdown(
        f"**{idx}.** {icon} **{device.get('id', 'Unknown')}** — "
        f"*{device.get('location', 'Unknown location')}*  \n"
        f"&nbsp;&nbsp;&nbsp;&nbsp;Action: {prescription.get('action', 'N/A')}  \n"
        f"&nbsp;&nbsp;&nbsp;&nbsp;ETA: {prescription.get('estimated_fix_time_minutes', '?')} min  \n"
        f"&nbsp;&nbsp;&nbsp;&nbsp;Bring: {', '.join(prescription.get('tools_required', [])) or 'N/A'}"
    )


# ===== MAP VIEW (Optional) =====
st.markdown("### 📍 Visual Route")
st.caption("Map showing device locations (requires GPS coordinates in device inventory).")

try:
    # Build a simple folium map
    # Default to a generic hospital location
    m = folium.Map(location=[-1.2921, 36.8219], zoom_start=17)  # Nairobi default
    
    for idx, pkt in enumerate(packets_sorted, start=1):
        device = pkt.get("device", {})
        lat = device.get("latitude")
        lon = device.get("longitude")
        if lat is None or lon is None:
            continue
        
        priority = pkt.get("priority", "MEDIUM")
        color = {"CRITICAL": "red", "HIGH": "orange", "MEDIUM": "yellow", "LOW": "green"}.get(priority, "gray")
        
        folium.Marker(
            location=[lat, lon],
            popup=f"#{idx} {device.get('id')} — {pkt.get('summary', '')}",
            icon=folium.Icon(color=color, icon="wrench", prefix="fa")
        ).add_to(m)
    
    st_folium(m, width="100%", height=400)
except Exception as e:
    st.warning(f"Map unavailable: {e}")


# ===== DETAILED CARDS =====
st.markdown("---")
st.markdown("### 📦 Task Details")

for idx, pkt in enumerate(packets_sorted, start=1):
    device = pkt.get("device", {})
    root_cause = pkt.get("root_cause", {})
    prescription = pkt.get("prescription", {})
    attempts = pkt.get("attempts", [])
    workaround = pkt.get("workaround", {})
    priority = pkt.get("priority", "MEDIUM")
    icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(priority, "⚪")
    
    with st.expander(
        f"{icon} #{idx} — {device.get('id', 'Unknown')} ({priority})",
        expanded=(idx == 1)  # Expand only the first card by default
    ):
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.markdown(f"#### 📍 Location")
            st.markdown(
                f"**{device.get('location', 'Unknown')}** — {device.get('department', 'Unknown')}  \n"
                f"IP: `{device.get('ip_address', 'N/A')}`  \n"
                f"Type: {device.get('type', 'N/A')}"
            )
            
            st.markdown(f"#### 🔍 Root Cause Hypothesis")
            st.markdown(
                f"**{root_cause.get('hypothesis', 'Unknown')}**  \n"
                f"AI Confidence: **{root_cause.get('confidence', 0.0):.0%}**"
            )
            
            if root_cause.get("evidence"):
                st.markdown("**Evidence:**")
                for ev in root_cause["evidence"]:
                    st.markdown(f"- {ev}")
            
            st.markdown(f"#### 🔧 Prescription")
            st.markdown(f"**Action:** {prescription.get('action', 'N/A')}")
            st.markdown(f"**Part Number:** `{prescription.get('part_number', 'N/A')}`")
            st.markdown(f"**Spare Location:** {prescription.get('spare_location', 'N/A')}")
            st.markdown(f"**Tools:** {', '.join(prescription.get('tools_required', [])) or 'None'}")
            
            st.markdown(f"#### 📝 What the AI Already Tried")
            for att in attempts:
                result_icon = "✅" if att.get("result") == "success" else "❌"
                st.markdown(
                    f"{result_icon} **Attempt {att.get('attempt')}**: `{att.get('script')}` — "
                    f"{att.get('result')} ({att.get('duration_seconds', 0)}s)"
                )
                if att.get("error"):
                    st.caption(f"Error: {att['error']}")
        
        with col_right:
            st.markdown(f"#### ⏱️ Estimated Fix")
            st.metric("Time", f"{prescription.get('estimated_fix_time_minutes', '?')} min")
            
            st.markdown(f"#### 🛡️ Workaround")
            if workaround.get("active"):
                st.success(f"Active: {workaround.get('description', 'N/A')}")
                if workaround.get("expires_at"):
                    st.caption(f"Expires: {workaround['expires_at']}")
            else:
                st.warning("No workaround active. Users may be impacted.")
            
            st.markdown(f"#### 🎫 Packet Info")
            st.caption(f"ID: `{pkt.get('packet_id', 'N/A')}`")
            st.caption(f"Generated: {pkt.get('generated_at', 'N/A')}")
            
            # Mark as resolved button
            if st.button(f"✅ Mark #{idx} as Resolved", key=f"resolve_{pkt.get('packet_id')}"):
                resp = requests.post(
                    f"{API_BASE}/warren-packets/{pkt.get('packet_id')}/resolve",
                    headers={"X-API-Key": API_KEY},
                    json={"resolved_by": "warren", "resolved_at": datetime.now().isoformat()}
                )
                if resp.ok:
                    st.success("Marked as resolved. AI is learning from this.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(f"Failed to mark as resolved: {resp.text}")
