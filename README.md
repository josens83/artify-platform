# Artify Platform 🎨

AI 기반 마케팅 콘텐츠 생성 플랫폼

Artify는 AI를 활용하여 마케팅 캠페인을 위한 비주얼 콘텐츠를 빠르고 쉽게 생성할 수 있는 통합 플랫폼입니다.

## 🌟 주요 기능

- **🎨 비주얼 에디터**: Fabric.js 기반의 강력한 캔버스 에디터
  - 도형, 텍스트, 이미지 추가 및 편집
  - Undo/Redo 기능
  - 레이어 관리
  - 템플릿 시스템 (소셜 미디어, 배너, 포스터)

- **✨ AI 콘텐츠 생성**: OpenAI API 통합
  - GPT-3.5-turbo로 텍스트 생성
  - DALL-E 3로 이미지 생성
  - 비용 추적 시스템

- **💾 자동 저장**: 5초 간격 자동 저장
  - 실시간 변경 감지
  - 시각적 저장 상태 표시

- **📤 다중 포맷 내보내기**
  - PNG (고해상도)
  - JPG (압축)
  - PDF (A4 자동 조정)
  - JSON (프로젝트 데이터)

- **🎯 세그먼트 관리**: 타겟 고객 세그먼트 생성
- **📊 분석 대시보드**: 캠페인 성과 분석
- **🔐 사용자 인증**: JWT 기반 인증 시스템
- **⚡ Rate Limiting**: API 남용 방지

## 🏗️ 프로젝트 구조

```
artify-platform/
├── frontend/              # Vanilla JavaScript SPA
│   ├── index.html         # 메인 페이지
│   ├── editor.html        # 에디터 페이지
│   ├── css/               # 스타일시트
│   └── js/
│       ├── state.js       # 상태 관리 (LocalStorage 동기화)
│       ├── api.js         # API 클라이언트
│       ├── router.js      # Hash 기반 라우팅
│       ├── ui-kit.js      # UI 컴포넌트
│       ├── home.js        # 홈 페이지 로직
│       ├── editor.js      # 에디터 핵심 로직 (1500+ lines)
│       └── panels/        # 패널 컴포넌트
│           ├── panel-generate.js    # AI 생성 패널
│           ├── panel-segments.js    # 세그먼트 관리
│           ├── panel-analytics.js   # 분석 대시보드
│           └── panel-history.js     # 히스토리 패널
│
├── backend/               # Node.js Express + PostgreSQL
│   ├── server.js          # Express 서버 (JWT, Rate Limiting, Swagger)
│   ├── database.js        # PostgreSQL 연결 및 ORM
│   ├── package.json       # 의존성 관리
│   └── README.md          # Backend API 문서
│
├── content-backend/       # FastAPI + Supabase + OpenAI
│   ├── main.py            # FastAPI 앱 (AI 생성, 분석)
│   ├── database.py        # SQLAlchemy 모델 (7 tables)
│   ├── requirements.txt   # Python 의존성
│   └── README.md          # Content Backend API 문서
│
├── content-vector/        # ChromaDB Vector Database (RAG)
│   ├── client.py          # ChromaDB 클라이언트 (351 lines)
│   ├── config.py          # 설정 관리
│   ├── requirements.txt   # ChromaDB, OpenAI
│   ├── .env.example       # 환경 변수 예제
│   └── Dockerfile         # Docker 컨테이너화
│
├── content-db/            # Database 스키마 및 마이그레이션
│   └── [DB 관련 파일]
│
└── README.md              # 메인 문서 (이 파일)
```

## 🚀 빠른 시작

### 필수 요구사항

- Node.js 16+
- Python 3.8+
- PostgreSQL 12+
- OpenAI API Key (선택사항)

### 1. 저장소 클론

```bash
git clone <repository-url>
cd artify-platform
```

### 2. 환경 변수 설정

#### Backend (.env)

```bash
cd backend
cp .env.example .env
```

`.env` 파일 편집:

```env
PORT=3001
NODE_ENV=development
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
DATABASE_URL=postgresql://username:password@localhost:5432/artify_db
```

#### Content Backend (.env)

```bash
cd ../content-backend
cp .env.example .env
```

`.env` 파일 편집:

**로컬 PostgreSQL 사용 시:**
```env
DATABASE_URL=postgresql://username:password@localhost:5432/artify_content_db
OPENAI_API_KEY=sk-...
HOST=0.0.0.0
PORT=8000
```

**Supabase 사용 시 (권장):**
```env
# Supabase PostgreSQL 연결
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.joywrnyrvpsaevhiqokw.supabase.co:5432/postgres

# Supabase 프로젝트 정보
# 프로젝트명: artify-content
# Region: Singapore (Southeast Asia)
# 프로젝트 ID: joywrnyrvpsaevhiqokw
# API URL: https://joywrnyrvpsaevhiqokw.supabase.co

OPENAI_API_KEY=sk-...
HOST=0.0.0.0
PORT=8000
```

### 3. 데이터베이스 설정

#### 옵션 1: 로컬 PostgreSQL

로컬 PostgreSQL에 데이터베이스 생성:

```bash
# PostgreSQL 접속
psql -U postgres

# 데이터베이스 생성
CREATE DATABASE artify_db;
CREATE DATABASE artify_content_db;

# 사용자 생성 및 권한 부여 (선택사항)
CREATE USER artify_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE artify_db TO artify_user;
GRANT ALL PRIVILEGES ON DATABASE artify_content_db TO artify_user;
```

#### 옵션 2: Supabase (권장)

**Content Backend는 Supabase를 사용합니다:**

1. Supabase 프로젝트: `artify-content`
2. Region: Singapore (Southeast Asia)
3. 프로젝트 ID: `joywrnyrvpsaevhiqokw`
4. Database URL: `postgresql://postgres:[PASSWORD]@db.joywrnyrvpsaevhiqokw.supabase.co:5432/postgres`

Supabase 대시보드에서:
- Database → Connection String 복사
- `.env` 파일의 `DATABASE_URL`에 붙여넣기

**Backend는 로컬 PostgreSQL 또는 별도 클라우드 DB 사용**

### 4. Backend 설치 및 실행

```bash
cd backend

# 의존성 설치
npm install

# 서버 실행
npm start
```

서버가 http://localhost:3001 에서 실행됩니다.

#### 주요 엔드포인트

- `GET /api/health` - 헬스 체크
- `POST /api/register` - 회원가입
- `POST /api/login` - 로그인
- `GET /api/projects` - 프로젝트 목록
- `POST /api/projects` - 프로젝트 생성
- `GET /api/projects/:id` - 프로젝트 조회
- `PUT /api/projects/:id` - 프로젝트 수정
- `DELETE /api/projects/:id` - 프로젝트 삭제

### 5. Content Backend 설치 및 실행

```bash
cd ../content-backend

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

서버가 http://localhost:8000 에서 실행됩니다.

#### 주요 엔드포인트

- `GET /` - API 정보
- `POST /generate/text` - AI 텍스트 생성
- `POST /generate/image` - AI 이미지 생성
- `GET /segments` - 세그먼트 목록
- `POST /segments` - 세그먼트 생성
- `GET /analytics/overview` - 분석 개요
- `GET /costs/summary` - 비용 요약
- `GET /costs/history` - 비용 내역

**API 문서**: http://localhost:8000/docs (Swagger UI)

### 6. Frontend 실행

프론트엔드는 정적 파일이므로 간단한 HTTP 서버로 실행할 수 있습니다:

```bash
cd ../frontend

# Python 내장 서버 사용
python -m http.server 5173

