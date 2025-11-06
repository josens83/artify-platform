import streamlit as st
import json
import requests

st.set_page_config(page_title="세그먼트 관리", page_icon="🎯", layout="wide")

st.title("🎯 세그먼트 관리")
st.markdown("타겟 고객을 정의하고 관리합니다")

# 탭 생성
tab1, tab2, tab3 = st.tabs(["➕ 새 세그먼트", "📋 세그먼트 목록", "📊 통계"])

with tab1:
    st.subheader("새 세그먼트 생성")

    col1, col2 = st.columns(2)

    with col1:
        segment_name = st.text_input("세그먼트 이름", placeholder="예: 20대 여성 피트니스 관심자")

        age_range = st.slider("연령대", 10, 80, (20, 35))

        gender = st.selectbox("성별", ["전체", "남성", "여성", "기타"])

    with col2:
        interests = st.multiselect(
            "관심사",
            ["피트니스", "패션", "뷰티", "테크", "여행", "음식", "게임", "음악", "영화", "독서"],
            default=["피트니스"]
        )

        location = st.text_input("지역", placeholder="예: 서울, 부산")

        income = st.select_slider(
            "소득 수준",
            options=["하", "중하", "중", "중상", "상"],
            value="중"
        )

    # JSON 프리뷰
    st.subheader("필터 프리뷰")
    filters = {
        "age_range": age_range,
        "gender": gender,
        "interests": interests,
        "location": location,
        "income": income
    }
    st.json(filters)

    if st.button("세그먼트 생성", type="primary", use_container_width=True):
        # API 호출 (실제로는 백엔드 연동)
        st.success(f"✅ '{segment_name}' 세그먼트가 생성되었습니다!")
        st.balloons()

with tab2:
    st.subheader("저장된 세그먼트")

    # 샘플 데이터
    segments = [
        {"이름": "20대 피트니스", "타겟": "20-29세", "관심사": "피트니스, 건강", "생성일": "2024-11-06"},
        {"이름": "30대 테크", "타겟": "30-39세", "관심사": "기술, 가젯", "생성일": "2024-11-05"},
        {"이름": "40대 여행", "타겟": "40-49세", "관심사": "여행, 문화", "생성일": "2024-11-04"},
    ]

    for seg in segments:
        with st.expander(f"📁 {seg['이름']}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**타겟**: {seg['타겟']}")
            with col2:
                st.write(f"**관심사**: {seg['관심사']}")
            with col3:
                st.write(f"**생성일**: {seg['생성일']}")

            if st.button(f"삭제", key=f"del_{seg['이름']}"):
                st.warning(f"'{seg['이름']}' 삭제됨")

with tab3:
    st.subheader("세그먼트 통계")

    # 차트 데이터
    import plotly.express as px
    import pandas as pd

    df = pd.DataFrame({
        "세그먼트": ["20대", "30대", "40대", "50대+"],
        "콘텐츠 수": [45, 38, 22, 15],
        "평균 CTR": [3.2, 2.8, 2.5, 2.1]
    })

    col1, col2 = st.columns(2)

    with col1:
        fig1 = px.bar(df, x="세그먼트", y="콘텐츠 수", title="세그먼트별 콘텐츠 생성량")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = px.line(df, x="세그먼트", y="평균 CTR", title="세그먼트별 평균 CTR", markers=True)
        st.plotly_chart(fig2, use_container_width=True)
