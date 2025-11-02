# Loomon AI 프론트엔드

바닐라 JavaScript로 구현된 채팅 인터페이스 기반 프론트엔드입니다.

## 파일 구조

```
app/
├── index.html      # 메인 HTML 페이지
├── styles.css      # 스타일시트
├── api.js          # API 통신 레이어
├── app.js          # 메인 애플리케이션 로직
└── README.md       # 이 파일
```

## 실행 방법

### 1. 백엔드 서버 실행

먼저 Django 백엔드 서버를 실행해야 합니다:

```bash
# 프로젝트 루트 디렉토리에서
python manage.py runserver
```

서버가 `http://localhost:8000`에서 실행됩니다.

### 2. 프론트엔드 접속

브라우저에서 다음 URL로 접속:

```
http://localhost:8000/
```

Django가 `app/index.html`을 서빙합니다.

## 사용 방법

### 1. 대화 시작

1. 입력 필드에 질문이나 요청을 입력합니다
   - 예: "Python으로 웹 크롤러를 만들고 싶어요"
   - 예: "Django REST API에 대해 배우고 싶어요"

2. 전송 버튼을 클릭하거나 Enter 키를 누릅니다

### 2. 질문 답변

시스템이 컨텍스트를 파악하기 위한 질문을 표시할 수 있습니다:
- 경험 수준 (초보/중급/고급)
- 목적 (개인용/업무용/학습용)
- 기타 도메인별 질문

각 질문에 버튼을 클릭하여 답변합니다.

### 3. 응답 확인

모든 질문에 답변하면 AI가 최적화된 응답을 생성합니다.

### 4. 피드백

응답 하단의 피드백 버튼으로 만족도를 표시할 수 있습니다:
- 👍 좋아요
- 👎 아쉬워요

### 5. 새 대화

"새 대화 시작" 버튼을 클릭하면 새로운 세션이 시작됩니다.

## 주요 기능

### 세션 관리
- 세션 ID가 자동으로 생성되어 localStorage에 저장됩니다
- 페이지를 새로고침해도 세션이 유지됩니다
- "새 대화 시작"으로 새 세션을 시작할 수 있습니다

### 대화 플로우
1. **Intent 파싱**: 사용자 입력의 의도를 자동으로 분석
2. **컨텍스트 수집**: 필요한 정보를 질문으로 수집
3. **프롬프트 합성**: 최적화된 프롬프트 자동 생성
4. **LLM 생성**: AI가 답변 생성
5. **피드백**: 사용자 만족도 수집

### UI/UX 특징
- 📱 반응형 디자인 (모바일 지원)
- ✨ 부드러운 애니메이션
- 💬 채팅 버블 스타일
- ⏳ 로딩 인디케이터
- 🎯 선택지 버튼
- 📊 모델 정보 표시
- 🕐 타임스탬프

## API 연동

프론트엔드는 다음 백엔드 API를 사용합니다:

- `POST /api/intent/parse/` - Intent 파싱
- `POST /api/context/questions/` - 질문 생성
- `POST /api/context/answer/` - 답변 저장
- `POST /api/llm/generate/` - LLM 응답 생성
- `POST /api/feedback/` - 피드백 저장

## 개발자 정보

### 코드 구조

**api.js**
- REST API 호출을 위한 래퍼 함수들
- 에러 핸들링
- `window.LoomonAIAPI`로 export

**app.js**
- `LoomonAIApp` 클래스
- 대화 플로우 제어
- UI 렌더링
- 이벤트 핸들링
- 세션 관리

### 커스터마이징

**API 베이스 URL 변경**
```javascript
// api.js
const API_BASE_URL = 'http://your-backend-url/api';
```

**스타일 변경**
```css
/* styles.css */
:root {
    --primary-color: #667eea;  /* 메인 색상 */
    --user-message-bg: #667eea;  /* 사용자 메시지 배경색 */
    /* ... */
}
```

## 문제 해결

### CORS 오류
Django `settings.py`에서 CORS 설정 확인:
```python
CORS_ALLOW_ALL_ORIGINS = True
```

### Static 파일 로드 실패
Django `settings.py`에서 static 파일 설정 확인:
```python
STATICFILES_DIRS = [BASE_DIR / 'app']
```

### API 호출 실패
1. 백엔드 서버가 실행 중인지 확인
2. API_BASE_URL이 올바른지 확인
3. 브라우저 콘솔에서 에러 메시지 확인
4. Django 서버 로그 확인

## 브라우저 지원

- Chrome/Edge (최신 버전)
- Firefox (최신 버전)
- Safari (최신 버전)
- 모바일 브라우저

## 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다.