# 또는 Node.js http-server 사용
npx http-server -p 5173
```

브라우저에서 http://localhost:5173 접속

### 7. Vector Database 설치 및 실행 (선택사항)

ChromaDB 기반 RAG 시스템은 콘텐츠 추천에 사용됩니다:

```bash
cd content-vector

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일에서 OPENAI_API_KEY 설정
```

**환경 변수 (.env):**
```env
CHROMA_PERSIST_DIR=./chroma_data
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-ada-002
```

**Python에서 사용:**
```python
from client import get_chroma_client

# ChromaDB 클라이언트 초기화
chroma = get_chroma_client()

# 콘텐츠 추가
chroma.add_creative(
    creative_id=1,
    text="커피숍 마케팅 슬로건",
    metadata={"campaign_id": 1, "type": "text"}
)

# 유사 콘텐츠 검색
results = chroma.search_similar(
    query_text="커피 관련 광고",
    n_results=5
)
```

### 8. 전체 시스템 실행

각각의 터미널에서:

```bash
# Terminal 1: Backend
cd backend && npm start

# Terminal 2: Content Backend
cd content-backend && uvicorn main:app --reload

# Terminal 3: Frontend
cd frontend && python -m http.server 5173

# Terminal 4 (선택): Vector DB (Python 스크립트로 사용)
# ChromaDB는 content-backend와 연동되어 사용됨
```

## 📚 API 문서

### Node.js Backend

API 문서: [backend/README.md](./backend/README.md)

Swagger UI는 추가 예정입니다.

### FastAPI Content Backend

**자동 생성 API 문서**가 제공됩니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔧 개발

### 기술 스택

**Frontend**
- Vanilla JavaScript (ES6+)
- Fabric.js 5.3.0 (캔버스 에디터)
- jsPDF 2.5.1 (PDF 내보내기)
- Chart.js 4.4.0 (차트)

**Backend**
- Node.js
- Express 4.18
- PostgreSQL (pg 8.11)
- JWT 인증 (jsonwebtoken 9.0)
- bcrypt 5.1 (비밀번호 해싱)
- express-rate-limit 7.1 (Rate Limiting)

**Content Backend**
- Python 3.8+
- FastAPI
- SQLAlchemy (ORM)
- OpenAI API (GPT-3.5-turbo, DALL-E 3)
- Supabase PostgreSQL

**Vector Database (RAG System)**
- ChromaDB 0.5+ (Vector Database)
- OpenAI Embeddings (text-embedding-ada-002)
- DuckDB + Parquet (Storage Backend)
- Pydantic 2.7+ (설정 관리)

## 🎯 상세 시스템 아키텍처

### 전체 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│                         사용자 (브라우저)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   Frontend SPA   │
                    │  (Vanilla JS)    │
                    │  Port: 5173      │
                    └────────┬─────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
    ┌───────▼───────┐ ┌─────▼──────┐ ┌──────▼──────┐
    │   Backend     │ │  Content   │ │   Vector    │
    │   (Node.js)   │ │  Backend   │ │  Database   │
    │ Port: 3001    │ │  (FastAPI) │ │ (ChromaDB)  │
    └───────┬───────┘ │ Port: 8000 │ └──────┬──────┘
            │         └─────┬──────┘        │
            │               │               │
    ┌───────▼────────┐ ┌───▼────────┐ ┌───▼────────┐
    │  PostgreSQL    │ │  Supabase  │ │  OpenAI    │
    │   (artify_db)  │ │  (7 tables)│ │  Embedding │
    │ Users,Projects │ │ Campaigns  │ │    API     │
    └────────────────┘ │ Creatives  │ └────────────┘
                       │ Gen Jobs   │
                       │ Metrics    │
                       └────┬───────┘
                            │
                    ┌───────▼────────┐
                    │   OpenAI API   │
                    │  GPT-3.5-turbo │
                    │   DALL-E 3     │
                    └────────────────┘
```

### 데이터 흐름 (Data Flow)

#### 1. 사용자 인증 흐름
```
User → Frontend → Backend (JWT) → PostgreSQL
                     ↓
                 Access Token
                     ↓
                 Frontend (저장)
```

#### 2. AI 콘텐츠 생성 흐름
```
User → Frontend → Content Backend → OpenAI API
                        ↓              ↓
                   Supabase DB    (생성 결과)
                  (gen_jobs)           ↓
                        ↓         Vector DB
                   Cost Tracking  (임베딩 저장)
                        ↓              ↓
                   Frontend ←──────────┘
                  (결과 표시)
```

#### 3. 프로젝트 저장 흐름 (Auto-save)
```
Canvas Editor → EditorPage.markAsChanged()
       ↓
  5초 간격 체크
       ↓
  변경사항 감지 → EditorPage.performAutoSave()
       ↓
  Backend API → PostgreSQL (projects.data JSONB)
       ↓
  저장 완료 표시
```

#### 4. 유사 콘텐츠 추천 흐름 (RAG)
```
User Query → Content Backend → Vector DB
                ↓                 ↓
          OpenAI Embedding  → 유사도 검색
                ↓                 ↓
          Top-K 결과 ←────────────┘
                ↓
           Frontend
```

### 주요 컴포넌트 상세

#### Frontend (Vanilla JavaScript SPA)

**핵심 모듈:**
- **state.js** (상태 관리)
  - Observer 패턴 구현
  - LocalStorage 동기화
  - 전역 상태 관리

- **editor.js** (1,500+ lines)
  - Fabric.js 캔버스 제어
  - Undo/Redo (50-state 히스토리)
  - Auto-save (5초 간격)
  - Layer 관리
  - Template 시스템

- **api.js** (API 클라이언트)
  - Fetch API 래퍼
  - JWT 토큰 관리
  - 에러 핸들링

**주요 기능:**
```javascript
// Auto-save 구현
EditorPage = {
  autoSaveTimer: null,
  autoSaveInterval: 5000,
  hasUnsavedChanges: false,

  startAutoSave() {
    setInterval(() => this.performAutoSave(), 5000);
  },

  performAutoSave() {
    if (this.hasUnsavedChanges) {
      // Backend API 호출
    }
  }
}
```

#### Backend (Node.js Express)

**아키텍처:**
```
server.js
  ├── Middleware
  │   ├── CORS (Vercel 도메인 화이트리스트)
  │   ├── Rate Limiter (3 tiers)
  │   └── JWT Auth
  ├── Routes
  │   ├── /api/health
  │   ├── /api/register
  │   ├── /api/login
  │   └── /api/projects (CRUD)
  └── Database Layer (database.js)
      └── PostgreSQL Pool
```

**Rate Limiting 전략:**
1. **General**: 100 req/15분 (전체 API)
2. **Auth**: 5 req/15분 (로그인/회원가입)
3. **Projects**: 30 req/1분 (프로젝트 CRUD)

**Swagger 통합:**
- OpenAPI 3.0 스펙
- URL: http://localhost:3001/api-docs

#### Content Backend (FastAPI)

**아키텍처:**
```
main.py
  ├── CORS Middleware
  ├── Routes
  │   ├── /generate/text (GPT-3.5-turbo)
  │   ├── /generate/image (DALL-E 3)
  │   ├── /segments (CRUD)
  │   ├── /analytics/*
  │   └── /costs/* (비용 추적)
  └── Database Layer (database.py)
      ├── SQLAlchemy ORM
      └── Supabase PostgreSQL
```

**비용 추적 시스템:**
```python
# gen_jobs 테이블에 모든 AI 작업 로깅
job = GenerationJob(
  job_type="text",
  model="gpt-3.5-turbo",
  prompt_tokens=45,
  completion_tokens=32,
  estimated_cost=0.0001065  # USD
)
db.add(job)
db.commit()
```

**자동 문서화:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

#### Vector Database (ChromaDB)

