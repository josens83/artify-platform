import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="성과 분석", page_icon="📊", layout="wide")

st.title("📊 성과 분석 대시보드")
st.markdown("캠페인과 콘텐츠의 성과를 실시간으로 분석합니다")

# 날짜 필터
col1, col2, col3, col4 = st.columns(4)
with col1:
    start_date = st.date_input("시작일", datetime.now() - timedelta(days=30))
with col2:
    end_date = st.date_input("종료일", datetime.now())
with col3:
    campaign_filter = st.selectbox("캠페인", ["전체", "여름 세일", "신제품 출시"])
with col4:
    segment_filter = st.selectbox("세그먼트", ["전체", "20대", "30대", "40대"])

# KPI 메트릭
st.markdown("---")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("총 노출수", "125.3K", "+12.5%")
with col2:
    st.metric("클릭수", "4,235", "+8.3%")
with col3:
    st.metric("평균 CTR", "3.38%", "+0.23%")
with col4:
    st.metric("전환율", "2.1%", "-0.1%")
with col5:
    st.metric("참여율", "5.7%", "+1.2%")

# 차트 섹션
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    # 일별 성과 추이
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    df_daily = pd.DataFrame({
        '날짜': dates,
        'CTR': [3.2 + (i % 7) * 0.2 for i in range(len(dates))],
        '참여율': [5.5 + (i % 5) * 0.3 for i in range(len(dates))]
    })

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df_daily['날짜'], y=df_daily['CTR'],
                               mode='lines+markers', name='CTR (%)',
                               line=dict(color='#667eea')))
    fig1.add_trace(go.Scatter(x=df_daily['날짜'], y=df_daily['참여율'],
                               mode='lines+markers', name='참여율 (%)',
                               line=dict(color='#764ba2')))
    fig1.update_layout(title="일별 성과 추이", height=400)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    # 세그먼트별 성과
    df_segment = pd.DataFrame({
        '세그먼트': ['20대', '30대', '40대', '50대+'],
        'CTR': [3.8, 3.2, 2.9, 2.5],
        '전환율': [2.5, 2.2, 1.9, 1.6]
    })

    fig2 = px.bar(df_segment, x='세그먼트', y=['CTR', '전환율'],
                  title="세그먼트별 성과 비교", barmode='group',
                  color_discrete_map={'CTR': '#667eea', '전환율': '#764ba2'})
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, use_container_width=True)

# 상위 성과 콘텐츠
st.markdown("---")
st.subheader("🏆 상위 성과 콘텐츠")

df_top = pd.DataFrame({
    '순위': [1, 2, 3, 4, 5],
    '캠페인': ['여름 세일', '신제품 출시', '여름 세일', '브랜드 인지도', '신제품 출시'],
    '세그먼트': ['20대 여성', '30대 남성', '20대 남성', '40대 여성', '30대 여성'],
    '카피': ['🏃‍♀️ 여름을 위한 완벽한 준비!', '🚀 혁신의 시작', '💪 당신의 여름을 바꿔줄', '✨ 품격있는 선택', '🎯 스마트한 당신을 위한'],
    'CTR': ['4.2%', '3.9%', '3.7%', '3.5%', '3.3%'],
    '참여율': ['7.1%', '6.8%', '6.5%', '6.2%', '5.9%']
})

st.dataframe(
    df_top,
    use_container_width=True,
    hide_index=True,
    column_config={
        "순위": st.column_config.NumberColumn("순위", width=50),
        "CTR": st.column_config.ProgressColumn("CTR", min_value=0, max_value=10, format="%.1f%%"),
        "참여율": st.column_config.ProgressColumn("참여율", min_value=0, max_value=10, format="%.1f%%")
    }
)

# AI 인사이트
st.markdown("---")
st.subheader("🤖 AI 인사이트")

insight = st.info("""
### 주요 발견사항:

1. **20대 세그먼트 성과 우수**: 20대 타겟 콘텐츠의 평균 CTR이 3.8%로 가장 높음
2. **이모지 사용 효과적**: 제목에 이모지를 포함한 콘텐츠가 평균 15% 높은 참여율 기록
3. **오전 10-11시 최적**: 오전 10-11시 게시된 콘텐츠의 도달률이 가장 높음

### 추천 액션:
- 20대 세그먼트에 더 많은 예산 할당 고려
- 모든 헤드라인에 관련 이모지 추가
- 주요 콘텐츠는 오전 10시 전후로 게시
""")

# 다운로드 버튼
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col2:
    if st.button("📥 리포트 다운로드", type="primary", use_container_width=True):
        st.toast("PDF 리포트 생성 중...")
        st.balloons()
