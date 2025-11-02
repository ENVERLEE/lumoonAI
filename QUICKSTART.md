# Prompt Mate 빠른 시작 가이드

## 5분 안에 시작하기

### 1. 환경 설정

```bash
# 1. 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 최소한 하나의 API 키를 설정하세요:

```bash
# OpenAI (권장)
OPENAI_API_KEY=sk-your-api-key-here

# 또는 Anthropic
ANTHROPIC_API_KEY=sk-ant-your-api-key-here

# 또는 Google
GOOGLE_API_KEY=your-google-api-key-here
```

### 3. 데이터베이스 초기화

```bash
python manage.py migrate
```

### 4. 서버 실행

```bash
python manage.py runserver
```

### 5. 프론트엔드 접속

브라우저에서 열기:
```
http://localhost:8000/
```

## 첫 대화 시작하기

1. **질문 입력**
   ```
   "Python으로 웹 크롤러를 만들고 싶어요"
   ```

2. **질문 답변**
   - 시스템이 "경험 수준은?" 같은 질문을 합니다
   - 선택지 버튼을 클릭하여 답변합니다

3. **결과 확인**
   - AI가 최적화된 답변을 생성합니다
   - 만족도 피드백을 제공할 수 있습니다

## 문제 해결

### API 키 오류
```
LLMProviderError: OpenAI 클라이언트가 초기화되지 않았습니다.
```
→ `.env` 파일에 API 키가 올바르게 설정되었는지 확인하세요

### 포트 충돌
```bash
# 다른 포트로 실행
python manage.py runserver 8001
```

### CORS 오류
Django의 `settings.py`에서 CORS가 활성화되어 있는지 확인:
```python
CORS_ALLOW_ALL_ORIGINS = True
```

## 다음 단계

- [전체 README 보기](./README.md)
- [API 문서 보기](./README.md#api-엔드포인트)
- [프론트엔드 가이드](./app/README.md)
- [설계 원리 보기](./plainplan.md)

## 예제 질문

다음과 같은 질문들을 시도해보세요:

### 개발
- "Django로 REST API를 만들고 싶어요"
- "Python 데코레이터에 대해 알려주세요"
- "React에서 상태 관리는 어떻게 하나요?"

### 학습
- "머신러닝을 처음 배우려고 해요"
- "TypeScript를 배우고 싶어요"

### 문제 해결
- "Django에서 CORS 에러가 나요"
- "Python에서 메모리 누수를 찾는 방법"

## 주요 기능

✅ Intent 자동 파싱  
✅ 컨텍스트 기반 질문 생성  
✅ 최적화된 프롬프트 합성  
✅ 다중 LLM 제공자 지원  
✅ 세션 기반 대화  
✅ 채팅 웹 인터페이스  
✅ 피드백 시스템  

## 지원

문제가 발생하면:
1. [README.md](./README.md)의 문제 해결 섹션 확인
2. Django 서버 로그 확인
3. 브라우저 개발자 콘솔 확인

즐거운 코딩 되세요! 🚀