**아키텍처:**
```
client.py (351 lines)
  ├── ChromaDBClient
  │   ├── Collections
  │   │   ├── copy_texts (텍스트 콘텐츠)
  │   │   ├── images (이미지 메타데이터)
  │   │   └── templates (템플릿)
  │   ├── Methods
  │   │   ├── add_creative()
  │   │   ├── search_similar()
  │   │   ├── delete_creative()
  │   │   ├── batch_add_creatives()
  │   │   └── get_collection_info()
  │   └── Embedding
  │       └── OpenAI text-embedding-ada-002
  └── Storage: DuckDB + Parquet
```

**사용 예시:**
```python
# 콘텐츠 추가 및 임베딩 생성
chroma.add_creative(
  creative_id=1,
  text="여름 세일 광고 문구",
  metadata={
    "campaign_id": 1,
    "type": "text",
    "tone": "친근한"
  }
)

# RAG 기반 유사 콘텐츠 검색
results = chroma.search_similar(
  query_text="여름 프로모션",
  n_results=5
)
# → Top 5 유사 콘텐츠 반환
```

**현재 상태:**
- ✅ 코드 완성 (351 lines)
- ✅ ChromaDB 연결 로직 구현
- ✅ OpenAI 임베딩 통합
- ⏳ Content Backend 연동 대기 중
- ⏳ RAG 기반 추천 시스템 구현 예정

### 데이터베이스 스키마

#### Backend Database (artify_db)

**users**
- id (SERIAL PRIMARY KEY)
- username (VARCHAR UNIQUE)
- email (VARCHAR UNIQUE)
- password (VARCHAR - hashed)
- created_at (TIMESTAMP)

**projects**
- id (SERIAL PRIMARY KEY)
- user_id (INTEGER FK)
- name (VARCHAR)
- data (JSONB) - 캔버스 데이터
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

#### Content Backend Database (Supabase - artify_content)

**총 7개 테이블 + 6개 인덱스**

##### 정적 데이터

**users** (사용자)
- id (INTEGER PRIMARY KEY)
- username (VARCHAR UNIQUE)
- email (VARCHAR UNIQUE)
- password_hash (VARCHAR)
- created_at (TIMESTAMP DEFAULT NOW())
- updated_at (TIMESTAMP DEFAULT NOW())

**campaigns** (캠페인)
- id (INTEGER PRIMARY KEY)
- user_id (INTEGER FK → users.id)
- name (VARCHAR NOT NULL)
- description (TEXT)
- status (VARCHAR) - 'draft', 'active', 'paused', 'completed'
- budget (FLOAT)
- start_date (TIMESTAMP)
- end_date (TIMESTAMP)
- created_at (TIMESTAMP DEFAULT NOW())
- updated_at (TIMESTAMP DEFAULT NOW())

**segments** (타겟 세그먼트)
- id (INTEGER PRIMARY KEY)
- name (VARCHAR NOT NULL)
- description (TEXT)
- criteria (TEXT) - JSON 형식 기준
- created_at (TIMESTAMP DEFAULT NOW())
- updated_at (TIMESTAMP DEFAULT NOW())

##### 동적 데이터

**creatives** (생성된 콘텐츠)
- id (INTEGER PRIMARY KEY)
- campaign_id (INTEGER FK → campaigns.id)
- content_type (VARCHAR) - 'text', 'image', 'video'
- prompt (TEXT NOT NULL)
- result (TEXT NOT NULL)
- model (VARCHAR) - 'gpt-3.5-turbo', 'dall-e-3'
- status (VARCHAR) - 'pending', 'completed', 'failed'
- created_at (TIMESTAMP DEFAULT NOW())

**gen_jobs** (AI 생성 작업 로그 - 비용 추적)
- id (INTEGER PRIMARY KEY)
- user_id (INTEGER FK → users.id)
- job_type (VARCHAR NOT NULL) - 'text', 'image'
- model (VARCHAR NOT NULL)
- prompt (TEXT NOT NULL)
- prompt_tokens (INTEGER)
- completion_tokens (INTEGER)
- total_tokens (INTEGER)
- estimated_cost (FLOAT DEFAULT 0.0) - USD
- status (VARCHAR DEFAULT 'completed') - 'pending', 'completed', 'failed'
- error_message (TEXT)
- created_at (TIMESTAMP DEFAULT NOW())
- completed_at (TIMESTAMP)

**metrics** (성과 데이터)
- id (INTEGER PRIMARY KEY)
- campaign_id (INTEGER FK → campaigns.id)
- metric_name (VARCHAR NOT NULL) - 'impressions', 'clicks', 'conversions'
- metric_value (FLOAT NOT NULL)
- timestamp (TIMESTAMP DEFAULT NOW())

**feedbacks** (피드백)
- id (INTEGER PRIMARY KEY)
- creative_id (INTEGER FK → creatives.id)
- user_id (INTEGER FK → users.id)
- rating (INTEGER) - 1-5
- comment (TEXT)
- created_at (TIMESTAMP DEFAULT NOW())

##### 인덱스 (6개)

1. `idx_campaigns_user_id` ON campaigns(user_id)
2. `idx_creatives_campaign_id` ON creatives(campaign_id)
3. `idx_gen_jobs_user_id` ON gen_jobs(user_id)
4. `idx_gen_jobs_created_at` ON gen_jobs(created_at)
5. `idx_metrics_campaign_id` ON metrics(campaign_id)
6. `idx_feedbacks_creative_id` ON feedbacks(creative_id)

## 🔐 보안

- JWT 기반 인증
- bcrypt 비밀번호 해싱 (10 rounds)
- Rate Limiting:
  - General: 100 req/15분
  - Auth: 5 req/15분
  - Project: 30 req/1분
- CORS 설정 (Vercel 도메인 화이트리스트)
- 환경변수로 민감 정보 관리

## 🧪 테스트

### Backend 헬스 체크

```bash
curl http://localhost:3001/api/health
```

### Content Backend 헬스 체크

```bash
curl http://localhost:8000/
```

### 텍스트 생성 테스트

```bash
curl -X POST http://localhost:8000/generate/text \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a marketing slogan for a coffee shop", "max_tokens": 50}'
```

## 🚢 배포

### Frontend 배포 (Vercel)

```bash
cd frontend
vercel
```

### Backend 배포 (Render/Railway)

1. PostgreSQL 데이터베이스 생성
2. 환경 변수 설정
3. Git 연결 및 자동 배포

### Content Backend 배포 (Render)

1. PostgreSQL 데이터베이스 생성
2. 환경 변수 설정 (특히 OPENAI_API_KEY)
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## 📝 주요 기능 구현 상태

### ✅ 완료된 기능

#### 1. 데이터 영속화 (PostgreSQL)
- **Backend**: PostgreSQL 완전 통합 ✅
  - Connection Pool 사용
  - users, projects 테이블 자동 생성
  - JSONB로 캔버스 데이터 저장
  - 인덱스 최적화 (user_id)
  - 인메모리 데이터 없음 (완전한 영속성)

- **Content Backend**: Supabase PostgreSQL 통합 ✅
  - SQLAlchemy ORM
  - 7개 테이블 (users, campaigns, segments, creatives, gen_jobs, metrics, feedbacks)
  - 6개 인덱스로 성능 최적화

#### 2. 캔버스 에디터 (Fabric.js 5.3.0) - **완전 구현 ✅**
- **기본 기능**
  - ✅ 선택/이동/크기조정/회전
  - ✅ 텍스트 추가 및 편집
  - ✅ 이미지 업로드 (Base64, 자동 스케일링)
  - ✅ 도형: 사각형, 원, 삼각형, 별, 다각형, 선

