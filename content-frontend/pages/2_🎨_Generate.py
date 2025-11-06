import streamlit as st
import time

st.set_page_config(page_title="콘텐츠 생성", page_icon="🎨", layout="wide")

st.title("🎨 AI 콘텐츠 생성")
st.markdown("캠페인과 세그먼트를 선택하고 AI로 콘텐츠를 생성합니다")

# 설정 섹션
with st.container():
    col1, col2, col3 = st.columns(3)

    with col1:
        campaign = st.selectbox(
            "캠페인 선택",
            ["여름 세일 2024", "신제품 출시", "브랜드 인지도", "새 캠페인 +"]
        )

    with col2:
        segment = st.selectbox(
            "세그먼트 선택",
            ["20대 피트니스", "30대 테크", "40대 여행", "전체"]
        )

    with col3:
        channel = st.selectbox(
            "채널",
            ["Instagram", "Facebook", "Twitter", "LinkedIn", "TikTok"]
        )

# 생성 옵션
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 텍스트 생성 옵션")

    tone = st.select_slider(
        "톤 & 매너",
        options=["공식적", "전문적", "친근한", "캐주얼", "유머러스"],
        value="친근한"
    )

    length = st.radio(
        "길이",
        ["짧게 (1-2문장)", "보통 (3-4문장)", "길게 (5문장 이상)"],
        horizontal=True
    )

    keywords = st.text_input(
        "키워드 (쉼표로 구분)",
        placeholder="무료배송, 한정수량, 여름세일"
    )

with col2:
    st.subheader("🎨 이미지 생성 옵션")

    style = st.selectbox(
        "이미지 스타일",
        ["미니멀", "모던", "빈티지", "일러스트", "사진", "3D"]
    )

    colors = st.multiselect(
        "색상 팔레트",
        ["🔴 빨강", "🔵 파랑", "🟢 초록", "🟡 노랑", "🟣 보라", "⚫ 검정", "⚪ 흰색"],
        default=["🔵 파랑", "⚪ 흰색"]
    )

    size = st.selectbox(
        "크기",
        ["1:1 (정사각형)", "16:9 (가로형)", "9:16 (세로형)", "4:5 (인스타)"]
    )

# 생성 버튼
st.markdown("---")
col1, col2, col3 = st.columns([2, 3, 2])

with col2:
    if st.button("🚀 콘텐츠 생성하기", type="primary", use_container_width=True):
        with st.spinner("AI가 콘텐츠를 생성 중입니다..."):
            progress = st.progress(0)
            for i in range(100):
                time.sleep(0.02)
                progress.progress(i + 1)

        st.success("✅ 콘텐츠 생성 완료!")

        # 결과 표시
        st.markdown("---")
        st.subheader("생성된 콘텐츠")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📝 카피")
            st.info("""
            **헤드라인**: 🏃‍♀️ 여름을 위한 완벽한 준비!

            **본문**: 피트니스를 사랑하는 당신을 위한 특별한 여름 세일!
            지금 바로 시작하세요. 한정 수량, 무료 배송까지!

            **CTA**: 지금 구매하기 →

            **해시태그**: #여름세일 #피트니스 #무료배송 #한정특가
            """)

            if st.button("📋 복사", key="copy_text"):
                st.toast("텍스트가 복사되었습니다!")

        with col2:
            st.markdown("### 🎨 이미지")
            st.image("https://via.placeholder.com/500x500/667eea/ffffff?text=AI+Generated+Image", use_column_width=True)

            if st.button("💾 다운로드", key="download_image"):
                st.toast("이미지 다운로드 시작!")

        # 피드백 섹션
        st.markdown("---")
        st.subheader("피드백")

        feedback = st.text_area("개선사항이나 피드백을 입력하세요", placeholder="예: 톤을 더 친근하게, 이미지에 사람 추가")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("👍 좋아요"):
                st.toast("피드백 감사합니다!")
        with col2:
            if st.button("👎 별로예요"):
                st.toast("개선하겠습니다!")
        with col3:
            if st.button("🔄 다시 생성"):
                st.rerun()
        with col4:
            if st.button("💾 저장"):
                st.success("콘텐츠가 저장되었습니다!")
