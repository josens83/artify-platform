import streamlit as st
import time
import random

st.set_page_config(page_title="콘텐츠 생성", page_icon="✨")
st.title("✨ AI 콘텐츠 생성")

# 설정
col1, col2, col3 = st.columns(3)
with col1:
    campaign = st.selectbox("캠페인", ["여름 세일", "신제품 출시", "브랜드 캠페인"])
with col2:
    segment = st.selectbox("세그먼트", ["20대 피트니스", "30대 테크", "전체"])
with col3:
    channel = st.selectbox("채널", ["Instagram", "Facebook", "Twitter"])

st.divider()

# 생성 옵션
col1, col2 = st.columns(2)
with col1:
    st.subheader("📝 텍스트 옵션")
    tone = st.select_slider("톤", ["공식적", "친근한", "캐주얼"])
    keywords = st.text_input("키워드", "무료배송, 한정특가")

with col2:
    st.subheader("🎨 이미지 옵션")
    style = st.selectbox("스타일", ["미니멀", "모던", "빈티지"])
    colors = st.multiselect("색상", ["파랑", "빨강", "초록"], ["파랑"])

# 생성 버튼
if st.button("🚀 콘텐츠 생성", type="primary", use_container_width=True):
    with st.spinner("AI가 생성 중... (시뮬레이션)"):
        progress = st.progress(0)
        for i in range(100):
            time.sleep(0.01)
            progress.progress(i + 1)

    # 생성 결과 (시뮬레이션)
    st.success("✅ 생성 완료!")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📝 생성된 카피")

        # 랜덤 카피 생성
        headlines = [
            "🏃‍♀️ 여름을 위한 완벽한 준비!",
            "💪 당신의 피트니스 여정을 시작하세요",
            "✨ 특별한 여름 세일"
        ]

        bodies = [
            "지금 구매하고 무료배송 혜택을 받으세요!",
            "한정 수량! 놓치지 마세요.",
            "최대 50% 할인된 가격으로 만나보세요."
        ]

        st.info(f"""
        **헤드라인**: {random.choice(headlines)}

        **본문**: {random.choice(bodies)}

        **CTA**: 지금 구매하기 →

        **해시태그**: #{campaign.replace(' ', '')} #{segment.replace(' ', '')}
        """)

    with col2:
        st.subheader("🎨 생성된 이미지")
        st.image("https://via.placeholder.com/400x400/667eea/ffffff?text=AI+Generated", use_column_width=True)

    # 피드백
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("👍 좋아요"):
            st.toast("피드백 감사합니다!")
    with col2:
        if st.button("🔄 다시 생성"):
            st.rerun()
    with col3:
        if st.button("💾 저장"):
            st.success("저장되었습니다!")
