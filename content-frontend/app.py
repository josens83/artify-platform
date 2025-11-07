import streamlit as st
import requests

# 페이지 설정
st.set_page_config(
    page_title="Content Management",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'segments' not in st.session_state:
    st.session_state.segments = []
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = []

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
    if st.button("🎯 세그먼트 관리", use_container_width=True, key="segments_btn"):
        st.switch_page("pages/1_🎯_Segments.py")

with col2:
    if st.button("✨ 콘텐츠 생성", use_container_width=True, key="generate_btn"):
        st.switch_page("pages/2_✨_Generate.py")

with col3:
    if st.button("📊 대시보드", use_container_width=True, key="dashboard_btn"):
        st.switch_page("pages/3_📊_Dashboard.py")

st.markdown("---")

# 시스템 정보
with st.expander("ℹ️ System Information"):
    st.write("**Backend API:** http://localhost:8001/api")
    st.write("**Vector DB:** http://localhost:6333")
    st.write("**Version:** 1.0.0")

# API 연결 상태 체크
with st.expander("🔧 API 연결 상태"):
    api_url = "https://artify-content-api.onrender.com"
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Backend API 체크"):
            try:
                response = requests.get(f"{api_url}/health", timeout=5)
                if response.status_code == 200:
                    st.success(f"✅ 연결 성공: {response.json()}")
                else:
                    st.error(f"❌ API 오류: {response.status_code}")
            except Exception as e:
                st.error(f"❌ 연결 실패: {e}")

    with col2:
        st.code(api_url)

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
