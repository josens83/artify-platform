# Artify Content Backend

FastAPI + PostgreSQL + OpenAI 기반 AI 콘텐츠 생성 및 분석 API

## 🚀 시작하기

### 필수 요구사항

- Python 3.8+
- PostgreSQL 12+
- OpenAI API Key

### 설치

```bash
# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 환경 변수 설정

`.env` 파일 생성:

#### 옵션 1: 로컬 PostgreSQL

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/artify_content_db

# OpenAI API Key
OPENAI_API_KEY=sk-...

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

#### 옵션 2: Supabase (권장 - 프로덕션 환경)

```env
# Supabase PostgreSQL 연결
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.joywrnyrvpsaevhiqokw.supabase.co:5432/postgres

# Supabase 프로젝트 정보
# 프로젝트명: artify-content
# Region: Singapore (Southeast Asia)
# 프로젝트 ID: joywrnyrvpsaevhiqokw
# API URL: https://joywrnyrvpsaevhiqokw.supabase.co
# Dashboard: https://supabase.com/dashboard/project/joywrnyrvpsaevhiqokw

# OpenAI API Key
OPENAI_API_KEY=sk-...

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

### 데이터베이스 초기화

#### 옵션 1: 로컬 PostgreSQL

```bash
# PostgreSQL 접속
psql -U postgres

# 데이터베이스 생성
CREATE DATABASE artify_content_db;
```

#### 옵션 2: Supabase (권장)

Supabase는 이미 설정되어 있습니다:
- 프로젝트명: **artify-content**
- Region: **Singapore (Southeast Asia)**
- 프로젝트 ID: `joywrnyrvpsaevhiqokw`
- Connection String: Supabase Dashboard → Database → Connection String에서 확인

**Supabase 대시보드에서:**
1. Settings → Database 이동
2. Connection String 복사 (URI 형식)
3. `.env` 파일의 `DATABASE_URL`에 붙여넣기
4. `[YOUR-PASSWORD]`를 실제 비밀번호로 교체

서버가 시작될 때 자동으로 테이블이 생성됩니다 (SQLAlchemy ORM).

### 실행

```bash
# 개발 모드 (자동 리로드)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

서버가 http://localhost:8000 에서 실행됩니다.

## 📚 API 문서

FastAPI는 자동으로 API 문서를 생성합니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## 🎨 AI 콘텐츠 생성

### 1. 텍스트 생성 (GPT-3.5-turbo)

AI를 사용하여 마케팅 텍스트를 생성합니다.

**요청**
```
POST /generate/text
Content-Type: application/json

{
  "prompt": "커피숍을 위한 마케팅 슬로건을 작성해주세요",
  "segment_id": 1,
  "tone": "친근한",
  "keywords": ["커피", "아침", "신선함"],
  "max_tokens": 100
}
```

**매개변수**
- `prompt` (필수): 생성 요청 프롬프트
- `segment_id` (선택): 타겟 세그먼트 ID
- `tone` (선택): 톤 ("전문적", "친근한", "유머러스" 등)
- `keywords` (선택): 포함할 키워드 목록
- `max_tokens` (선택): 최대 토큰 수 (기본값: 150)

**응답 (200 OK)**
```json
{
  "success": true,
  "text": "아침을 시작하는 가장 신선한 방법! 우리 커피숍에서 하루를 활기차게 시작하세요. ☕✨",
  "usage": {
    "prompt_tokens": 45,
    "completion_tokens": 32,
    "total_tokens": 77
  },
  "cost": 0.0001065,
  "model": "gpt-3.5-turbo"
}
```

**에러 응답**

- `503 Service Unavailable`: OpenAI API 키 미설정
  ```json
  { "detail": "OpenAI API key not configured. Please set OPENAI_API_KEY." }
  ```

- `500 Internal Server Error`: 생성 실패
  ```json
  { "detail": "Failed to generate text: ..." }
  ```

### 2. 이미지 생성 (DALL-E 3)

AI를 사용하여 마케팅 이미지를 생성합니다.

**요청**
```
POST /generate/image
Content-Type: application/json

