import streamlit as st
import requests
from config import API_URL

st.set_page_config(page_title="Analytics", page_icon="=Ê", layout="wide")

st.title("=Ê Performance Analytics")
st.markdown("Track and analyze your content performance")

# T¸­ ”}
st.markdown("---")
st.subheader("Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Impressions",
        value="125.4K",
        delta="12.5%"
    )

with col2:
    st.metric(
        label="Engagement Rate",
        value="8.2%",
        delta="2.1%"
    )

with col3:
    st.metric(
        label="Click-through Rate",
        value="3.5%",
        delta="-0.5%",
        delta_color="inverse"
    )

with col4:
    st.metric(
        label="Conversions",
        value="1,234",
        delta="15.3%"
    )

#  ˜x 1ü
st.markdown("---")
st.subheader("Campaign Performance")

campaigns = [
    {"name": "Summer Sale", "impressions": "45.2K", "engagement": "9.1%", "ctr": "4.2%"},
    {"name": "New Product Launch", "impressions": "38.7K", "engagement": "7.8%", "ctr": "3.1%"},
    {"name": "Brand Awareness", "impressions": "41.5K", "engagement": "8.5%", "ctr": "3.8%"},
]

for campaign in campaigns:
    with st.expander(f"=È {campaign['name']}"):
        col1, col2, col3 = st.columns(3)
        col1.metric("Impressions", campaign['impressions'])
        col2.metric("Engagement", campaign['engagement'])
        col3.metric("CTR", campaign['ctr'])

# 0  Ý
st.markdown("---")
st.subheader("Detailed Analysis")

col1, col2 = st.columns([1, 3])

with col1:
    date_range = st.date_input("Select Date Range", [])
    metric_type = st.selectbox("Metric Type", ["Impressions", "Engagement", "CTR", "Conversions"])

with col2:
    st.info("=Ê Chart visualization will be displayed here")
    st.markdown("""
    - Time series analysis
    - Performance trends
    - Comparative analysis
    """)
