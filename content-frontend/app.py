import streamlit as st
from config import settings

# 페이지 설정
st.set_page_config(
    page_title="Content Management",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# 메인 페이지
st.title("📝 Content Management System")
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("### 🎯 Segments")
    st.write("타겟 세그먼트를 관리하고 분석합니다.")
    if st.button("Go to Segments →"):
        st.switch_page("pages/1_segments.py")

with col2:
    st.success("### ✨ Generate")
    st.write("AI 기반 콘텐츠를 생성합니다.")
    if st.button("Go to Generate →"):
        st.switch_page("pages/2_generate.py")

with col3:
    st.warning("### 📊 Dashboard")
    st.write("콘텐츠 성과를 분석합니다.")
    if st.button("Go to Dashboard →"):
        st.switch_page("pages/3_dashboard.py")

st.markdown("---")

# 시스템 정보
with st.expander("ℹ️ System Information"):
    st.write(f"**Backend API:** {settings.BACKEND_URL}")
    st.write(f"**Vector DB:** {settings.VECTOR_DB_URL}")
    st.write(f"**Version:** {settings.VERSION}")

# 사이드바
with st.sidebar:
    st.image("https://via.placeholder.com/150x50/667eea/ffffff?text=Content+CMS", use_container_width=True)
    st.markdown("---")

    st.subheader("Quick Links")
    st.markdown("- [Segments](pages/1_segments.py)")
    st.markdown("- [Generate](pages/2_generate.py)")
    st.markdown("- [Dashboard](pages/3_dashboard.py)")

    st.markdown("---")
    st.caption(f"Version {settings.VERSION}")
