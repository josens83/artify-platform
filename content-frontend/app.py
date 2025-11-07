import streamlit as st

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
    st.write("기능 준비 중입니다.")

with col2:
    st.success("### ✨ Generate")
    st.write("AI 기반 콘텐츠를 생성합니다.")
    st.write("기능 준비 중입니다.")

with col3:
    st.warning("### 📊 Dashboard")
    st.write("콘텐츠 성과를 분석합니다.")
    st.write("기능 준비 중입니다.")

st.markdown("---")

# 시스템 정보
with st.expander("ℹ️ System Information"):
    st.write("**Backend API:** http://localhost:8001/api")
    st.write("**Vector DB:** http://localhost:6333")
    st.write("**Version:** 1.0.0")

# 샘플 데이터 표시
st.subheader("📊 샘플 데이터")
sample_data = {
    "항목": ["콘텐츠 A", "콘텐츠 B", "콘텐츠 C"],
    "조회수": [1200, 850, 2100],
    "참여율": ["12%", "8%", "15%"]
}
st.table(sample_data)

# 간단한 차트
st.subheader("📈 트렌드")
chart_data = {
    "날짜": [1, 2, 3, 4, 5],
    "방문자": [100, 120, 115, 140, 135]
}
st.line_chart(chart_data["방문자"])

# 사이드바
with st.sidebar:
    st.image("https://via.placeholder.com/150x50/667eea/ffffff?text=Content+CMS", use_container_width=True)
    st.markdown("---")

    st.subheader("Quick Info")
    st.write("✅ 시스템 정상 작동 중")
    st.write("🔧 Python 3.11")
    st.write("🚀 Streamlit Cloud")

    st.markdown("---")
    st.caption("Version 1.0.0")
