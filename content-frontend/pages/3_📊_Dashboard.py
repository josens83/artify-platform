import streamlit as st
import random
from datetime import datetime, timedelta

st.set_page_config(page_title="성과 대시보드", page_icon="📊", layout="wide")
st.title("📊 성과 분석 대시보드")

# 날짜 필터
col1, col2, col3, col4 = st.columns(4)
with col1:
    start_date = st.date_input("시작일", datetime.now() - timedelta(days=30))
with col2:
    end_date = st.date_input("종료일", datetime.now())
with col3:
    campaign_filter = st.selectbox("캠페인", ["전체", "여름 세일 2024", "신제품 출시", "브랜드 인지도"])
with col4:
    segment_filter = st.selectbox("세그먼트", ["전체", "20대", "30대", "40대"])

st.divider()

# KPI 메트릭 카드
st.subheader("📈 주요 성과 지표")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "총 노출수",
        "125.3K",
        "+12.5%",
        help="지난 기간 대비 증가율"
    )
with col2:
    st.metric(
        "클릭수",
        "4,235",
        "+8.3%"
    )
with col3:
    st.metric(
        "평균 CTR",
        "3.38%",
        "+0.23%"
    )
with col4:
    st.metric(
        "전환율",
        "2.1%",
        "-0.1%"
    )
with col5:
    st.metric(
        "참여율",
        "5.7%",
        "+1.2%"
    )

st.divider()

# 차트 섹션
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 일별 성과 추이")

    # 샘플 데이터 생성
    dates = []
    ctr_values = []
    engagement_values = []

    for i in range(30, 0, -1):
        date = (datetime.now() - timedelta(days=i))
        dates.append(date.strftime("%m/%d"))
        ctr_values.append(3.0 + random.uniform(-0.5, 1.0))
        engagement_values.append(5.0 + random.uniform(-1.0, 1.5))

    # 탭으로 구분
    tab1, tab2 = st.tabs(["CTR", "참여율"])

    with tab1:
        chart_data = {"날짜": dates[-14:], "CTR(%)": ctr_values[-14:]}
        st.line_chart(data=chart_data, x="날짜", y="CTR(%)", height=300)

    with tab2:
        chart_data = {"날짜": dates[-14:], "참여율(%)": engagement_values[-14:]}
        st.line_chart(data=chart_data, x="날짜", y="참여율(%)", height=300)

with col2:
    st.subheader("🎯 세그먼트별 성과")

    # 세그먼트 데이터
    segments_data = {
        "세그먼트": ["20대", "30대", "40대", "50대+"],
        "CTR(%)": [3.8, 3.2, 2.9, 2.5],
        "전환율(%)": [2.5, 2.2, 1.9, 1.6]
    }

    st.bar_chart(
        data=segments_data,
        x="세그먼트",
        y=["CTR(%)", "전환율(%)"],
        height=350
    )

st.divider()

# 상위 성과 콘텐츠
st.subheader("🏆 상위 성과 콘텐츠 TOP 5")

# 생성된 콘텐츠 가져오기 (있다면)
if 'generated_content' in st.session_state and st.session_state.generated_content:
    top_content = []
    for i, content in enumerate(st.session_state.generated_content[-5:], 1):
        top_content.append({
            "순위": i,
            "캠페인": content['campaign'],
            "세그먼트": content['segment'],
            "헤드라인": content['headline'][:30] + "...",
            "CTR": f"{3.5 + random.random():.1f}%",
            "참여율": f"{5.5 + random.random():.1f}%"
        })
