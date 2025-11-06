# Content Management Backend

FastAPI 기반 AI 콘텐츠 관리 백엔드 - Supabase & ChromaDB 통합

## 🚀 Features

- **Supabase**: PostgreSQL 데이터베이스 직접 연결
- **ChromaDB**: 임베디드 모드 벡터 DB (별도 서버 불필요)
- **OpenAI**: 자동 임베딩 생성
- **FastAPI**: 고성능 비동기 REST API

## 📁 프로젝트 구조

```
content-backend/
├── main.py                  # FastAPI 애플리케이션
├── requirements.txt         # Python 의존성
├── .env.example             # 환경 변수 템플릿
├── models/
│   ├── __init__.py
│   └── database.py          # Supabase 클라이언트
├── routers/
│   ├── __init__.py
│   ├── auth.py              # 인증
│   ├── campaigns.py         # 캠페인 관리
│   ├── segments.py          # 세그먼트 관리
│   ├── creatives.py         # 크리에이티브 관리
│   └── vector_search.py     # 벡터 검색
└── utils/
    ├── __init__.py
    ├── config.py            # 설정
    └── vector.py            # ChromaDB 클라이언트
```

## 🛠️ 설치 및 실행

### 1. 의존성 설치

```bash
cd content-backend
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일 편집:
```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# OpenAI
OPENAI_API_KEY=sk-your-api-key

# ChromaDB
CHROMA_PERSIST_DIR=./chroma_data
```

### 3. 서버 실행

```bash
# 개발 모드 (auto-reload)
uvicorn main:app --reload --port 8001

# 또는
python main.py
```

서버: http://localhost:8001
API Docs: http://localhost:8001/docs

## 📡 API 엔드포인트

### Campaigns (캠페인)

- `POST /api/campaigns` - 캠페인 생성
- `GET /api/campaigns` - 캠페인 목록
- `GET /api/campaigns/{id}` - 캠페인 조회
- `PUT /api/campaigns/{id}` - 캠페인 수정
- `DELETE /api/campaigns/{id}` - 캠페인 삭제

### Segments (세그먼트)

- `POST /api/segments` - 세그먼트 생성
- `GET /api/segments` - 세그먼트 목록
- `GET /api/segments/{id}` - 세그먼트 조회
- `PUT /api/segments/{id}` - 세그먼트 수정
- `DELETE /api/segments/{id}` - 세그먼트 삭제

### Creatives (크리에이티브)

- `POST /api/creatives` - 크리에이티브 생성 (자동으로 벡터 DB에 추가)
- `GET /api/creatives` - 크리에이티브 목록
- `GET /api/creatives/{id}` - 크리에이티브 조회
- `PUT /api/creatives/{id}` - 크리에이티브 수정
- `DELETE /api/creatives/{id}` - 크리에이티브 삭제
- `POST /api/creatives/{id}/similar` - 유사 크리에이티브 검색

### Vector Search (벡터 검색)

- `POST /api/vector/search` - 벡터 유사도 검색
- `GET /api/vector/collections` - 컬렉션 목록
- `GET /api/vector/collections/{name}/info` - 컬렉션 정보

## 💡 사용 예제

### 1. 캠페인 생성

```bash
curl -X POST "http://localhost:8001/api/campaigns" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Summer Sale 2024",
    "objective": "awareness",
    "channel": "facebook",
    "start_date": "2024-06-01",
    "end_date": "2024-08-31"
  }'
```

### 2. 크리에이티브 생성 (자동 임베딩)

```bash
curl -X POST "http://localhost:8001/api/creatives" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": 1,
    "segment_id": 5,
    "copy_text": "Discover amazing summer deals! 50% off all products.",
    "meta": {"tone": "exciting", "length": "short"}
  }'
```

### 3. 유사 콘텐츠 검색

```bash
curl -X POST "http://localhost:8001/api/vector/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "summer sales promotion",
    "collection": "copy_texts",
    "top_k": 5
  }'
```

### 4. 특정 크리에이티브의 유사 항목 찾기

```bash
curl -X POST "http://localhost:8001/api/creatives/123/similar?top_k=5"
```

## 🗄️ 데이터베이스 스키마

Supabase에 다음 테이블이 필요합니다:

- `users` - 사용자
- `campaigns` - 캠페인
- `segments` - 세그먼트
- `creatives` - 크리에이티브
- `gen_jobs` - AI 생성 작업
- `metrics` - 성과 지표
- `feedbacks` - 피드백

스키마는 `../content-db/schema.sql` 참조

## 📊 ChromaDB 컬렉션

3개의 벡터 컬렉션이 자동 생성됩니다:

- `copy_texts` - 텍스트 카피 임베딩
- `images` - 이미지 메타데이터 임베딩
- `templates` - 템플릿 임베딩

데이터는 `./chroma_data` 디렉토리에 저장됩니다.

## 🔒 인증

현재는 placeholder 인증을 사용합니다 (user_id=1).
프로덕션에서는 `routers/auth.py`의 JWT 인증을 활성화해야 합니다.

## 🐛 디버깅

로그 확인:
```bash
# 서버 실행 시 자동으로 로그 출력
# INFO 레벨로 설정됨
```

## 📝 TODO

- [ ] JWT 인증 완전 구현
- [ ] Rate limiting 추가
- [ ] 벡터 검색 필터링 고도화
- [ ] 배치 임베딩 최적화
- [ ] 캐싱 레이어 추가

## 📄 라이선스

MIT License