- **고급 기능**
  - ✅ Undo/Redo (50-state 히스토리)
  - ✅ 레이어 관리 패널 (순서 변경, 선택, 삭제)
  - ✅ 자동 저장 (5초 간격, 변경 감지)
  - ✅ 템플릿 시스템 (소셜 미디어, 배너, 포스터)
  - ✅ 텍스트 스타일링 (폰트, 크기, 굵기, 기울임, 밑줄, 정렬)
  - ✅ 속성 패널 (실시간 업데이트)

- **내보내기**
  - ✅ PNG (고해상도 2x)
  - ✅ JPG (90% 품질)
  - ✅ PDF (A4 자동 조정)
  - ✅ JSON (프로젝트 데이터)

- **AI 통합**
  - ✅ 우측 패널에 AI 생성 패널 내장
  - ✅ Content Backend와 연동
  - ✅ 생성된 콘텐츠 캔버스에 직접 추가

#### 3. AI 콘텐츠 생성
- ✅ OpenAI GPT-3.5-turbo (텍스트)
- ✅ OpenAI DALL-E 3 (이미지)
- ✅ 비용 추적 시스템 (gen_jobs 테이블)
- ✅ 토큰 카운팅 및 실시간 비용 계산

#### 4. Vector Database (ChromaDB)
- ✅ 코드 완성 (351 lines)
- ✅ 3개 컬렉션 (copy_texts, images, templates)
- ✅ OpenAI 임베딩 통합
- ⏳ Content Backend 연동 대기

#### 5. 보안 및 성능
- ✅ JWT 인증
- ✅ bcrypt 비밀번호 해싱
- ✅ Rate Limiting (3단계)
- ✅ CORS 설정
- ✅ Swagger API 문서

### 🔄 진행 중

#### Vector DB ↔ Content Backend 연동
- ChromaDB 클라이언트 준비 완료
- Content Backend에 RAG 엔드포인트 추가 필요
- 유사 콘텐츠 추천 시스템 구현 예정

### ⚠️ 개선 필요 사항 (Must-Have)

다음 7가지 핵심 개선사항은 프로덕션 환경에서 **반드시** 구현되어야 합니다:

1. **데이터베이스 마이그레이션 관리** - 스키마 버전 관리 및 롤백
2. **데이터베이스 통합 전략** - 단일 소스 오브 트루스 결정
3. **백업 및 재해 복구** - 데이터 손실 방지
4. **정적 vs 동적 데이터 분리** - Redis 캐시 계층
5. **조회 우선순위 및 TTL 전략** - 성능 최적화
6. **비용·안전장치** - Rate Limiting, 쿼터, 프롬프트 캐싱, 비동기 큐 (🚨 최우선)
7. **Vector DB 의미 기반 활용** - 브랜드 RAG, 고성과 검색, 시맨틱 디듑

---

#### 1. 데이터베이스 마이그레이션 관리

**현재 상태:**
- Backend: CREATE TABLE IF NOT EXISTS 사용 (수동)
- Content Backend: SQLAlchemy ORM 자동 생성

**개선 필요:**
- ❌ Alembic 마이그레이션 도구 미사용
- ❌ 스키마 버전 관리 없음
- ❌ 롤백 전략 없음

**권장 조치:**
```bash
# Content Backend에 Alembic 추가
cd content-backend
pip install alembic
alembic init migrations

# 첫 마이그레이션 생성
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

#### 2. 데이터베이스 통합 전략

**현재 상태:**
- Backend DB: PostgreSQL (users, projects)
- Content Backend DB: Supabase (campaigns, creatives, gen_jobs, metrics, feedbacks, segments)
- **단일 소스 오브 트루스 미확정**

**권장 전략 (2가지 옵션):**

**옵션 A: Supabase로 완전 통합 (권장)**
```
모든 데이터 → Supabase PostgreSQL
- users, projects, campaigns, creatives, segments, gen_jobs, metrics, feedbacks
- Backend와 Content Backend 모두 Supabase 연결
- 단일 데이터베이스로 조인 쿼리 가능
- 통합 백업 및 복제
```

**옵션 B: 도메인 분리 (현재 유지)**
```
Backend DB (PostgreSQL)
- users, projects (프로젝트 관리 도메인)

Content Backend DB (Supabase)
- campaigns, creatives, segments, gen_jobs, metrics, feedbacks (콘텐츠 도메인)

장점: 도메인 분리, 독립적 확장
단점: 데이터 동기화 필요, 복잡도 증가
```

#### 3. 백업 및 재해 복구 전략

**현재 상태:**
- ❌ 자동 백업 설정 없음
- ❌ 백업 복원 절차 없음
- ❌ 재해 복구 계획 없음

**권장 조치:**

**Supabase 자동 백업:**
```
1. Supabase Dashboard → Database → Backups
2. Point-in-Time Recovery (PITR) 활성화
3. 일일 자동 백업 설정
4. 백업 보관 기간: 7-30일
```

**로컬 PostgreSQL 백업:**
```bash
# 일일 백업 스크립트
pg_dump -U postgres artify_db > backup_$(date +%Y%m%d).sql

# Cron 작업으로 자동화
0 2 * * * /path/to/backup.sh
```

**백업 복원 테스트:**
```bash
# 테스트 복원 (월 1회)
psql -U postgres artify_test < backup.sql
```

#### 4. 정적 vs 동적 데이터 분리

**현재 상태:**
- 모든 데이터가 PostgreSQL/Supabase에 저장
- 캐시 계층 없음
- 정적 데이터와 동적 데이터 구분 없음

**권장 아키텍처:**

```
┌─────────────────────────────────────────────┐
│          Application Layer                   │
└───────┬─────────────────────────┬───────────┘
        │                         │
┌───────▼─────────┐     ┌────────▼──────────┐
│  정적 데이터     │     │   동적 데이터      │
│  (Redis Cache)  │     │  (PostgreSQL)     │
└─────────────────┘     └───────────────────┘
        │
┌───────▼─────────┐
│  PostgreSQL     │
│  (Source of     │
│   Truth)        │
└─────────────────┘
```

**정적 데이터 (캐시 우선):**
- 템플릿 메타데이터
- 브랜드 가이드라인
- 색상 팔레트
- 폰트 목록
- 세그먼트 기준
- 캠페인 설정

**동적 데이터 (실시간 처리):**
- 사용자 생성 콘텐츠
- AI 생성 요청/결과
- gen_jobs 로그
- 실시간 메트릭
- 사용자 피드백

**Redis 통합 예시:**
```javascript
// Backend에 Redis 추가
const redis = require('redis');
const client = redis.createClient();

// 템플릿 조회 (캐시 우선)
async function getTemplate(id) {
  // 1. Redis 캐시 확인
  const cached = await client.get(`template:${id}`);
  if (cached) return JSON.parse(cached);

  // 2. PostgreSQL에서 조회
  const template = await db.query('SELECT * FROM templates WHERE id = $1', [id]);

  // 3. Redis에 캐싱 (TTL: 1시간)
  await client.setex(`template:${id}`, 3600, JSON.stringify(template));

  return template;
}
```

**Content Backend에 Redis 추가:**
```python
# requirements.txt에 추가
redis>=5.0.0

# main.py
from redis import Redis

redis_client = Redis(host='localhost', port=6379, decode_responses=True)

@app.get("/segments")
async def get_segments(db: Session = Depends(get_db)):
    # 캐시 확인
    cached = redis_client.get("segments:all")
    if cached:
        return json.loads(cached)

    # DB 조회
    segments = db.query(Segment).all()

    # 캐싱 (5분)
    redis_client.setex("segments:all", 300, json.dumps(segments))

    return segments
