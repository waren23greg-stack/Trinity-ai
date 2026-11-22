"""
Nightingale-AI Department Heatmap
Real-time visual map of department stress levels.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

API_BASE = "http://localhost:8000/api"
API_KEY = st.secrets["api"]["warren_dashboard_key"]

st.set_page_config(
    page_title="Nightingale — Heatmap",
    page_icon="🔥",
    layout="wide"
)

st_autorefresh(interval=10000, key="heatmap_refresh")  # 10s refresh

st.markdown("# 🔥 Department Stress Heatmap")
st.markdown("*Live view of queue pressure, device health, and AI interventions across all departments.*")


# ===== FETCH DATA =====
@st.cache_data(ttl=10)
def fetch_department_stress():
    resp = requests.get(
        f"{API_BASE}/departments/stress",
        headers={"X-API-Key": API_KEY},
        timeout=5
    )
    return resp.json() if resp.ok else {"departments": []}


departments = fetch_department_stress().get("departments", [])


# ===== SUMMARY METRICS =====
if departments:
    df = pd.DataFrame(departments)
    
    total = len(df)
    critical = len(df[df["stress_level"] == "CRITICAL"])
    warning = len(df[df["stress_level"] == "WARNING"])
    healthy = len(df[df["stress_level"] == "HEALTHY"])
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Departments", total)
    col2.metric("🔴 Critical", critical, delta="action needed" if critical > 0 else "all clear")
    col3.metric("🟡 Warning", warning)
    col4.metric("🟢 Healthy", healthy)
    
    st.markdown("---")
    
    # ===== HEATMAP (TREEMAP) =====
    st.markdown("### Department Heatmap")
    st.caption("Size = patient queue length | Color = stress level")
    
    color_map = {
        "HEALTHY": "#2ecc71",
        "WARNING": "#f39c12",
        "CRITICAL": "#e74c3c"
    }
    
    fig = px.treemap(
        df,
        path=["department"],
        values="queue_length",
        color="stress_level",
        color_discrete_map=color_map,
        hover_data={
            "queue_length": True,
            "devices_offline": True,
            "ai_status": True,
            "avg_wait_minutes": True
        },
        title=""
    )
    fig.update_traces(
        textinfo="label+value+percent root",
        textfont_size=14
    )
    fig.update_layout(height=500, margin=dict(t=0, l=0, r=0, b=0))
    st.plotly_chart(fig, use_container_width=True)
    
    # ===== DETAILED TABLE =====
    st.markdown("### 📋 Detailed Department Status")
    
    # Sort by stress level then queue length
    severity_order = {"CRITICAL": 0, "WARNING": 1, "HEALTHY": 2}
    df["severity_rank"] = df["stress_level"].map(severity_order)
    df_sorted = df.sort_values(["severity_rank", "queue_length"], ascending=[True, False])
    
    st.dataframe(
        df_sorted[[
            "department", "stress_level", "queue_length",
            "avg_wait_minutes", "devices_offline", "ai_status"
        ]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "department": "Department",
            "stress_level": st.column_config.SelectboxColumn(
                "Stress Level",
                options=["CRITICAL", "WARNING", "HEALTHY"]
            ),
            "queue_length": st.column_config.NumberColumn("Queue Length", format="%d 👥"),
            "avg_wait_minutes": st.column_config.NumberColumn("Avg Wait", format="%d min"),
            "devices_offline": st.column_config.NumberColumn("Devices Offline", format="%d ⚠️"),
            "ai_status": "AI Status"
        }
    )
    
    # ===== FILTER & DRILL DOWN =====
    st.markdown("### 🔍 Drill Down")
    
    selected_dept = st.selectbox(
        "Select a department for full details:",
        options=df["department"].tolist()
    )
    
    if selected_dept:
        dept_data = df[df["department"] == selected_dept].iloc[0]
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown(f"**Department:** {dept_data['department']}")
            st.markdown(f"**Stress Level:** {dept_data['stress_level']}")
            st.markdown(f"**Queue Length:** {dept_data['queue_length']} patients")
            st.markdown(f"**Avg Wait:** {dept_data['avg_wait_minutes']} min")
        
        with col_b:
            st.markdown(f"**Devices Offline:** {dept_data['devices_offline']}")
            st.markdown(f"**AI Status:** {dept_data['ai_status']}")
            st.markdown(f"**Last Updated:** {dept_data.get('last_updated', 'N/A')}")
        
        # Show active tickets for this department
        st.markdown("**Active Tickets:**")
        dept_tickets = requests.get(
            f"{API_BASE}/tickets",
            params={"department": selected_dept},
            headers={"X-API-Key": API_KEY}
        ).json().get("tickets", [])
        
        if dept_tickets:
            for t in dept_tickets:
                st.warning(f"🎫 {t.get('ticket_id')} — {t.get('description', '')[:80]}")
        else:
            st.success("No open tickets for this department.")

else:
    st.info("No department data available. Check that the API gateway is running.")