else:
    # 샘플 데이터
    top_content = [
        {"순위": 1, "캠페인": "여름 세일", "세그먼트": "20대 여성", "헤드라인": "☀️ 여름을 위한 완벽한 준비!", "CTR": "4.2%", "참여율": "7.1%"},
        {"순위": 2, "캠페인": "신제품 출시", "세그먼트": "30대 남성", "헤드라인": "🚀 혁신의 시작", "CTR": "3.9%", "참여율": "6.8%"},
        {"순위": 3, "캠페인": "여름 세일", "세그먼트": "20대 남성", "헤드라인": "💪 당신의 여름을 바꿔줄", "CTR": "3.7%", "참여율": "6.5%"},
        {"순위": 4, "캠페인": "브랜드 인지도", "세그먼트": "40대 여성", "헤드라인": "✨ 품격있는 선택", "CTR": "3.5%", "참여율": "6.2%"},
        {"순위": 5, "캠페인": "신제품 출시", "세그먼트": "30대 여성", "헤드라인": "🎯 스마트한 당신을 위한", "CTR": "3.3%", "참여율": "5.9%"}
    ]

# 테이블로 표시
st.dataframe(
    top_content,
    use_container_width=True,
    hide_index=True,
    column_config={
        "순위": st.column_config.NumberColumn("순위", width="small"),
        "캠페인": st.column_config.TextColumn("캠페인", width="medium"),
        "세그먼트": st.column_config.TextColumn("세그먼트", width="small"),
        "헤드라인": st.column_config.TextColumn("헤드라인", width="large"),
        "CTR": st.column_config.ProgressColumn("CTR", min_value=0, max_value=10, format="%.1f%%"),
        "참여율": st.column_config.ProgressColumn("참여율", min_value=0, max_value=10, format="%.1f%%")
    }
)

st.divider()

# AI 인사이트
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🤖 AI 인사이트 & 추천")

    insights = st.container(border=True)
    with insights:
        st.markdown("""
        ### 📊 주요 발견사항

        **1. 세그먼트 성과 분석**
        - 🥇 **20대 세그먼트**가 가장 높은 CTR (3.8%) 기록
        - 전환율도 20대가 가장 우수 (2.5%)
        - 40대 이상은 상대적으로 낮은 참여율

        **2. 시간대별 패턴**
        - 📅 오전 **10-11시** 게시 콘텐츠가 최고 성과
        - 주말보다 평일 성과가 15% 높음
        - 화요일과 목요일이 최적 게시일

        **3. 콘텐츠 특성**
        - 😊 **이모지 포함** 헤드라인이 평균 15% 높은 CTR
        - 짧은 카피(2문장 이내)가 더 효과적
        - 시각적 요소가 강한 콘텐츠가 참여율 우수

        ### 💡 추천 액션

        1. **즉시 실행**
           - 20대 타겟 캠페인에 예산 20% 증대
           - 모든 헤드라인에 관련 이모지 추가
           - 오전 10시 전후로 주요 콘텐츠 예약

        2. **테스트 제안**
           - A/B 테스트: 긴 카피 vs 짧은 카피
           - 30대 세그먼트 세분화 (직업군별)
           - 동영상 콘텐츠 추가 테스트

        3. **장기 전략**
           - 40대+ 세그먼트 재정의 필요
           - 주말 특화 콘텐츠 전략 수립
           - 시즌별 캠페인 로드맵 작성
        """)

with col2:
    st.subheader("📥 리포트 다운로드")

    export_container = st.container(border=True)
    with export_container:
        st.write("**리포트 옵션**")

        report_type = st.radio(
            "형식 선택",
            ["PDF 리포트", "Excel 데이터", "CSV 데이터"]
        )

        include_charts = st.checkbox("차트 포함", value=True)
        include_insights = st.checkbox("AI 인사이트 포함", value=True)

        if st.button("📥 다운로드", type="primary", use_container_width=True):
            st.toast(f"{report_type} 생성 중...")
            with st.spinner("리포트 생성 중..."):
                import time
                time.sleep(2)
            st.success("✅ 리포트가 준비되었습니다!")
            st.balloons()

# 푸터 정보
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
with col2:
    st.caption("데이터 소스: Artify Analytics")
with col3:
    st.caption("v1.0.0")
