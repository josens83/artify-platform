import streamlit as st
import requests
import json

st.set_page_config(page_title="세그먼트 관리", page_icon="🎯")
st.title("🎯 세그먼트 관리")

API_URL = "https://artify-content-api.onrender.com"

# 세그먼트 생성 폼
with st.form("segment_form"):
    st.subheader("새 세그먼트 생성")

    name = st.text_input("세그먼트 이름", placeholder="예: 20대 여성 피트니스")

    col1, col2 = st.columns(2)
    with col1:
        age_min, age_max = st.slider("연령대", 10, 80, (20, 35))
        gender = st.selectbox("성별", ["전체", "남성", "여성"])

    with col2:
        interests = st.multiselect(
            "관심사",
            ["피트니스", "패션", "뷰티", "테크", "여행", "음식"]
        )
        location = st.text_input("지역", placeholder="서울")

    # JSON 필터 생성
    filters = {
        "age_range": [age_min, age_max],
        "gender": gender,
        "interests": interests,
        "location": location
    }

    st.json(filters)

    if st.form_submit_button("저장", type="primary"):
        # 실제로는 API 호출
        st.success(f"✅ '{name}' 세그먼트 저장 완료!")
        st.balloons()

# 저장된 세그먼트 목록
st.divider()
st.subheader("저장된 세그먼트")

# 샘플 데이터 (나중에 API에서 가져옴)
segments = st.session_state.get('segments', [])
if not segments:
    segments = [
        {"name": "20대 피트니스", "filters": {"age_range": [20, 29], "interests": ["피트니스"]}},
        {"name": "30대 테크", "filters": {"age_range": [30, 39], "interests": ["테크"]}}
    ]

for seg in segments:
    with st.expander(seg['name']):
        st.json(seg['filters'])
        if st.button(f"삭제", key=f"del_{seg['name']}"):
            st.warning(f"삭제됨: {seg['name']}")
