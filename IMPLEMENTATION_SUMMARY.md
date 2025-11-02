# ChatGPT 수준 AI 서비스 구현 완료

## 개요
Django + 바닐라 JS 기반의 ChatGPT급 고퀄리티 AI 서비스를 성공적으로 구현했습니다.

## 구현된 주요 기능

### 1. 사용자 인증 시스템 (Django Session 기반) ✅
- **백엔드**
  - `CustomUser` 모델 (Django AbstractUser 확장)
  - 회원가입 API: `/api/auth/register/`
  - 로그인 API: `/api/auth/login/`
  - 로그아웃 API: `/api/auth/logout/`
  - 사용자 정보 조회/수정 API: `/api/auth/me/`, `/api/auth/update/`
  - Django Session 기반 인증 (stateful)
  
- **프론트엔드**
  - 로그인/회원가입 모달 UI
  - 자동 인증 체크
  - 사용자 프로필 표시
  - 로그인 상태 관리

### 2. 대화 기록 관리 시스템 ✅
- **백엔드 모델**
  - `Conversation`: 대화 세션 (제목, 유저, 마지막 메시지 시각)
  - `Message`: 개별 메시지 (역할, 내용, 메타데이터)
  - Session을 Conversation과 연결
  
- **API**
  - 대화 목록: `GET /api/conversations/`
  - 대화 생성: `POST /api/conversations/`
  - 대화 상세: `GET /api/conversations/{id}/`
  - 메시지 조회: `GET /api/conversations/{id}/messages/`
  - 대화 이름 변경: `PATCH /api/conversations/{id}/rename/`
  - 대화 삭제: `DELETE /api/conversations/{id}/`
  
- **프론트엔드**
  - 사이드바에 대화 기록 목록 표시
  - 대화 클릭 시 메시지 로드
  - 자동 페이지네이션

### 3. RAG 시스템 (FAISS + OpenAI Embeddings) ✅
- **핵심 구현: `core/rag_manager.py`**
  - FAISS 인덱스 관리 (유저별 인덱스)
  - OpenAI `text-embedding-3-small` 사용 (1536차원)
  - 유사도 기반 검색 (top-k)
  - 임베딩 캐싱 (Redis)
  
- **데이터 모델**
  - `ConversationMemory`: 대화 임베딩 벡터 저장
  - 대화 저장 시 자동으로 임베딩 생성
  - FAISS 인덱스 자동 업데이트
  
- **통합**
  - `session_manager.py`에 RAG 통합
  - 프롬프트 합성 시 관련 대화 자동 검색
  - 관련 대화 컨텍스트를 프롬프트에 추가

### 4. 사용자별 커스텀 지침 ✅
- **백엔드**
  - `UserCustomInstructions` 모델 (지침 텍스트, 활성화 여부)
  - CRUD API: `/api/custom-instructions/`
  - 프롬프트 합성 시 자동 추가
  
- **프론트엔드**
  - 설정 모달에 커스텀 지침 탭
  - 텍스트 입력 및 활성화 토글
  - 저장 기능

### 5. 인터넷 모드 참고자료 주석 시스템 ✅
- **백엔드**
  - `SearchReference` 모델 (URL, 제목, 요약, 관련성 점수)
  - Perplexity Sonar의 citations 파싱
  - PromptHistory와 연결하여 참고자료 저장
  
- **프론트엔드**
  - 메시지에 참고자료 섹션 표시
  - 참고자료를 카드 형태로 표시
  - 클릭 시 새 탭에서 열기
  - 참고자료 개수 표시

## 기술 스택

### 백엔드
- Django 4.2
- Django REST Framework
- FAISS (벡터 검색)
- NumPy (벡터 연산)
- OpenAI API (임베딩, LLM)
- Perplexity API (인터넷 검색)
- Anthropic API (Claude)
- Google Gemini API
- PostgreSQL / SQLite

### 프론트엔드
- 바닐라 JavaScript (ES6+)
- HTML5 + CSS3
- Fetch API
- 모던 UI/UX 디자인

## 주요 파일 구조

```
reconciliation/
├── core/
│   ├── models.py                 # 모든 데이터 모델 (CustomUser, Conversation, Message, etc.)
│   ├── views.py                  # API ViewSets 및 Views
│   ├── auth_views.py             # 인증 API
│   ├── serializers.py            # DRF Serializers
│   ├── rag_manager.py            # RAG 시스템 (FAISS)
│   ├── session_manager.py        # 세션 관리 (RAG 통합)
│   └── urls.py                   # URL 라우팅
├── llm_providers/
│   ├── router.py                 # LLM 라우터
│   ├── openai_provider.py
│   ├── anthropic_provider.py
│   ├── google_provider.py
│   └── perplexity_provider.py
├── app/
│   ├── index.html                # 메인 HTML (모달 추가)
│   ├── app.js                    # 메인 앱 로직 (인증, 대화 기록)
│   ├── auth.js                   # 인증 API 함수
│   ├── api.js                    # 기존 API 함수
│   └── styles.css                # 스타일 (모달, 참고자료)
├── prompt_mate/
│   ├── settings.py               # AUTH_USER_MODEL 설정
│   └── urls.py
└── requirements.txt              # faiss-cpu, numpy 추가
```