```

#### 5. 조회 우선순위 및 TTL 전략

**계층별 우선순위:**
```
1. 메모리 캐시 (In-Memory) - 초 단위 TTL
2. Redis 캐시 - 분~시간 단위 TTL
3. PostgreSQL - Source of Truth
```

**TTL 가이드라인:**
```
템플릿:     24시간 (거의 변하지 않음)
세그먼트:   1시간 (가끔 업데이트)
캠페인 설정: 10분 (자주 변경 가능)
실시간 메트릭: 캐시 안 함 (항상 최신 데이터)
```

#### 6. 비용·안전장치

**현재 상태:**
- ✅ Backend: express-rate-limit (3-tier 전략)
- ✅ gen_jobs 테이블: 토큰/비용 로깅 구조 존재
- ❌ Content Backend: Rate limiting 없음
- ❌ 사용자별/캠페인별 쿼터 시스템 없음
- ❌ 프롬프트 캐싱 없음
- ❌ 비동기 작업 큐 없음 (현재 동기 처리)
- ❌ 일일/월간 비용 캡 없음

**권장 조치:**

##### 6.1. Content Backend에 Rate Limiting 추가

```python
# requirements.txt
slowapi>=0.1.9

# main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 사용자별 Rate Limiting
@app.post("/generate/text")
@limiter.limit("10/minute")  # 분당 10회
async def generate_text(request: Request, ...):
    pass

@app.post("/generate/image")
@limiter.limit("5/minute")  # 분당 5회 (비용이 높음)
async def generate_image(request: Request, ...):
    pass
```

##### 6.2. 사용자별 쿼터 시스템

**데이터베이스 스키마 추가:**
```sql
-- 사용자 쿼터 테이블
CREATE TABLE user_quotas (
  user_id INTEGER PRIMARY KEY REFERENCES users(id),
  daily_text_quota INTEGER DEFAULT 100,
  daily_image_quota INTEGER DEFAULT 20,
  monthly_cost_cap FLOAT DEFAULT 50.0,  -- USD
  daily_text_used INTEGER DEFAULT 0,
  daily_image_used INTEGER DEFAULT 0,
  monthly_cost_used FLOAT DEFAULT 0.0,
  last_daily_reset TIMESTAMP DEFAULT NOW(),
  last_monthly_reset TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_user_quotas_user_id ON user_quotas(user_id);
```

**쿼터 체크 로직:**
```python
async def check_quota(user_id: int, job_type: str, db: Session):
    quota = db.query(UserQuota).filter_by(user_id=user_id).first()

    # 일일 리셋 체크
    if (datetime.now() - quota.last_daily_reset).days >= 1:
        quota.daily_text_used = 0
        quota.daily_image_used = 0
        quota.last_daily_reset = datetime.now()

    # 월간 리셋 체크
    if (datetime.now() - quota.last_monthly_reset).days >= 30:
        quota.monthly_cost_used = 0.0
        quota.last_monthly_reset = datetime.now()

    # 쿼터 체크
    if job_type == "text":
        if quota.daily_text_used >= quota.daily_text_quota:
            raise HTTPException(429, "Daily text quota exceeded")
        quota.daily_text_used += 1

    if job_type == "image":
        if quota.daily_image_used >= quota.daily_image_quota:
            raise HTTPException(429, "Daily image quota exceeded")
        quota.daily_image_used += 1

    db.commit()
    return quota

@app.post("/generate/text")
async def generate_text(request: TextRequest, db: Session = Depends(get_db)):
    # 쿼터 체크
    quota = await check_quota(request.user_id, "text", db)

    # 월간 비용 체크
    if quota.monthly_cost_used >= quota.monthly_cost_cap:
        raise HTTPException(402, "Monthly cost cap exceeded")

    # 생성 로직...
```

##### 6.3. 프롬프트 캐싱

**해시 기반 캐싱 (동일 프롬프트):**
```python
import hashlib
from redis import Redis

redis_client = Redis(host='localhost', port=6379, decode_responses=True)

def get_prompt_hash(prompt: str, model: str) -> str:
    """프롬프트 + 모델의 해시 생성"""
    content = f"{model}:{prompt}"
    return hashlib.sha256(content.encode()).hexdigest()

@app.post("/generate/text")
async def generate_text(request: TextRequest, db: Session = Depends(get_db)):
    # 1. 해시 기반 캐시 확인
    cache_key = get_prompt_hash(request.prompt, request.model or "gpt-3.5-turbo")
    cached = redis_client.get(f"prompt:hash:{cache_key}")

    if cached:
        logger.info(f"Cache HIT (hash): {cache_key[:8]}...")
        return json.loads(cached)

    # 2. OpenAI API 호출
    response = await openai.ChatCompletion.create(...)

    # 3. 캐싱 (24시간)
    redis_client.setex(
        f"prompt:hash:{cache_key}",
        86400,  # 24 hours
        json.dumps(response)
    )

    return response
```

**시맨틱 기반 캐싱 (유사 프롬프트):**
```python
from openai import OpenAI

client = OpenAI()

async def semantic_cache_search(prompt: str, threshold: float = 0.95) -> Optional[dict]:
    """Vector DB에서 유사 프롬프트 검색"""
    # 1. 프롬프트 임베딩
    embedding_response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=prompt
    )
    query_embedding = embedding_response.data[0].embedding

    # 2. ChromaDB에서 유사도 검색
    from client import get_chroma_client
    chroma = get_chroma_client()

    results = chroma.prompt_cache_collection.query(
        query_embeddings=[query_embedding],
        n_results=1
    )

    # 3. 임계값 체크
    if results['distances'][0][0] <= (1 - threshold):  # 코사인 유사도 95% 이상
        cached_result = results['metadatas'][0][0]['result']
        logger.info(f"Cache HIT (semantic): similarity={1-results['distances'][0][0]:.3f}")
        return json.loads(cached_result)

    return None

@app.post("/generate/text")
async def generate_text(request: TextRequest, db: Session = Depends(get_db)):
    # 1. 해시 캐시 체크
    # ... (위와 동일)

    # 2. 시맨틱 캐시 체크
    semantic_result = await semantic_cache_search(request.prompt, threshold=0.95)
    if semantic_result:
        return semantic_result

    # 3. OpenAI API 호출
    response = await openai.ChatCompletion.create(...)

    # 4. 시맨틱 캐시에 저장
    embedding_response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=request.prompt
    )

    chroma.prompt_cache_collection.add(
        embeddings=[embedding_response.data[0].embedding],
        documents=[request.prompt],
        metadatas=[{
            "result": json.dumps(response),
            "model": request.model,
            "timestamp": datetime.now().isoformat()
        }],
        ids=[cache_key]
    )

    return response
```

##### 6.4. 비동기 작업 큐

**Celery + Redis 통합:**
```python
# requirements.txt
celery>=5.3.0
redis>=5.0.0

# celery_app.py
from celery import Celery

celery_app = Celery(
    'artify',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_time_limit=300,  # 5분 타임아웃
    task_soft_time_limit=240,  # 4분 경고
)

@celery_app.task(bind=True, max_retries=3)
def generate_image_task(self, job_id: int, prompt: str, model: str, user_id: int):
    """비동기 이미지 생성 작업"""
    try:
        # 작업 상태 업데이트
        update_job_status(job_id, "processing")

        # OpenAI DALL-E 호출
        response = openai.Image.create(
            model=model,
            prompt=prompt,
            n=1,
            size="1024x1024"
        )

        # 결과 저장
        image_url = response.data[0].url
        update_job_result(job_id, image_url, "completed")

        return {"status": "completed", "image_url": image_url}

    except SoftTimeLimitExceeded:
        # 소프트 타임아웃 (재시도)
        update_job_status(job_id, "timeout_retry")
        raise self.retry(countdown=60)  # 1분 후 재시도

    except Exception as exc:
        # 에러 처리
        update_job_status(job_id, "failed", error=str(exc))
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        return {"status": "failed", "error": str(exc)}

