import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from config import settings

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

st.title("📊 Content Performance Dashboard")
st.markdown("콘텐츠 성과 및 분석 대시보드")
st.markdown("---")

# 기간 선택
col1, col2, col3 = st.columns([2, 2, 6])
with col1:
    date_from = st.date_input("시작일", datetime.now() - timedelta(days=30))
with col2:
    date_to = st.date_input("종료일", datetime.now())

# KPI 메트릭
st.subheader("📈 주요 지표")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("총 콘텐츠", "1,234", "+56")
with col2:
    st.metric("총 조회수", "125.5K", "+12.3K")
with col3:
    st.metric("평균 참여율", "4.8%", "+0.3%")
with col4:
    st.metric("전환율", "2.1%", "+0.2%")
with col5:
    st.metric("ROI", "245%", "+15%")

st.markdown("---")

# 차트 섹션
col1, col2 = st.columns(2)

with col1:
    st.subheader("📅 일별 성과 추이")

    # 샘플 데이터
    dates = pd.date_range(start=date_from, end=date_to, freq='D')
    df_performance = pd.DataFrame({
        'Date': dates,
        'Views': [1000 + i * 50 for i in range(len(dates))],
        'Engagement': [500 + i * 25 for i in range(len(dates))],
        'Conversions': [50 + i * 3 for i in range(len(dates))]
    })

    fig = px.line(df_performance, x='Date', y=['Views', 'Engagement', 'Conversions'],
                  title='성과 지표 추이')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 콘텐츠 타입별 분포")

    # 샘플 데이터
    df_content_type = pd.DataFrame({
        'Type': ['Social Post', 'Blog Article', 'Email', 'Ad Copy'],
        'Count': [450, 320, 280, 184]
    })

    fig = px.pie(df_content_type, values='Count', names='Type',
                 title='콘텐츠 타입 분포')
    st.plotly_chart(fig, use_container_width=True)

# 세그먼트별 성과
st.markdown("---")
st.subheader("🎯 세그먼트별 성과")

df_segments = pd.DataFrame({
    'Segment': ['Tech Enthusiasts', 'Fashion Lovers', 'Food Bloggers'],
    'Contents': [456, 389, 389],
    'Views': [45600, 38900, 41000],
    'Engagement Rate': [5.2, 4.5, 4.8],
    'Conversion Rate': [2.3, 1.9, 2.1]
})

st.dataframe(df_segments, use_container_width=True)

# 상위 콘텐츠
st.markdown("---")
st.subheader("🏆 Top 10 콘텐츠")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("##### 👀 최다 조회")
    for i in range(1, 6):
        st.write(f"{i}. Tech Innovation Post - 12.5K views")

with col2:
    st.markdown("##### 💬 최다 참여")
    for i in range(1, 6):
        st.write(f"{i}. Fashion Trend Article - 890 engagements")

with col3:
    st.markdown("##### 💰 최다 전환")
    for i in range(1, 6):
        st.write(f"{i}. Food Recipe Email - 145 conversions")

# 사이드바
with st.sidebar:
    st.subheader("필터")

    segment_filter = st.multiselect(
        "세그먼트",
        ["Tech Enthusiasts", "Fashion Lovers", "Food Bloggers"],
        default=["Tech Enthusiasts", "Fashion Lovers", "Food Bloggers"]
    )

    content_type_filter = st.multiselect(
        "콘텐츠 타입",
        ["Social Post", "Blog Article", "Email", "Ad Copy"],
        default=["Social Post", "Blog Article", "Email", "Ad Copy"]
    )

    if st.button("필터 적용", use_container_width=True):
        st.rerun()

    st.markdown("---")

    if st.button("📥 리포트 다운로드", use_container_width=True):
        st.success("리포트가 다운로드되었습니다!")