## 데이터베이스 스키마

### 주요 테이블
- `users`: 사용자 (CustomUser)
- `conversations`: 대화 세션
- `messages`: 메시지
- `conversation_memories`: RAG 임베딩
- `user_custom_instructions`: 커스텀 지침
- `search_references`: 인터넷 검색 참고자료
- `sessions`: 세션 상태
- `intents`: 의도 분석
- `prompt_history`: 프롬프트 이력
- `feedbacks`: 피드백

## 실행 방법

### 1. 가상환경 활성화 및 패키지 설치
```bash
cd /Users/enverlee/reconciliation
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 환경 변수 설정
`.env` 파일 생성:
```
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key
PERPLEXITY_API_KEY=your_perplexity_key
```

### 3. 마이그레이션 (이미 완료)
```bash
python manage.py migrate
```

### 4. 슈퍼유저 생성
```bash
python manage.py createsuperuser
```

### 5. 서버 실행
```bash
python manage.py runserver
```

### 6. 접속
브라우저에서 `http://localhost:8000/` 접속

## API 엔드포인트

### 인증
- `POST /api/auth/register/` - 회원가입
- `POST /api/auth/login/` - 로그인
- `POST /api/auth/logout/` - 로그아웃
- `GET /api/auth/me/` - 현재 사용자 조회
- `PATCH /api/auth/update/` - 사용자 정보 수정

### 대화
- `GET /api/conversations/` - 대화 목록
- `POST /api/conversations/` - 대화 생성
- `GET /api/conversations/{id}/` - 대화 상세
- `GET /api/conversations/{id}/messages/` - 메시지 목록
- `PATCH /api/conversations/{id}/rename/` - 대화 이름 변경
- `DELETE /api/conversations/{id}/` - 대화 삭제

### 커스텀 지침
- `GET /api/custom-instructions/` - 조회
- `POST /api/custom-instructions/` - 저장
- `PATCH /api/custom-instructions/{id}/` - 수정

### LLM 생성
- `POST /api/llm/generate/` - AI 응답 생성
  - 파라미터: `internet_mode`, `specificity_level`, `quality`
  - RAG 자동 적용
  - 커스텀 지침 자동 적용
  - 인터넷 모드 시 참고자료 자동 저장

## 특별 기능

### 1. RAG 기반 대화 기억
- 사용자의 모든 대화를 임베딩하여 FAISS 인덱스에 저장
- 새로운 질문이 들어오면 유사한 과거 대화 자동 검색
- 관련 대화를 프롬프트에 자동 추가하여 맥락 유지

### 2. 커스텀 지침
- 사용자가 설정한 지침이 모든 응답에 자동 적용
- 예: "항상 한국어로 답변", "전문 용어 설명 포함" 등

### 3. 인터넷 모드
- Perplexity Sonar를 사용한 실시간 웹 검색
- 검색 결과와 함께 출처(citations) 자동 추출
- 참고자료를 카드 형태로 UI에 표시
- 각 참고자료에 URL, 제목, 도메인 표시

### 4. 고급 프롬프트 엔지니어링
- Intent Parser: 사용자 의도 분석
- Context Elicitor: 필요한 정보 질문
- Prompt Synthesizer: 최적화된 프롬프트 생성
- 구체성 레벨 조정 (짧음 ~ 매우 구체적)

## ChatGPT 수준 달성 요소

### ✅ 인증 및 사용자 관리
- Django Session 기반 안전한 인증
- 사용자 프로필 관리

### ✅ 대화 기록 영구 저장
- 모든 대화를 DB에 저장
- 언제든 과거 대화 불러오기

### ✅ RAG 기반 장기 기억
- FAISS로 벡터 검색
- 관련 대화 자동 참조
- 맥락 있는 대화 가능

### ✅ 커스텀 지침
- 사용자별 맞춤 동작
- 지침 활성화/비활성화

### ✅ 인터넷 검색
- 실시간 웹 정보 활용
- 출처 표시
- 신뢰성 확보

### ✅ 고퀄리티 UI/UX
- 모던한 디자인
- 반응형 레이아웃
- 직관적인 인터페이스

## 향후 개선 가능 사항
- 대화 검색 기능
- 대화 태그/카테고리
- 멀티모달 지원 (이미지, 파일)
- 팀/그룹 대화
- API rate limiting
- 더 정교한 RAG (Hybrid Search)
- 벡터 DB를 Chroma/Pinecone으로 마이그레이션

## 완료 상태
✅ 모든 TODO 완료
✅ 마이그레이션 성공
✅ 백엔드 API 구현 완료
✅ 프론트엔드 UI 구현 완료
✅ RAG 시스템 통합 완료
✅ 인터넷 모드 참고자료 시스템 완료

**프로젝트가 성공적으로 완료되었습니다!**