# main.py
@app.post("/generate/image/async")
async def generate_image_async(request: ImageRequest, db: Session = Depends(get_db)):
    # 1. 쿼터 체크
    await check_quota(request.user_id, "image", db)

    # 2. gen_jobs 생성
    job = GenerationJob(
        user_id=request.user_id,
        job_type="image",
        model=request.model or "dall-e-3",
        prompt=request.prompt,
        status="pending"
    )
    db.add(job)
    db.commit()

    # 3. Celery 작업 큐에 추가
    task = generate_image_task.apply_async(
        args=[job.id, request.prompt, request.model, request.user_id],
        task_id=f"img_{job.id}"
    )

    return {
        "job_id": job.id,
        "task_id": task.id,
        "status": "pending",
        "poll_url": f"/jobs/{job.id}/status"
    }
```

**작업 상태 폴링 엔드포인트:**
```python
@app.get("/jobs/{job_id}/status")
async def get_job_status(job_id: int, db: Session = Depends(get_db)):
    job = db.query(GenerationJob).filter_by(id=job_id).first()

    if not job:
        raise HTTPException(404, "Job not found")

    return {
        "job_id": job.id,
        "status": job.status,  # pending, processing, completed, failed, cancelled
        "result": job.result if job.status == "completed" else None,
        "error": job.error_message if job.status == "failed" else None,
        "created_at": job.created_at,
        "completed_at": job.completed_at
    }

@app.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: int, db: Session = Depends(get_db)):
    """작업 취소"""
    job = db.query(GenerationJob).filter_by(id=job_id).first()

    if not job:
        raise HTTPException(404, "Job not found")

    if job.status in ["completed", "failed", "cancelled"]:
        raise HTTPException(400, f"Cannot cancel job with status: {job.status}")

    # Celery 작업 취소
    celery_app.control.revoke(f"img_{job.id}", terminate=True)

    # DB 업데이트
    job.status = "cancelled"
    job.completed_at = datetime.now()
    db.commit()

    return {"job_id": job.id, "status": "cancelled"}
```

##### 6.5. 비용 로깅 및 일일 캡

**비용 계산 및 로깅:**
```python
PRICING = {
    "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},  # per 1K tokens
    "gpt-4": {"input": 0.03, "output": 0.06},
    "dall-e-3": {"1024x1024": 0.040, "1024x1792": 0.080, "1792x1024": 0.080}
}

def calculate_text_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """텍스트 생성 비용 계산"""
    pricing = PRICING.get(model, PRICING["gpt-3.5-turbo"])
    cost = (prompt_tokens / 1000 * pricing["input"]) + \
           (completion_tokens / 1000 * pricing["output"])
    return round(cost, 6)

def calculate_image_cost(model: str, size: str = "1024x1024") -> float:
    """이미지 생성 비용 계산"""
    return PRICING.get(model, {}).get(size, 0.040)

@app.post("/generate/text")
async def generate_text(request: TextRequest, db: Session = Depends(get_db)):
    # OpenAI API 호출
    response = await openai.ChatCompletion.create(...)

    # 비용 계산
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens
    cost = calculate_text_cost(request.model, prompt_tokens, completion_tokens)

    # gen_jobs에 로깅
    job = GenerationJob(
        user_id=request.user_id,
        job_type="text",
        model=request.model,
        prompt=request.prompt,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        estimated_cost=cost,
        status="completed"
    )
    db.add(job)

    # 사용자 쿼터 업데이트
    quota = db.query(UserQuota).filter_by(user_id=request.user_id).first()
    quota.monthly_cost_used += cost

    db.commit()

    # 월간 캡 체크 (다음 요청에서 차단)
    if quota.monthly_cost_used >= quota.monthly_cost_cap:
        logger.warning(f"User {request.user_id} reached monthly cap: ${quota.monthly_cost_used:.2f}")

    return {
        "result": response.choices[0].message.content,
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "estimated_cost_usd": cost
        },
        "quota": {
            "monthly_used": quota.monthly_cost_used,
            "monthly_cap": quota.monthly_cost_cap,
            "remaining": quota.monthly_cost_cap - quota.monthly_cost_used
        }
    }
```

**비용 대시보드 엔드포인트:**
```python
@app.get("/users/{user_id}/costs/daily")
async def get_daily_costs(user_id: int, db: Session = Depends(get_db)):
    """일일 비용 통계"""
    today = datetime.now().date()

    costs = db.query(
        func.sum(GenerationJob.estimated_cost).label('total_cost'),
        func.count(GenerationJob.id).label('job_count'),
        GenerationJob.job_type
    ).filter(
        GenerationJob.user_id == user_id,
        func.date(GenerationJob.created_at) == today
    ).group_by(GenerationJob.job_type).all()

    return {
        "date": today.isoformat(),
        "breakdown": [
            {"type": c.job_type, "cost": float(c.total_cost or 0), "count": c.job_count}
            for c in costs
        ],
        "total": sum(float(c.total_cost or 0) for c in costs)
    }

@app.get("/users/{user_id}/costs/monthly")
async def get_monthly_costs(user_id: int, db: Session = Depends(get_db)):
    """월간 비용 통계"""
    # 지난 30일
    start_date = datetime.now() - timedelta(days=30)

    daily_costs = db.query(
        func.date(GenerationJob.created_at).label('date'),
        func.sum(GenerationJob.estimated_cost).label('cost')
    ).filter(
        GenerationJob.user_id == user_id,
        GenerationJob.created_at >= start_date
    ).group_by(func.date(GenerationJob.created_at)).all()

    quota = db.query(UserQuota).filter_by(user_id=user_id).first()

    return {
        "period": {"start": start_date.date().isoformat(), "end": datetime.now().date().isoformat()},
        "daily": [{"date": str(d.date), "cost": float(d.cost)} for d in daily_costs],
        "total": quota.monthly_cost_used,
        "cap": quota.monthly_cost_cap,
        "remaining": quota.monthly_cost_cap - quota.monthly_cost_used
    }
```

#### 7. Vector DB의 의미 기반 활용

**현재 상태:**
- ✅ ChromaDB 클라이언트 완성 (351 lines)
- ✅ 3개 컬렉션 정의 (copy_texts, images, templates)
- ❌ 구체적 유즈케이스 미정의
- ❌ Content Backend 연동 없음
- ❌ RAG 활용 전략 부재

**권장 유즈케이스:**

##### 7.1. 유즈케이스 A: 브랜드 보이스/가이드라인 RAG

**목적:** AI 생성 시 브랜드 가이드라인을 컨텍스트로 주입하여 일관된 톤앤매너 유지

**구현:**

```python
# content-vector/client.py에 추가
def add_brand_guideline(self, brand_id: int, guideline_text: str, metadata: dict):
    """브랜드 가이드라인 저장"""
    self.brand_guidelines_collection.add(
        documents=[guideline_text],
        metadatas=[{
            "brand_id": brand_id,
            "category": metadata.get("category", "general"),  # tone, style, values, etc.
            "created_at": datetime.now().isoformat(),
            **metadata
        }],
        ids=[f"brand_{brand_id}_{metadata.get('category', 'general')}"]
    )

def get_brand_context(self, brand_id: int, query: str, n_results: int = 3) -> str:
    """브랜드 관련 가이드라인 검색 및 컨텍스트 생성"""
    results = self.brand_guidelines_collection.query(
        query_texts=[query],
        where={"brand_id": brand_id},
        n_results=n_results
    )

    if not results['documents'][0]:
        return ""

    # 검색된 가이드라인을 컨텍스트로 조합
    context = "\n\n".join([
        f"[{results['metadatas'][0][i]['category']}]\n{doc}"
        for i, doc in enumerate(results['documents'][0])
    ])

    return context

# content-backend/main.py에서 활용
from content_vector.client import get_chroma_client

