# Loomon AI Frontend

바닐라 JavaScript로 구현된 프론트엔드 애플리케이션입니다.

## 실행 방법

### 1. Django 서버 실행 (별도 터미널)

```bash
cd /Users/enverlee/reconciliation
source venv/bin/activate
python manage.py runserver
```

Django 서버가 `http://localhost:8000`에서 실행됩니다.

### 2. 프론트엔드 서버 실행

프론트엔드는 별도의 HTTP 서버로 실행해야 합니다. Python 3의 내장 HTTP 서버를 사용할 수 있습니다:

```bash
cd /Users/enverlee/reconciliation/app
python3 -m http.server 8001
```

또는 Node.js가 설치되어 있다면:

```bash
cd /Users/enverlee/reconciliation/app
npx http-server -p 8001
```

### 3. 브라우저에서 접속

프론트엔드 서버가 `http://localhost:8001`에서 실행되면 브라우저에서 접속하세요.

## 환경 설정

### API 서버 URL 변경

`config.js` 파일에서 `API_BASE_URL`을 수정하여 Django API 서버 주소를 변경할 수 있습니다:

```javascript
const API_BASE_URL = 'http://localhost:8000';  // Django 서버 주소
```

프로덕션 환경에서는 실제 API 서버 주소로 변경하세요.

## 파일 구조

- `index.html` - 메인 HTML 파일
- `config.js` - API 설정
- `app.js` - 메인 애플리케이션 로직
- `auth.js` - 인증 관련 함수
- `conversation.js` - 대화 관리 함수
- `api.js` - 핵심 API 함수
- `subscription.js` - 구독 및 결제 함수
- `invite.js` - 초대 코드 함수
- `ui.js` - UI 컴포넌트 렌더링
- `styles.css` - 스타일시트

## 개발 팁

- CORS 오류가 발생하면 Django의 `CORS_ALLOWED_ORIGINS` 설정에 프론트엔드 서버 주소를 추가하세요.
- API 호출 시 `credentials: 'include'`를 사용하여 Django 세션 쿠키가 전송됩니다.

