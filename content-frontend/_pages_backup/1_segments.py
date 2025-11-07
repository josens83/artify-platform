import streamlit as st
import requests
from config import settings

st.set_page_config(page_title="Segments", page_icon="🎯", layout="wide")

st.title("🎯 Segment Management")
st.markdown("타겟 세그먼트를 관리하고 분석합니다.")
st.markdown("---")

# 탭 생성
tab1, tab2, tab3 = st.tabs(["📋 Segment List", "➕ Create New", "📊 Analytics"])

with tab1:
    st.subheader("기존 세그먼트 목록")

    # 샘플 데이터
    segments = [
        {"id": 1, "name": "Tech Enthusiasts", "size": 1250, "status": "Active"},
        {"id": 2, "name": "Fashion Lovers", "size": 890, "status": "Active"},
        {"id": 3, "name": "Food Bloggers", "size": 560, "status": "Paused"},
    ]

    for segment in segments:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            with col1:
                st.write(f"**{segment['name']}**")
            with col2:
                st.write(f"👥 {segment['size']} members")
            with col3:
                status_color = "🟢" if segment['status'] == "Active" else "🟡"
                st.write(f"{status_color} {segment['status']}")
            with col4:
                if st.button("Edit", key=f"edit_{segment['id']}"):
                    st.info(f"Editing {segment['name']}...")
            st.divider()

with tab2:
    st.subheader("새 세그먼트 생성")

    with st.form("new_segment_form"):
        segment_name = st.text_input("세그먼트 이름", placeholder="예: Tech Enthusiasts")
        segment_desc = st.text_area("설명", placeholder="세그먼트에 대한 설명을 입력하세요...")

        col1, col2 = st.columns(2)
        with col1:
            age_range = st.slider("연령대", 18, 65, (25, 45))
        with col2:
            interests = st.multiselect(
                "관심사",
                ["Technology", "Fashion", "Food", "Travel", "Sports", "Art"]
            )

        submitted = st.form_submit_button("생성하기", use_container_width=True)
        if submitted:
            st.success(f"✅ 세그먼트 '{segment_name}' 생성 완료!")

with tab3:
    st.subheader("세그먼트 분석")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 세그먼트", "3", "+1")
    with col2:
        st.metric("총 회원 수", "2,700", "+150")
    with col3:
        st.metric("활성 세그먼트", "2", "0")

    st.info("📊 상세 분석 차트는 곧 추가될 예정입니다.")

# 사이드바
with st.sidebar:
    st.subheader("필터")
    status_filter = st.selectbox("상태", ["All", "Active", "Paused"])
    size_filter = st.slider("최소 회원 수", 0, 2000, 0)

    if st.button("필터 적용"):
        st.rerun()