@app.post("/generate/text/with-brand")
async def generate_text_with_brand(request: BrandTextRequest, db: Session = Depends(get_db)):
    """브랜드 가이드라인 기반 텍스트 생성"""

    # 1. Vector DB에서 관련 브랜드 가이드라인 검색
    chroma = get_chroma_client()
    brand_context = chroma.get_brand_context(
        brand_id=request.brand_id,
        query=request.prompt,
        n_results=3
    )

    # 2. 프롬프트에 컨텍스트 주입
    enhanced_prompt = f"""다음 브랜드 가이드라인을 반드시 준수하여 작성하세요:

{brand_context}

---

사용자 요청: {request.prompt}

위 가이드라인의 톤앤매너, 스타일, 가치관을 반영하여 응답하세요."""

    # 3. OpenAI API 호출
    response = await openai.ChatCompletion.create(
        model=request.model or "gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "당신은 브랜드 가이드라인을 정확히 따르는 마케팅 카피라이터입니다."},
            {"role": "user", "content": enhanced_prompt}
        ],
        temperature=0.7
    )

    return {
        "result": response.choices[0].message.content,
        "brand_context_used": brand_context,
        "usage": response.usage
    }
```

**예시:**
```python
# 브랜드 가이드라인 등록
chroma.add_brand_guideline(
    brand_id=1,
    guideline_text="우리 브랜드는 친근하고 유머러스한 톤을 사용합니다. '~해요' 체를 사용하며, 이모지를 적절히 활용합니다.",
    metadata={"category": "tone"}
)

chroma.add_brand_guideline(
    brand_id=1,
    guideline_text="환경 보호와 지속가능성을 핵심 가치로 삼습니다. 모든 메시지에 이를 반영해야 합니다.",
    metadata={"category": "values"}
)

# 생성 시 자동 적용
# "여름 세일 광고" → 가이드라인 검색 → 친근한 톤 + 환경 메시지 반영
```

##### 7.2. 유즈케이스 B: 고성과 크리에이티브 유사 검색

**목적:** 과거 성과가 좋았던 콘텐츠와 유사한 크리에이티브를 검색하여 재활용/추천

**구현:**

```python
# content-vector/client.py
def add_creative_with_performance(self, creative_id: int, text: str, metadata: dict):
    """성과 데이터 포함 크리에이티브 저장"""
    self.copy_texts_collection.add(
        documents=[text],
        metadatas=[{
            "creative_id": creative_id,
            "campaign_id": metadata.get("campaign_id"),
            "performance_score": metadata.get("performance_score", 0),  # CTR, conversion 등
            "impressions": metadata.get("impressions", 0),
            "clicks": metadata.get("clicks", 0),
            "conversions": metadata.get("conversions", 0),
            "created_at": datetime.now().isoformat(),
        }],
        ids=[f"creative_{creative_id}"]
    )

def search_high_performing_similar(self, query_text: str, min_score: float = 0.05, n_results: int = 5):
    """고성과 유사 크리에이티브 검색"""
    results = self.copy_texts_collection.query(
        query_texts=[query_text],
        where={"performance_score": {"$gte": min_score}},  # 최소 성과 점수 필터
        n_results=n_results
    )

    return [
        {
            "creative_id": results['metadatas'][0][i]['creative_id'],
            "text": results['documents'][0][i],
            "similarity": 1 - results['distances'][0][i],  # 코사인 유사도
            "performance_score": results['metadatas'][0][i]['performance_score'],
            "metrics": {
                "impressions": results['metadatas'][0][i]['impressions'],
                "clicks": results['metadatas'][0][i]['clicks'],
                "conversions": results['metadatas'][0][i]['conversions'],
            }
        }
        for i in range(len(results['documents'][0]))
    ]

# content-backend/main.py
@app.get("/creatives/recommend")
async def recommend_similar_creatives(
    query: str,
    min_performance: float = 0.05,
    n_results: int = 5,
    db: Session = Depends(get_db)
):
    """유사한 고성과 크리에이티브 추천"""

    chroma = get_chroma_client()
    recommendations = chroma.search_high_performing_similar(
        query_text=query,
        min_score=min_performance,
        n_results=n_results
    )

    return {
        "query": query,
        "recommendations": recommendations,
        "count": len(recommendations)
    }
```

**자동 성과 업데이트:**
```python
@app.post("/creatives/{creative_id}/update-performance")
async def update_creative_performance(creative_id: int, db: Session = Depends(get_db)):
    """메트릭 기반 성과 점수 업데이트"""

    # 1. DB에서 메트릭 조회
    creative = db.query(Creative).filter_by(id=creative_id).first()
    metrics = db.query(Metric).filter_by(campaign_id=creative.campaign_id).all()

    # 2. 성과 점수 계산 (CTR, conversion rate 등)
    impressions = sum(m.metric_value for m in metrics if m.metric_name == "impressions")
    clicks = sum(m.metric_value for m in metrics if m.metric_name == "clicks")
    conversions = sum(m.metric_value for m in metrics if m.metric_name == "conversions")

    ctr = clicks / impressions if impressions > 0 else 0
    cvr = conversions / clicks if clicks > 0 else 0
    performance_score = (ctr * 0.5) + (cvr * 0.5)  # 가중치 적용

    # 3. Vector DB 업데이트
    chroma = get_chroma_client()
    chroma.copy_texts_collection.update(
        ids=[f"creative_{creative_id}"],
        metadatas=[{
            "performance_score": performance_score,
            "impressions": int(impressions),
            "clicks": int(clicks),
            "conversions": int(conversions),
            "last_updated": datetime.now().isoformat()
        }]
    )

    return {
        "creative_id": creative_id,
        "performance_score": performance_score,
        "metrics": {"impressions": impressions, "clicks": clicks, "conversions": conversions}
    }
```

##### 7.3. 유즈케이스 C: 프롬프트 시맨틱 디듑 (비용 절감)

**목적:** 의미상 중복된 프롬프트를 감지하여 캐시된 결과 재사용, API 호출 비용 절감

**구현 (섹션 6.3과 연계):**

```python
# content-vector/client.py
def add_prompt_cache(self, prompt: str, model: str, result: dict, cost: float):
    """프롬프트 캐시에 저장 (임베딩 자동 생성)"""
    self.prompt_cache_collection.add(
        documents=[prompt],
        metadatas=[{
            "model": model,
            "result": json.dumps(result),
            "cost_saved": cost,
            "hit_count": 0,
            "created_at": datetime.now().isoformat()
        }],
        ids=[hashlib.sha256(f"{model}:{prompt}".encode()).hexdigest()]
    )

def search_semantic_cache(self, prompt: str, model: str, threshold: float = 0.95):
    """시맨틱 유사도 기반 캐시 검색"""
    results = self.prompt_cache_collection.query(
        query_texts=[prompt],
        where={"model": model},
        n_results=1
    )

    if not results['documents'][0]:
        return None

    similarity = 1 - results['distances'][0][0]

    # 임계값 체크
    if similarity >= threshold:
        # 히트 카운트 증가
        cache_id = results['ids'][0][0]
        metadata = results['metadatas'][0][0]
        metadata['hit_count'] += 1

        self.prompt_cache_collection.update(
            ids=[cache_id],
            metadatas=[metadata]
        )

        return {
            "result": json.loads(metadata['result']),
            "similarity": similarity,
            "cost_saved": metadata['cost_saved'],
            "hit_count": metadata['hit_count']
        }

    return None