{
  "prompt": "A modern coffee shop interior with warm lighting",
  "size": "1024x1024",
  "quality": "standard"
}
```

**매개변수**
- `prompt` (필수): 이미지 설명
- `size` (선택): 이미지 크기
  - `"1024x1024"` (기본값)
  - `"1024x1792"` (세로)
  - `"1792x1024"` (가로)
- `quality` (선택): 품질 (`"standard"` 또는 `"hd"`)

**응답 (200 OK)**
```json
{
  "success": true,
  "image_url": "https://oaidalleapiprodscus.blob.core.windows.net/...",
  "revised_prompt": "A contemporary coffee shop interior featuring warm, inviting lighting...",
  "cost": 0.040,
  "model": "dall-e-3",
  "size": "1024x1024"
}
```

**에러 응답**

- `503 Service Unavailable`: OpenAI API 키 미설정
- `500 Internal Server Error`: 생성 실패

---

## 🎯 세그먼트 관리

### 3. 세그먼트 목록 조회

모든 타겟 세그먼트를 조회합니다.

**요청**
```
GET /segments
```

**응답 (200 OK)**
```json
{
  "segments": [
    {
      "id": 1,
      "name": "2030 여성",
      "description": "20-30대 여성 고객층",
      "criteria": "{\"age_range\": \"20-30\", \"gender\": \"female\"}",
      "created_at": "2024-11-01T10:00:00",
      "updated_at": "2024-11-01T10:00:00"
    },
    {
      "id": 2,
      "name": "기업 고객",
      "description": "B2B 기업 고객",
      "criteria": "{\"type\": \"business\"}",
      "created_at": "2024-11-02T14:30:00",
      "updated_at": "2024-11-02T14:30:00"
    }
  ]
}
```

### 4. 세그먼트 생성

새 타겟 세그먼트를 생성합니다.

**요청**
```
POST /segments
Content-Type: application/json

