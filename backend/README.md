# Artify Backend

Node.js Express + PostgreSQL 기반 인증 및 프로젝트 관리 API

## 🚀 시작하기

### 필수 요구사항

- Node.js 16+
- PostgreSQL 12+
- npm 또는 yarn

### 설치

```bash
npm install
```

### 환경 변수 설정

`.env` 파일 생성:

```env
PORT=3001
NODE_ENV=development
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
DATABASE_URL=postgresql://username:password@localhost:5432/artify_db
```

### 데이터베이스 초기화

```bash
# PostgreSQL 접속
psql -U postgres

# 데이터베이스 생성
CREATE DATABASE artify_db;
```

서버가 시작될 때 자동으로 테이블이 생성됩니다.

### 실행

```bash
npm start
```

서버가 http://localhost:3001 에서 실행됩니다.

## 📚 API 문서

### Swagger UI

자동 생성된 대화형 API 문서가 제공됩니다:

**Swagger UI**: http://localhost:3001/api-docs

### Base URL

```
http://localhost:3001/api
```

### 인증

JWT(JSON Web Token) 기반 인증을 사용합니다.

로그인 성공 시 토큰을 받아서 모든 보호된 엔드포인트에 포함시켜야 합니다:

```
Authorization: Bearer <token>
```

---

## 🔓 공개 엔드포인트

### 1. 헬스 체크

서버 상태를 확인합니다.

**요청**
```
GET /api/health
```

**응답 (200 OK)**
```json
{
  "status": "healthy",
  "service": "artify-backend",
  "version": "2.0.0",
  "timestamp": "2024-11-07T07:30:00.000Z",
  "cors": {
    "enabled": true,
    "allowedOrigins": [
      "https://artify-ruddy.vercel.app",
      "*.vercel.app",
      "localhost"
    ]
  },
  "database": {
    "type": "PostgreSQL",
    "connected": true,
    "users": 10,
    "projects": 25
  }
}
```

### 2. 회원가입

새 사용자를 등록합니다.

**Rate Limit**: 5 requests / 15분

**요청**
```
POST /api/register
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securePassword123"
}
```

**응답 (201 Created)**
```json
{
  "message": "User registered successfully",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com"
  }
}
```

**에러 응답**

- `400 Bad Request`: 필수 필드 누락
  ```json
  { "error": "All fields are required" }
  ```

- `400 Bad Request`: 이메일 중복
  ```json
  { "error": "Email already exists" }
  ```

- `400 Bad Request`: 사용자명 중복
  ```json
  { "error": "Username already exists" }
  ```

### 3. 로그인

기존 사용자로 로그인합니다.

**Rate Limit**: 5 requests / 15분

**요청**
```
POST /api/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "securePassword123"
}
```

**응답 (200 OK)**
```json
{
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com"
  }
}
```

**에러 응답**

- `400 Bad Request`: 필수 필드 누락
  ```json
  { "error": "Email and password are required" }
  ```

- `401 Unauthorized`: 잘못된 인증 정보
  ```json
  { "error": "Invalid credentials" }
  ```

---

## 🔐 보호된 엔드포인트

모든 보호된 엔드포인트는 Authorization 헤더가 필요합니다:

```
Authorization: Bearer <your_jwt_token>
```

**Rate Limit**: 30 requests / 1분

### 4. 프로젝트 목록 조회

현재 사용자의 모든 프로젝트를 조회합니다.

**요청**
```
GET /api/projects
Authorization: Bearer <token>
```

**응답 (200 OK)**
```json
{
  "projects": [
    {
      "id": 1,
      "name": "여름 세일 캠페인",
      "created_at": "2024-11-01T10:00:00.000Z",
      "updated_at": "2024-11-07T15:30:00.000Z"
    },
    {
      "id": 2,
      "name": "신제품 런칭",
      "created_at": "2024-11-05T14:20:00.000Z",
      "updated_at": "2024-11-06T09:15:00.000Z"
    }
  ]
}
```

### 5. 프로젝트 생성

새 프로젝트를 생성합니다.

**요청**
```
POST /api/projects
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "신규 캠페인",
  "data": {
    "canvas": {
      "objects": [],
      "background": "#ffffff"
    },
    "settings": {
      "width": 800,
      "height": 600
    }
  }
}
```

**응답 (201 Created)**
```json
{
  "message": "Project created successfully",
  "project": {
    "id": 3,
    "name": "신규 캠페인",
    "created_at": "2024-11-07T16:00:00.000Z",
    "updated_at": "2024-11-07T16:00:00.000Z"
  }
}
```

**에러 응답**

- `400 Bad Request`: 프로젝트명 누락
  ```json
  { "error": "Project name is required" }
  ```

### 6. 프로젝트 조회

특정 프로젝트의 상세 정보를 조회합니다.

**요청**
```
GET /api/projects/:id
Authorization: Bearer <token>
```

**응답 (200 OK)**
```json
{
  "id": 1,
  "name": "여름 세일 캠페인",
  "data": {
    "canvas": {
      "objects": [
        {
          "type": "text",
          "text": "SUMMER SALE",
          "left": 100,
          "top": 100
        }
      ],
      "background": "#ffffff"
    },
    "settings": {
      "width": 800,
      "height": 600
    }
  },
  "createdAt": "2024-11-01T10:00:00.000Z",
  "updatedAt": "2024-11-07T15:30:00.000Z"
}
```

**에러 응답**

- `404 Not Found`: 프로젝트 없음
  ```json
  { "error": "Project not found" }
  ```

- `403 Forbidden`: 권한 없음
  ```json
  { "error": "Access denied" }
  ```

### 7. 프로젝트 수정

프로젝트를 업데이트합니다.