# content-backend/main.py (섹션 6.3 통합)
@app.post("/generate/text")
async def generate_text(request: TextRequest, db: Session = Depends(get_db)):
    chroma = get_chroma_client()

    # 1. 시맨틱 캐시 체크 (95% 유사도)
    cached = chroma.search_semantic_cache(
        prompt=request.prompt,
        model=request.model or "gpt-3.5-turbo",
        threshold=0.95
    )

    if cached:
        logger.info(f"Semantic cache HIT: {cached['similarity']:.2%} similar, saved ${cached['cost_saved']:.4f}")
        return {
            "result": cached['result'],
            "cached": True,
            "similarity": cached['similarity'],
            "cost_saved_usd": cached['cost_saved']
        }

    # 2. OpenAI API 호출
    response = await openai.ChatCompletion.create(...)
    cost = calculate_text_cost(...)

    # 3. 시맨틱 캐시에 저장
    chroma.add_prompt_cache(
        prompt=request.prompt,
        model=request.model,
        result=response.choices[0].message,
        cost=cost
    )

    return {"result": response, "cached": False, "cost_usd": cost}
```

**비용 절감 대시보드:**
```python
@app.get("/analytics/cache-savings")
async def get_cache_savings(user_id: int, db: Session = Depends(get_db)):
    """캐시로 절감한 비용 통계"""

    # 1. 해시 캐시 히트
    hash_cache_hits = redis_client.get(f"user:{user_id}:cache:hash:hits") or 0

    # 2. 시맨틱 캐시 히트
    chroma = get_chroma_client()
    semantic_results = chroma.prompt_cache_collection.get(
        where={"hit_count": {"$gt": 0}}
    )

    total_semantic_hits = sum(m['hit_count'] for m in semantic_results['metadatas'])
    total_saved = sum(m['cost_saved'] * m['hit_count'] for m in semantic_results['metadatas'])

    return {
        "cache_stats": {
            "hash_hits": int(hash_cache_hits),
            "semantic_hits": total_semantic_hits,
            "total_hits": int(hash_cache_hits) + total_semantic_hits
        },
        "cost_savings": {
            "total_saved_usd": round(total_saved, 4),
            "average_per_hit": round(total_saved / total_semantic_hits, 6) if total_semantic_hits > 0 else 0
        }
    }
```

**전략 요약:**

| 유즈케이스 | Vector DB 역할 | RDB 역할 | 효과 |
|-----------|---------------|----------|------|
| A. 브랜드 RAG | 가이드라인 임베딩 저장 및 검색 | 브랜드 메타데이터 (ID, 이름) | 일관된 브랜드 보이스 |
| B. 고성과 검색 | 크리에이티브 텍스트 임베딩 | 성과 메트릭 (CTR, CVR) | 데이터 기반 재활용 |
| C. 시맨틱 디듑 | 프롬프트 임베딩 및 유사도 검색 | 비용 로그 (gen_jobs) | 30-50% 비용 절감 |

## 🐛 알려진 이슈

### 중요도: 매우 높음 (비용/안정성)
- **Content Backend Rate Limiting 부재**: API 남용 및 비용 폭탄 위험
- **사용자별 쿼터 시스템 없음**: 무제한 AI 생성 가능 (비용 통제 불가)
- **비동기 작업 큐 없음**: 이미지 생성 시 동기 처리로 타임아웃 위험
- **일일/월간 비용 캡 없음**: 사용자당 지출 한도 미설정

### 중요도: 높음 (운영 안정성)
- **Alembic 마이그레이션 부재**: 스키마 변경 추적 불가, 롤백 불가
- **백업 전략 미구축**: 데이터 손실 위험, 재해 복구 불가
- **프롬프트 캐싱 없음**: 동일/유사 요청 중복 비용 발생 (30-50% 절감 기회 상실)
- **Vector DB 유즈케이스 미구현**: ChromaDB 클라이언트는 완성됐으나 실제 활용 전략 부재

### 중요도: 중간 (기능 개선)
- **캐시 계층 없음**: 정적 데이터(템플릿, 세그먼트) 매번 DB 조회
- **데이터베이스 통합 미결정**: Backend DB와 Content Backend DB 분리 운영 (조인 불가)
- **비용 대시보드 부재**: 사용자별 일일/월간 비용 추적 UI 없음

## 🚀 향후 로드맵

### Phase 1: 비용·안전장치 구축 (우선순위: 매우 높음) 🚨
**타임라인**: 1-2주

1. **Content Backend Rate Limiting** (slowapi 통합)
   - 텍스트 생성: 10 req/min
   - 이미지 생성: 5 req/min
   - IP/사용자별 제한

2. **사용자별 쿼터 시스템**
   - user_quotas 테이블 생성
   - 일일: 텍스트 100회, 이미지 20회
   - 월간: $50 USD 캡
   - 자동 리셋 로직

3. **프롬프트 캐싱 (2-tier)**
   - Redis 해시 캐싱 (동일 프롬프트)
   - ChromaDB 시맨틱 캐싱 (95% 유사도)
   - 예상 비용 절감: 30-50%

4. **비동기 작업 큐 (Celery + Redis)**
   - 이미지 생성 비동기 처리
   - 작업 상태 폴링 엔드포인트
   - 타임아웃/재시도/취소 지원

5. **비용 로깅 및 대시보드**
   - gen_jobs 비용 계산 로직
   - 일일/월간 비용 통계 API
   - Frontend 비용 대시보드 UI

### Phase 2: Vector DB 의미 기반 활용 (우선순위: 높음)
**타임라인**: 2-3주

1. **유즈케이스 A: 브랜드 보이스 RAG**
   - brand_guidelines_collection 추가
   - /generate/text/with-brand 엔드포인트
   - 가이드라인 관리 UI

2. **유즈케이스 B: 고성과 크리에이티브 검색**
   - 성과 데이터 Vector DB 동기화
   - /creatives/recommend 엔드포인트
   - 자동 성과 점수 업데이트 (CTR, CVR)

3. **유즈케이스 C: 시맨틱 디듑 비용 절감**
   - prompt_cache_collection 통합
   - 캐시 히트율 모니터링
   - 절감 비용 대시보드

### Phase 3: 데이터 아키텍처 개선 (우선순위: 중간)
**타임라인**: 3-4주

1. **Alembic 마이그레이션 도구 도입**
   - Content Backend Alembic 초기화
   - 첫 마이그레이션 생성
   - 롤백 절차 수립

2. **자동 백업 설정**
   - Supabase PITR 활성화 (7일 보관)
   - 로컬 PostgreSQL 일일 백업 cron
   - 월 1회 복원 테스트

3. **Redis 캐시 계층 추가**
   - 템플릿: 24시간 TTL
   - 세그먼트: 1시간 TTL
   - 캠페인 설정: 10분 TTL

4. **데이터베이스 통합 전략 결정**
   - 옵션 A: Supabase 완전 통합 (권장)
   - 옵션 B: 도메인 분리 유지
   - 마이그레이션 계획 수립

### Phase 4: 성능 최적화 (우선순위: 낮음)
**타임라인**: 4-6주

1. CDN 통합 (Cloudflare/Cloudinary)
2. 데이터베이스 쿼리 최적화
3. 연결 풀 튜닝
4. 프론트엔드 번들 최적화
5. 이미지 레이지 로딩

---

**권장 우선순위:**
1. ⚡ **Phase 1 (비용·안전장치)** - 즉시 시작 (비용 폭탄 방지)
2. 🎯 **Phase 2 (Vector DB 활용)** - 2주 후 시작 (핵심 차별화 기능)
3. 🔧 **Phase 3 (아키텍처 개선)** - 병렬 진행 가능
4. 🚀 **Phase 4 (성능 최적화)** - 트래픽 증가 시 진행

## 📄 라이선스

MIT License

## 👥 기여

기여는 언제나 환영합니다! Pull Request를 보내주세요.

## 📧 문의

프로젝트 관련 문의사항이 있으시면 Issue를 등록해주세요.

---

**Made with ❤️ by Artify Team**
