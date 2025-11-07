import streamlit as st
import requests
from config import settings

st.set_page_config(page_title="Generate Content", page_icon="✨", layout="wide")

st.title("✨ AI Content Generation")
st.markdown("AI를 활용하여 맞춤형 콘텐츠를 생성합니다.")
st.markdown("---")

# 2단 레이아웃
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 콘텐츠 설정")

    # 세그먼트 선택
    segment = st.selectbox(
        "타겟 세그먼트",
        ["Tech Enthusiasts", "Fashion Lovers", "Food Bloggers"]
    )

    # 콘텐츠 타입
    content_type = st.radio(
        "콘텐츠 타입",
        ["Social Post", "Blog Article", "Email", "Ad Copy"]
    )

    # 톤앤매너
    tone = st.select_slider(
        "톤앤매너",
        options=["Professional", "Friendly", "Casual", "Humorous", "Inspirational"]
    )

    # 길이
    length = st.slider("콘텐츠 길이 (단어)", 50, 500, 150)

    # 프롬프트
    prompt = st.text_area(
        "프롬프트",
        placeholder="생성하고 싶은 콘텐츠에 대해 설명해주세요...",
        height=150
    )

    # 고급 옵션
    with st.expander("🔧 고급 옵션"):
        temperature = st.slider("창의성 (Temperature)", 0.0, 1.0, 0.7)
        keywords = st.text_input("키워드 (쉼표로 구분)", "")
        include_hashtags = st.checkbox("해시태그 포함", value=True)
        include_cta = st.checkbox("CTA 포함", value=True)

    # 생성 버튼
    if st.button("🚀 콘텐츠 생성", type="primary", use_container_width=True):
        with st.spinner("AI가 콘텐츠를 생성하고 있습니다..."):
            # TODO: 실제 API 호출
            st.session_state['generated_content'] = f"""
🎯 Targeting: {segment}

Discover the latest innovations in AI technology! 🚀

Our new platform revolutionizes the way you create content.
With advanced AI algorithms, you can now generate professional
{content_type.lower()} in seconds, not hours.

Join thousands of satisfied users today!

👉 Click here to get started!

#AI #Innovation #ContentCreation #TechRevolution
            """.strip()
            st.success("✅ 콘텐츠 생성 완료!")

with col2:
    st.subheader("✨ 생성된 콘텐츠")

    if 'generated_content' in st.session_state:
        # 생성된 콘텐츠 표시
        st.markdown("### 미리보기")
        with st.container():
            st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px;">
                {st.session_state['generated_content'].replace(chr(10), '<br>')}
                </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # 액션 버튼들
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("📋 복사", use_container_width=True):
                st.success("클립보드에 복사되었습니다!")
        with col_b:
            if st.button("💾 저장", use_container_width=True):
                st.success("콘텐츠가 저장되었습니다!")
        with col_c:
            if st.button("🔄 재생성", use_container_width=True):
                st.rerun()

        # 피드백
        st.markdown("---")
        st.markdown("### 피드백")
        rating = st.slider("콘텐츠 품질 평가", 1, 5, 4)
        feedback = st.text_area("개선 사항", placeholder="선택사항")
        if st.button("피드백 제출", use_container_width=True):
            st.success("피드백이 제출되었습니다!")
    else:
        st.info("👈 왼쪽에서 콘텐츠 설정 후 '콘텐츠 생성' 버튼을 클릭하세요.")

# 사이드바
with st.sidebar:
    st.subheader("📚 생성 이력")
    st.caption("최근 생성된 콘텐츠")

    history = [
        {"title": "Tech Blog Post", "date": "2024-01-15"},
        {"title": "Fashion Ad Copy", "date": "2024-01-14"},
        {"title": "Food Review", "date": "2024-01-13"},
    ]

    for item in history:
        with st.container():
            st.write(f"📄 {item['title']}")
            st.caption(item['date'])
            st.divider()
