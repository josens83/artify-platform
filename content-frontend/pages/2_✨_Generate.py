import streamlit as st
import time
import random
import json

st.set_page_config(page_title="콘텐츠 생성", page_icon="✨")
st.title("✨ AI 콘텐츠 생성")

# API URL
API_URL = "https://artify-content-api.onrender.com"

# 캠페인/세그먼트 선택
col1, col2, col3 = st.columns(3)
with col1:
    campaign = st.selectbox(
        "캠페인 선택",
        ["여름 세일 2024", "신제품 출시", "브랜드 인지도 캠페인"]
    )
with col2:
    # 세션에 저장된 세그먼트 가져오기
    segments = st.session_state.get('segments', ["20대 피트니스", "30대 테크", "40대 여행"])
    segment = st.selectbox("세그먼트", segments)
with col3:
    channel = st.selectbox("채널", ["Instagram", "Facebook", "Twitter", "LinkedIn"])

st.divider()

# 생성 옵션
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
        ["짧게 (1-2문장)", "보통 (3-4문장)", "길게 (5문장 이상)"]
    )
    keywords = st.text_input(
        "키워드 (쉼표로 구분)",
        placeholder="무료배송, 한정수량, 여름세일"
    )

with col2:
    st.subheader("🎨 이미지 생성 옵션")
    style = st.selectbox(
        "이미지 스타일",
        ["미니멀", "모던", "빈티지", "일러스트", "사진"]
    )
    colors = st.multiselect(
        "주요 색상",
        ["🔵 파랑", "🔴 빨강", "🟢 초록", "🟡 노랑", "⚫ 검정", "⚪ 흰색"],
        default=["🔵 파랑", "⚪ 흰색"]
    )
    size = st.selectbox(
        "크기",
        ["1:1 (정사각형)", "16:9 (가로형)", "9:16 (세로형)"]
    )

st.divider()

# 생성 버튼
if st.button("🚀 AI 콘텐츠 생성하기", type="primary", use_container_width=True):
    with st.spinner("AI가 콘텐츠를 생성 중입니다..."):
        # 프로그레스 바
        progress = st.progress(0)
        for i in range(100):
            time.sleep(0.02)
            progress.progress(i + 1)

    st.success("✅ 콘텐츠 생성 완료!")

    # 생성 결과 표시
    st.divider()
    st.subheader("생성된 콘텐츠")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📝 카피")

        # 시뮬레이션 카피 생성
        if "여름" in campaign:
            headline = "☀️ 이번 여름, 당신만을 위한 특별한 기회!"
            body = "뜨거운 여름을 시원하게 보낼 수 있는 절호의 찬스! 최대 50% 할인된 가격으로 만나보세요. 무료배송은 기본, 한정수량이니 서두르세요!"
        elif "신제품" in campaign:
            headline = "🚀 혁신의 시작, 새로운 경험을 만나보세요"
            body = "오랜 연구 끝에 탄생한 신제품을 소개합니다. 당신의 일상을 바꿀 특별한 제품, 지금 바로 경험해보세요."
        else:
            headline = "✨ 믿을 수 있는 브랜드, 확실한 선택"
            body = "고객님의 신뢰에 보답하는 품질과 서비스. 우리와 함께라면 언제나 최고의 선택입니다."

        cta = "지금 바로 확인하기 →"
        hashtags = f"#{campaign.replace(' ', '')} #{segment.replace(' ', '')} #{channel}"

        # 결과 표시
        content_display = f"""
        **헤드라인**: {headline}

        **본문**: {body}

        **CTA**: {cta}

        **해시태그**: {hashtags}
        """

        st.info(content_display)

        # 복사 버튼
        if st.button("📋 텍스트 복사"):
            st.toast("클립보드에 복사되었습니다!")

    with col2:
        st.markdown("### 🎨 이미지")

        # 플레이스홀더 이미지
        image_url = f"https://via.placeholder.com/500x500/667eea/ffffff?text={style}+Style"
        st.image(image_url, use_column_width=True)

        # 다운로드 버튼
        if st.button("💾 이미지 다운로드"):
            st.toast("다운로드를 시작합니다!")

    # 생성된 콘텐츠 세션에 저장
    if 'generated_content' not in st.session_state:
        st.session_state.generated_content = []

    st.session_state.generated_content.append({
        "campaign": campaign,
        "segment": segment,
        "channel": channel,
        "headline": headline,
        "body": body,
        "timestamp": time.time()
    })

    # 피드백 섹션
    st.divider()
    st.subheader("피드백")

    feedback_text = st.text_area(
        "개선사항이나 피드백을 입력하세요",
        placeholder="예: 톤을 더 친근하게, 이미지에 사람 추가"
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("👍 좋아요"):
            st.toast("긍정적인 피드백이 저장되었습니다!")
    with col2:
        if st.button("👎 별로예요"):
            st.toast("피드백이 저장되었습니다. 개선하겠습니다!")
    with col3:
        if st.button("🔄 다시 생성"):
            st.rerun()
    with col4:
        if st.button("💾 프로젝트에 저장"):
            st.success("프로젝트에 저장되었습니다!")

# 사이드바 - 최근 생성 내역
with st.sidebar:
    st.subheader("📜 최근 생성 내역")
    if 'generated_content' in st.session_state and st.session_state.generated_content:
        for i, content in enumerate(reversed(st.session_state.generated_content[-5:])):
            with st.expander(f"{content['campaign'][:15]}... ({i+1})"):
                st.write(f"**세그먼트**: {content['segment']}")
                st.write(f"**채널**: {content['channel']}")
                st.write(f"**헤드라인**: {content['headline'][:30]}...")
    else:
        st.info("아직 생성된 콘텐츠가 없습니다")
