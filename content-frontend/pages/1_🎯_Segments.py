import streamlit as st
import requests
from config import API_URL

st.set_page_config(page_title="Segments", page_icon="<¯", layout="wide")

st.title("<¯ Audience Segments")
st.markdown("Create and manage your target audience segments")

# 8ø<¸ Ý1
st.markdown("---")
st.subheader("Create New Segment")

with st.form("new_segment"):
    segment_name = st.text_input("Segment Name")
    segment_desc = st.text_area("Description")

    col1, col2 = st.columns(2)
    with col1:
        age_range = st.slider("Age Range", 18, 65, (25, 45))
    with col2:
        interests = st.multiselect(
            "Interests",
            ["Technology", "Fashion", "Sports", "Food", "Travel"]
        )

    submitted = st.form_submit_button("Create Segment")

    if submitted:
        if segment_name:
            st.success(f" Segment '{segment_name}' created successfully!")
        else:
            st.error("L Please enter a segment name")

# 0t 8ø<¸ ©]
st.markdown("---")
st.subheader("Existing Segments")

# Ø pt0
segments = [
    {"name": "Tech Enthusiasts", "count": 1250, "status": "Active"},
    {"name": "Fashion Forward", "count": 890, "status": "Active"},
    {"name": "Food Lovers", "count": 2100, "status": "Active"},
]

for segment in segments:
    with st.expander(f"=Ê {segment['name']}"):
        col1, col2, col3 = st.columns(3)
        col1.metric("Audience Size", segment['count'])
        col2.metric("Status", segment['status'])
        col3.button("Edit", key=f"edit_{segment['name']}")