{
  "name": "밀레니얼 부모",
  "description": "자녀를 둔 30대 부모",
  "criteria": {
    "age_range": "30-40",
    "has_children": true
  }
}
```

**응답 (200 OK)**
```json
{
  "id": 3,
  "name": "밀레니얼 부모",
  "description": "자녀를 둔 30대 부모",
  "criteria": "{\"age_range\": \"30-40\", \"has_children\": true}",
  "created_at": "2024-11-07T16:00:00",
  "updated_at": "2024-11-07T16:00:00"
}
```

### 5. 세그먼트 삭제

세그먼트를 삭제합니다.

**요청**
```
DELETE /segments/{segment_id}
```

**응답 (200 OK)**
```json
{
  "message": "Segment deleted successfully"
}
```

**에러 응답**

- `404 Not Found`: 세그먼트가 없음
  ```json
  { "detail": "Segment not found" }
  ```

---

## 📊 분석 대시보드

### 6. 분석 개요

캠페인 성과 분석 데이터를 조회합니다.

**요청**
```
GET /analytics/overview?project_id=1
```

**매개변수**
- `project_id` (선택): 특정 프로젝트 필터링

**응답 (200 OK)**
```json
{
  "total_campaigns": 25,
  "total_impressions": 150000,
  "total_clicks": 7500,
  "total_conversions": 450,
  "avg_ctr": 5.0,
  "avg_conversion_rate": 6.0
}
```

### 7. 콘텐츠 생성 내역

AI로 생성된 콘텐츠 내역을 조회합니다.

**요청**
```
GET /content/history?limit=20
```

**매개변수**
- `limit` (선택): 최대 결과 수 (기본값: 50)
- `content_type` (선택): 필터링 (`"text"` 또는 `"image"`)

**응답 (200 OK)**
```json
{
  "history": [
    {
      "id": 15,
      "content_type": "text",
      "prompt": "커피숍 마케팅 슬로건",
      "result": "아침을 시작하는 가장 신선한 방법!",
      "model": "gpt-3.5-turbo",
      "created_at": "2024-11-07T15:30:00"
    },
    {
      "id": 14,
      "content_type": "image",
      "prompt": "A modern coffee shop interior",
      "result": "https://oaidalleapiprodscus.blob...",
      "model": "dall-e-3",
      "created_at": "2024-11-07T14:20:00"
    }
  ],
  "total": 2
}
```

---

## 💰 비용 추적

### 8. 비용 요약

AI 생성 비용 요약을 조회합니다.

**요청**
```
GET /costs/summary?user_id=1
```

**매개변수**
- `user_id` (선택): 특정 사용자 필터링

**응답 (200 OK)**
```json
{
  "total_cost": 12.45,
  "total_jobs": 342,
  "text_jobs": 280,
  "image_jobs": 62,
  "text_cost": 8.23,
  "image_cost": 4.22,
  "cost_by_model": {
    "gpt-3.5-turbo": 8.23,
    "dall-e-3": 4.22
  },
  "period": {
    "start": "2024-10-01T00:00:00",
    "end": "2024-11-07T16:00:00"
  }
}
```

### 9. 비용 내역

상세 비용 내역을 조회합니다.

**요청**
```
GET /costs/history?limit=50
```

**매개변수**
- `limit` (선택): 최대 결과 수 (기본값: 50)
- `user_id` (선택): 특정 사용자 필터링
- `job_type` (선택): 작업 유형 필터링 (`"text"` 또는 `"image"`)

**응답 (200 OK)**
```json
{
  "history": [
    {
      "id": 342,
      "user_id": 1,
      "job_type": "text",
      "model": "gpt-3.5-turbo",
      "prompt": "커피숍 마케팅 슬로건",
      "prompt_tokens": 45,
      "completion_tokens": 32,
      "total_tokens": 77,
      "estimated_cost": 0.0001065,
      "status": "completed",
      "created_at": "2024-11-07T15:30:00",
      "completed_at": "2024-11-07T15:30:02"
    },
    {
      "id": 341,
      "user_id": 1,
      "job_type": "image",
      "model": "dall-e-3",
      "prompt": "A modern coffee shop interior",
      "estimated_cost": 0.040,
      "status": "completed",
      "created_at": "2024-11-07T14:20:00",
      "completed_at": "2024-11-07T14:20:15"
    }
  ],
  "total": 2
}
```

---

## 🔍 기타 엔드포인트

### 10. API 정보

API 기본 정보를 조회합니다.

**요청**
```
GET /
```

**응답 (200 OK)**
```json
{
  "service": "Artify Content Backend",
  "version": "2.0.0",
  "status": "healthy",
  "openai_configured": true,
  "database": "connected"
}
```

### 11. 헬스 체크

서비스 상태를 확인합니다.

**요청**
```
GET /health
```

**응답 (200 OK)**
```json
{
  "status": "healthy",
  "timestamp": "2024-11-07T16:00:00.000Z"
}
```

---

## 💵 가격 정책 (2024년 OpenAI 기준)

### 텍스트 생성

| 모델 | 입력 토큰 | 출력 토큰 |
|------|-----------|-----------|
| GPT-3.5-turbo | $0.0005 / 1K | $0.0015 / 1K |
| GPT-4 | $0.03 / 1K | $0.06 / 1K |

### 이미지 생성

| 모델 | 크기 | 가격 |
|------|------|------|
| DALL-E 3 | 1024×1024 | $0.040 |
| DALL-E 3 | 1024×1792 | $0.080 |
| DALL-E 3 | 1792×1024 | $0.080 |
| DALL-E 3 HD | 1024×1024 | $0.080 |

---

## 🗃️ 데이터베이스 스키마

**Supabase Database: artify-content**

**총 7개 테이블 + 6개 인덱스**

### 정적 데이터 테이블

#### users 테이블 (사용자)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | INTEGER | PRIMARY KEY | 사용자 ID |
| username | VARCHAR(255) | UNIQUE, NOT NULL | 사용자명 |
| email | VARCHAR(255) | UNIQUE, NOT NULL | 이메일 |
| password_hash | VARCHAR(255) | NOT NULL | 해시된 비밀번호 |
| created_at | TIMESTAMP | DEFAULT NOW() | 생성일시 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 수정일시 |

#### campaigns 테이블 (캠페인)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | INTEGER | PRIMARY KEY | 캠페인 ID |
| user_id | INTEGER | FK → users.id | 소유자 ID |
| name | VARCHAR(255) | NOT NULL | 캠페인명 |
| description | TEXT | | 설명 |
| status | VARCHAR(50) | DEFAULT 'draft' | 상태: 'draft', 'active', 'paused', 'completed' |
| budget | FLOAT | | 예산 |
| start_date | TIMESTAMP | | 시작일 |
| end_date | TIMESTAMP | | 종료일 |
| created_at | TIMESTAMP | DEFAULT NOW() | 생성일시 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 수정일시 |

#### segments 테이블 (타겟 세그먼트)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | INTEGER | PRIMARY KEY | 세그먼트 ID |
| name | VARCHAR(255) | NOT NULL | 세그먼트명 |
| description | TEXT | | 설명 |
| criteria | TEXT | | JSON 형식 타겟팅 기준 |
| created_at | TIMESTAMP | DEFAULT NOW() | 생성일시 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 수정일시 |

### 동적 데이터 테이블

#### creatives 테이블 (생성된 콘텐츠)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | INTEGER | PRIMARY KEY | 콘텐츠 ID |
| campaign_id | INTEGER | FK → campaigns.id | 캠페인 ID |
| content_type | VARCHAR(50) | NOT NULL | 콘텐츠 유형: 'text', 'image', 'video' |
| prompt | TEXT | NOT NULL | 생성 프롬프트 |
| result | TEXT | NOT NULL | 생성 결과 (텍스트 또는 URL) |
| model | VARCHAR(100) | | 사용 모델: 'gpt-3.5-turbo', 'dall-e-3' |
| status | VARCHAR(50) | DEFAULT 'completed' | 상태: 'pending', 'completed', 'failed' |
| created_at | TIMESTAMP | DEFAULT NOW() | 생성일시 |

**인덱스:** `idx_creatives_campaign_id` ON campaign_id

#### gen_jobs 테이블 (AI 생성 작업 로그 - 비용 추적)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | INTEGER | PRIMARY KEY | 작업 ID |
| user_id | INTEGER | FK → users.id | 사용자 ID |
| job_type | VARCHAR(50) | NOT NULL | 작업 유형: 'text', 'image' |
| model | VARCHAR(100) | NOT NULL | 사용 모델 |
| prompt | TEXT | NOT NULL | 프롬프트 |
| prompt_tokens | INTEGER | | 입력 토큰 수 (텍스트 생성 시) |
| completion_tokens | INTEGER | | 출력 토큰 수 (텍스트 생성 시) |
| total_tokens | INTEGER | | 전체 토큰 수 |
| estimated_cost | FLOAT | DEFAULT 0.0 | 예상 비용 (USD) |
| status | VARCHAR(50) | DEFAULT 'completed' | 상태: 'pending', 'completed', 'failed' |
| error_message | TEXT | | 에러 메시지 |
| created_at | TIMESTAMP | DEFAULT NOW() | 생성일시 |
| completed_at | TIMESTAMP | | 완료일시 |

**인덱스:**
- `idx_gen_jobs_user_id` ON user_id
- `idx_gen_jobs_created_at` ON created_at

#### metrics 테이블 (성과 데이터)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | INTEGER | PRIMARY KEY | 메트릭 ID |
| campaign_id | INTEGER | FK → campaigns.id | 캠페인 ID |
| metric_name | VARCHAR(255) | NOT NULL | 메트릭명: 'impressions', 'clicks', 'conversions' |
| metric_value | FLOAT | NOT NULL | 메트릭 값 |
| timestamp | TIMESTAMP | DEFAULT NOW() | 측정 시간 |

**인덱스:** `idx_metrics_campaign_id` ON campaign_id

#### feedbacks 테이블 (피드백)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | INTEGER | PRIMARY KEY | 피드백 ID |
| creative_id | INTEGER | FK → creatives.id | 콘텐츠 ID |
| user_id | INTEGER | FK → users.id | 사용자 ID |
| rating | INTEGER | CHECK (1-5) | 평점 (1-5) |
| comment | TEXT | | 피드백 내용 |
| created_at | TIMESTAMP | DEFAULT NOW() | 생성일시 |

**인덱스:** `idx_feedbacks_creative_id` ON creative_id

### 데이터베이스 인덱스 요약

총 **6개 인덱스**로 쿼리 성능 최적화:

1. `idx_campaigns_user_id` ON campaigns(user_id)
2. `idx_creatives_campaign_id` ON creatives(campaign_id)
3. `idx_gen_jobs_user_id` ON gen_jobs(user_id)
4. `idx_gen_jobs_created_at` ON gen_jobs(created_at)
5. `idx_metrics_campaign_id` ON metrics(campaign_id)
6. `idx_feedbacks_creative_id` ON feedbacks(creative_id)

### 외래 키 관계

```
users (1) ──< campaigns (N)
users (1) ──< gen_jobs (N)
users (1) ──< feedbacks (N)

