import streamlit as st
from config import API_URL

st.set_page_config(
    page_title="Artify Content Platform",
    page_icon="🎨",
    layout="wide"
)

st.title("🎨 Artify Content Platform")
st.markdown("### AI-powered Content Generation & Management")

# API 상태 확인
st.sidebar.title("🔧 System Status")

import requests
try:
    response = requests.get(f"{API_URL}/health", timeout=5)
    if response.status_code == 200:
        st.sidebar.success("✅ API Connected")
        health_data = response.json()
        st.sidebar.json(health_data)
    else:
        st.sidebar.error("❌ API Error")
except Exception as e:
    st.sidebar.error(f"❌ API Unreachable: {str(e)}")

# 메인 대시보드
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Total Campaigns", value="0", delta="New")

with col2:
    st.metric(label="Generated Content", value="0", delta="0%")

with col3:
    st.metric(label="Total Segments", value="0", delta="0")

st.markdown("---")

st.info("👈 Use the sidebar to navigate to different sections")

st.markdown("""
### 📱 Features

- **🎯 Segments**: Create and manage audience segments
- **🎨 Generate**: AI-powered content generation
- **📊 Analytics**: Track performance metrics

### 🚀 Getting Started

1. Create audience segments
2. Generate content for your campaigns
3. Analyze performance metrics
""")
