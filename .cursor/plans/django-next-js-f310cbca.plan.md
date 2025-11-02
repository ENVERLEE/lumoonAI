<!-- f310cbca-cfba-42d1-94e9-6b3b6d1ea7fe 73030f4e-376a-4b8f-a3a9-116730067460 -->
# Django와 Next.js 완전 분리 계획

## 목표

- Django: REST API만 제공 (프론트엔드 정적 파일 제공 제거)
- Next.js: 새로운 프론트엔드 (App Router 사용)
- 완전히 독립된 두 애플리케이션으로 분리

## 작업 범위

### 1. Next.js 프로젝트 초기화 ✅

- `/frontend` 디렉토리에 Next.js 프로젝트 생성 (App Router)
- TypeScript 선택 가능 (선택사항)
- Tailwind CSS 또는 기존 CSS 스타일 유지
- 환경 변수 설정 파일 생성 (`.env.local`)

### 2. Django 설정 수정 ✅

- `prompt_mate/settings.py`:
  - `TEMPLATES` 설정에서 `app` 디렉토리 제거
  - `STATICFILES_DIRS`에서 `app` 디렉토리 제거
  - CORS 설정 유지 (Next.js 도메인 허용)

- `prompt_mate/urls.py`:
  - 프론트엔드 템플릿 라우트 제거
  - API 경로만 유지

### 3. API 클라이언트 구성 ✅

- 모든 API 모듈 TypeScript로 변환 완료

### 4. 누락된 기능 구현 (우선순위)

#### 4.1 질문-답변 UI 완전 구현

- `components/QuestionMessage.tsx`: 질문 표시 컴포넌트
  - 우선순위 표시 (별점)
  - 질문 텍스트 및 rationale 표시
  - 선택지 버튼 (1, 2, 3...)
  - 건너뛰기 버튼
- 질문 답변 후 자동으로 다음 질문 표시
- 모든 질문 답변 완료 시 LLM 응답 생성

#### 4.2 대화 목록 클릭 기능

- `Sidebar.tsx`에서 대화 클릭 시 `ChatArea`에 대화 ID 전달
- `ChatArea.tsx`에서 대화 로드 함수 구현
- 메시지 히스토리 복원
- 세션 ID 연결

#### 4.3 예시 질문 클릭 기능

- `WelcomeScreen.tsx`의 suggestion chips에 onClick 핸들러 추가
- 클릭 시 메시지 입력 필드에 자동 입력 및 전송

#### 4.4 커스텀 지시사항 모달

- `components/SettingsModal.tsx` 구현
  - 커스텀 지침 입력/수정
  - 활성화/비활성화 토글
  - 저장 기능

#### 4.5 로그인/회원가입 모달 개선

- `components/AuthModal.tsx` 완성
  - 이메일 인증 상태 표시
  - 인증 이메일 재발송 기능
  - 로그인 성공 시 자동 새로고침

#### 4.6 구독 모달 완전 구현

- `components/SubscriptionModal.tsx` 구현
  - 플랜 선택 탭
  - 사용량 탭
  - 초대 탭 (초대 코드 생성/사용)
  - 결제 탭 (계좌 정보, 결제 요청, 상태 확인)

#### 4.7 프로필 모달 구현

- `components/ProfileModal.tsx` 구현
  - 사용자 정보 표시
  - 이메일 인증 상태 표시
  - 프로필 수정 (bio, avatar)
  - 이메일 인증 재발송

#### 4.8 사이드바 기능 보완

- "새 대화" 버튼 클릭 기능
- 대화 삭제 기능
- 활성 대화 하이라이트
- 프로필 클릭 시 프로필 모달 열기
- 구독 설정 버튼 클릭 시 구독 모달 열기

#### 4.9 ChatArea 기능 보완

- 설정 버튼 클릭 시 설정 모달 열기
- 구독 버튼 클릭 시 구독 모달 열기
- 피드백 버튼 (좋아요/아쉬워요)
- 모델 선택 드롭다운 (구독에 따라)

### 5. 상태 관리 개선

- 전역 상태를 위한 Context 생성 또는 props drilling 해결
- 현재 대화 ID를 Sidebar와 ChatArea 간 공유

### 6. 스타일링 ✅

- 기존 CSS 통합 완료

### 7. 추가 기능 검증

- 질문-답변 플로우 전체 테스트
- 대화 로드/저장 테스트
- 모든 모달 동작 테스트
- 구독 시스템 통합 테스트

## 주요 파일 구조

```
/frontend (새로 생성)
  /app
    layout.tsx
    page.tsx
    /auth
      page.tsx
  /components
    Sidebar.tsx
    ChatArea.tsx
    ...
  /lib
    api.ts
    auth.ts
  /styles
    globals.css
  .env.local
  package.json
  next.config.js

/reconciliation (기존)
  /core
    urls.py (수정)
    ...
  /prompt_mate
    settings.py (수정)
    urls.py (수정)
  /app (프론트엔드 파일들은 유지하되 사용 안 함)
```

## 주의사항

- CORS 설정: Django에서 Next.js 도메인 허용 필요
- 세션 쿠키: 도메인이 다르면 쿠키 설정 확인 필요
- 환경 변수: 개발/프로덕션별로 다른 API URL 사용 가능