campaigns (1) ──< creatives (N)
campaigns (1) ──< metrics (N)

creatives (1) ──< feedbacks (N)
```

---

## 🧪 테스트

### cURL 예제

#### 텍스트 생성
```bash
curl -X POST http://localhost:8000/generate/text \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "커피숍 마케팅 슬로건을 작성해주세요",
    "tone": "친근한",
    "max_tokens": 100
  }'
```

#### 이미지 생성
```bash
curl -X POST http://localhost:8000/generate/image \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A modern coffee shop interior with warm lighting",
    "size": "1024x1024"
  }'
```

#### 세그먼트 조회
```bash
curl http://localhost:8000/segments
```

#### 비용 요약
```bash
curl http://localhost:8000/costs/summary
```

---

## 📦 의존성

```txt
fastapi==0.104.1         # 웹 프레임워크
uvicorn==0.24.0          # ASGI 서버
sqlalchemy==2.0.23       # ORM
psycopg2-binary==2.9.9   # PostgreSQL 드라이버
python-dotenv==1.0.0     # 환경변수 관리
openai==1.3.5            # OpenAI API 클라이언트
pydantic==2.5.0          # 데이터 검증
```

---

## 🚀 배포

### Render

1. Render 대시보드에서 "New PostgreSQL" 생성
2. "New Web Service" 생성
3. GitHub 저장소 연결
4. 환경 변수 설정:
   - `DATABASE_URL` (Render PostgreSQL URL)
   - `OPENAI_API_KEY` (OpenAI API 키)
5. Build Command: `pip install -r requirements.txt`
6. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t artify-content-backend .
docker run -p 8000:8000 --env-file .env artify-content-backend
```

---

## 🐛 트러블슈팅

### OpenAI API 키 오류

```
⚠️ WARNING: OPENAI_API_KEY not set
```

**해결**: `.env` 파일에 유효한 OpenAI API 키 설정

### 데이터베이스 연결 오류

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**해결**: `DATABASE_URL`이 올바른지 확인하고 PostgreSQL 서버가 실행 중인지 확인

### Rate Limit 오류 (OpenAI)

```
openai.error.RateLimitError: Rate limit reached
```

**해결**: OpenAI 계정의 사용량 제한 확인 및 업그레이드

---

## 📞 지원

이슈가 있으시면 GitHub Issues에 등록해주세요.

**API 문서**: http://localhost:8000/docs