**요청**
```
PUT /api/projects/:id
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "여름 세일 캠페인 (수정)",
  "data": {
    "canvas": {
      "objects": [
        {
          "type": "text",
          "text": "BIG SUMMER SALE",
          "left": 100,
          "top": 100,
          "fontSize": 48
        }
      ]
    }
  }
}
```

**응답 (200 OK)**
```json
{
  "message": "Project updated successfully",
  "project": {
    "id": 1,
    "name": "여름 세일 캠페인 (수정)",
    "updatedAt": "2024-11-07T16:30:00.000Z"
  }
}
```

**에러 응답**

- `404 Not Found`: 프로젝트 없음
- `403 Forbidden`: 권한 없음

### 8. 프로젝트 삭제

프로젝트를 삭제합니다.

**요청**
```
DELETE /api/projects/:id
Authorization: Bearer <token>
```

**응답 (200 OK)**
```json
{
  "message": "Project deleted successfully"
}
```

**에러 응답**

- `404 Not Found`: 프로젝트 없음
- `403 Forbidden`: 권한 없음

---

## 🛡️ Rate Limiting

API 남용을 방지하기 위해 Rate Limiting이 적용됩니다:

### 일반 API
- **제한**: 100 requests / 15분
- **적용**: `/api/*` 모든 엔드포인트
- **응답**: 429 Too Many Requests
  ```json
  { "message": "Too many requests from this IP, please try again later." }
  ```

### 인증 API
- **제한**: 5 requests / 15분
- **적용**: `/api/register`, `/api/login`
- **응답**: 429 Too Many Requests
  ```json
  { "message": "Too many authentication attempts, please try again later." }
  ```

### 프로젝트 API
- **제한**: 30 requests / 1분
- **적용**: `/api/projects/*`
- **응답**: 429 Too Many Requests
  ```json
  { "message": "Too many project operations, please slow down." }
  ```

---

## 🔒 보안

### JWT 토큰

- **알고리즘**: HS256
- **만료 시간**: 7일
- **페이로드**:
  ```json
  {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "iat": 1699363200,
    "exp": 1699968000
  }
  ```

### 비밀번호

- **해싱**: bcrypt
- **Rounds**: 10
- 원본 비밀번호는 저장되지 않습니다

### CORS

다음 도메인에서의 요청만 허용됩니다:

- `https://artify-ruddy.vercel.app`
- `*.vercel.app` (모든 Vercel 배포)
- `http://localhost:3000`
- `http://localhost:5173`
- `http://127.0.0.1:5173`
- `http://localhost:5500`

---

## 🗃️ 데이터베이스 스키마

### users 테이블

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | SERIAL | PRIMARY KEY | 사용자 ID |
| username | VARCHAR(255) | UNIQUE, NOT NULL | 사용자명 |
| email | VARCHAR(255) | UNIQUE, NOT NULL | 이메일 |
| password | VARCHAR(255) | NOT NULL | 해시된 비밀번호 |
| created_at | TIMESTAMP | DEFAULT NOW() | 생성일시 |

### projects 테이블

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | SERIAL | PRIMARY KEY | 프로젝트 ID |
| user_id | INTEGER | FK(users.id), NOT NULL | 소유자 ID |
| name | VARCHAR(255) | NOT NULL | 프로젝트명 |
| data | JSONB | DEFAULT '{}' | 캔버스 데이터 |
| created_at | TIMESTAMP | DEFAULT NOW() | 생성일시 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 수정일시 |

**인덱스**:
- `user_id` (projects 조회 최적화)
- `ON DELETE CASCADE` (사용자 삭제 시 프로젝트 자동 삭제)

---

## 🧪 테스트

### cURL 예제

#### 회원가입
```bash
curl -X POST http://localhost:3001/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

#### 로그인
```bash
curl -X POST http://localhost:3001/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

#### 프로젝트 조회 (인증 필요)
```bash
curl http://localhost:3001/api/projects \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

#### 프로젝트 생성
```bash
curl -X POST http://localhost:3001/api/projects \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Project",
    "data": {
      "canvas": { "objects": [] }
    }
  }'
```

---

## 📦 의존성

```json
{
  "express": "^4.18.2",        // 웹 프레임워크
  "cors": "^2.8.5",            // CORS 미들웨어
  "jsonwebtoken": "^9.0.2",   // JWT 인증
  "bcrypt": "^5.1.1",          // 비밀번호 해싱
  "dotenv": "^16.0.3",         // 환경변수 관리
  "pg": "^8.11.3",             // PostgreSQL 클라이언트
  "express-rate-limit": "^7.1.5"  // Rate Limiting
}
```

---

## 🚀 배포

### Render

1. Render 대시보드에서 "New PostgreSQL" 생성
2. "New Web Service" 생성
3. GitHub 저장소 연결
4. 환경 변수 설정:
   - `DATABASE_URL` (Render PostgreSQL URL 복사)
   - `JWT_SECRET` (강력한 랜덤 문자열)
   - `NODE_ENV=production`
5. Build Command: `npm install`
6. Start Command: `npm start`

### Railway

1. Railway 프로젝트 생성
2. PostgreSQL 플러그인 추가
3. GitHub 저장소 연결
4. 환경 변수는 자동으로 설정됨
5. 배포

---

## 🐛 트러블슈팅

### DATABASE_URL 오류

```
❌ DATABASE_URL is not set in environment variables
```

**해결**: `.env` 파일에 `DATABASE_URL` 설정 확인

### JWT 토큰 만료

```
{ "error": "Invalid token" }
```

**해결**: 다시 로그인하여 새 토큰 발급

### CORS 오류

```
Not allowed by CORS
```

**해결**: `server.js`의 `corsOptions.origin` 배열에 도메인 추가

---

## 📞 지원

이슈가 있으시면 GitHub Issues에 등록해주세요.
