# Loomon AI: 범용 AI 인터페이스 시스템

plainplan.md의 설계 원리를 바탕으로 구현된 Django 기반 AI 인터페이스 시스템입니다.

## 개요

Loomon AI는 사용자와 AI 사이의 "통역자 + 질문 설계자" 역할을 합니다. 사용자의 불완전한 입력을 분석하고, 필요한 정보를 수집하며, 최적화된 프롬프트를 자동으로 생성하여 AI가 최고의 성능을 발휘할 수 있도록 돕습니다.

## 주요 기능

### Phase 1 핵심 엔진 (현재 구현)

1. **Intent Parser (의도 파싱 엔진)**
   - LLM을 활용한 3차원 의도 분석 (인지적 목표, 구체성, 완결성)
   - 신뢰도 기반 명확화 요청
   - 경량 모델 사용으로 빠른 응답

2. **Context Elicitation (컨텍스트 도출)**
   - LLM 기반 적응적 질문 생성
   - 정보 엔트로피 최소화 알고리즘
   - 3단계 위계 구조 (Universal → Intent-Specific → Domain-Specific)

3. **Prompt Synthesis (프롬프트 합성)**
   - 5요소 구조 (Role + Task + Context + Constraints + Format)
   - 토큰 효율성 최적화
   - 인지적 목표별 템플릿

4. **LLM Provider 추상화**
   - 다중 제공자 지원 (OpenAI, Anthropic, Google)
   - 작업별 자동 모델 라우팅
   - 폴백 메커니즘

5. **Session 관리**
   - Stateful 세션
   - 컨텍스트 누적 및 학습
   - 사용자 선호도 추적

## 아키텍처

```
├── prompt_mate/          # Django 프로젝트
│   ├── settings.py       # 전역 설정
│   └── urls.py           # URL 라우팅
├── core/                 # 핵심 엔진 앱
│   ├── models.py         # Session, Intent, Question, PromptHistory
│   ├── intent_parser.py  # 의도 파싱
│   ├── context_elicitor.py  # 질문 생성
│   ├── prompt_synthesizer.py  # 프롬프트 합성
│   ├── session_manager.py  # 세션 관리
│   ├── serializers.py    # API 직렬화
│   ├── views.py          # API Views
│   └── urls.py           # API 엔드포인트
└── llm_providers/        # LLM 제공자 추상화
    ├── base.py           # 추상 인터페이스
    ├── openai_provider.py
    ├── anthropic_provider.py
    ├── google_provider.py
    └── router.py         # 모델 라우팅
```

## 설치 및 설정

### 1. 필수 요구사항

- Python 3.9+
- Django 4.2+
- PostgreSQL (선택적, SQLite로도 가능)
- Redis (선택적, 프로덕션 캐싱용)

### 2. 설치

```bash
# 저장소 클론
cd /Users/enverlee/reconciliation

# 가상환경 생성 (권장)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 설정하세요:

```bash
# Django 설정
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# LLM API Keys (최소 1개 필수)
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GOOGLE_API_KEY=your-google-api-key

# LLM 제공자 설정
DEFAULT_LLM_PROVIDER=openai

# Prompt Mate 설정
DEFAULT_MODEL_QUALITY=balanced
MAX_CONTEXT_QUESTIONS=4
SEMANTIC_CACHE_THRESHOLD=0.85
TOKEN_BUDGET=1500
INTENT_PARSER_MODEL=gpt-4o-mini
CONTEXT_ELICITOR_MODEL=gpt-4o-mini

# 결제 계좌 정보 (수동 결제 시스템용)
PAYMENT_BANK_NAME=국민은행
PAYMENT_ACCOUNT_NUMBER=123-45-67890
PAYMENT_ACCOUNT_HOLDER=홍길동
```

### 4. 데이터베이스 마이그레이션

```bash
python manage.py migrate
```

### 5. 서버 실행

```bash
python manage.py runserver
```

서버가 `http://localhost:8000`에서 실행됩니다.

## API 엔드포인트

### 기본 URL: `/api/`

#### 1. Intent 파싱

```http
POST /api/intent/parse/
Content-Type: application/json

{
  "user_input": "파이썬으로 웹 크롤러를 만들고 싶어요",
  "session_id": "optional-uuid"
}
```

**응답:**
```json
{
  "intent": {
    "cognitive_goal": "만들기",
    "specificity": "MEDIUM",
    "completeness": "PARTIAL",
    "confidence": 0.85
  },
  "session_id": "uuid",
  "needs_clarification": false
}
```

#### 2. 컨텍스트 질문 생성

```http
POST /api/context/questions/
Content-Type: application/json

{
  "session_id": "uuid"
}
```

**응답:**
```json
{
  "session_id": "uuid",
  "questions": [
    {
      "text": "당신의 경험 수준은 어느 정도인가요?",
      "priority": 1,
      "rationale": "경험 수준에 따라 설명 깊이 조절",
      "options": ["초보", "중급", "고급"],
      "default": "중급"
    }
  ]
}
```

#### 3. 질문 답변

```http
POST /api/context/answer/
Content-Type: application/json

{
  "session_id": "uuid",
  "question_text": "당신의 경험 수준은 어느 정도인가요?",
  "answer": "중급"
}
```

#### 4. 프롬프트 합성

```http
POST /api/prompt/synthesize/
Content-Type: application/json

{
  "session_id": "uuid",
  "user_input": "optional",
  "output_format": "optional"
}
```

#### 5. LLM 응답 생성

```http
POST /api/llm/generate/
Content-Type: application/json

{
  "session_id": "uuid",
  "quality": "balanced",
  "temperature": 0.7
}
```

**응답:**
```json
{
  "session_id": "uuid",
  "model_used": "gpt-4o-mini",
  "provider": "OpenAIProvider",
  "response": "생성된 응답 내용...",
  "tokens_used": 1250
}
```

#### 6. 피드백 제출

```http
POST /api/feedback/
Content-Type: application/json

{
  "session_id": "uuid",
  "feedback_text": "더 자세한 설명이 필요해요",
  "sentiment": "neutral"
}
```

## 프론트엔드 웹 인터페이스

### 실행 방법

1. **백엔드 서버 시작**
```bash
python manage.py runserver
```

2. **브라우저에서 접속**
```
http://localhost:8000/
```

3. **채팅 인터페이스 사용**
   - 입력 필드에 질문 입력
   - 시스템의 질문에 답변
   - AI 응답 확인
   - 피드백 제공

### 기능
- 💬 채팅 인터페이스 기반 UI
- 📱 반응형 디자인 (모바일 지원)
- 🎯 선택지 버튼으로 간편한 질문 답변
- ⏳ 실시간 로딩 인디케이터
- 💾 세션 자동 저장 및 복원
- 👍👎 피드백 시스템

자세한 내용은 [`app/README.md`](./app/README.md)를 참조하세요.

## 사용 예시

### Python으로 전체 워크플로우 실행

```python
import requests

BASE_URL = "http://localhost:8000/api"

# 1. Intent 파싱
response = requests.post(f"{BASE_URL}/intent/parse/", json={
    "user_input": "Django로 REST API를 만들고 싶어요"
})
data = response.json()
session_id = data['session_id']

# 2. 질문 생성
response = requests.post(f"{BASE_URL}/context/questions/", json={
    "session_id": session_id
})
questions = response.json()['questions']

# 3. 질문 답변
for question in questions:
    requests.post(f"{BASE_URL}/context/answer/", json={
        "session_id": session_id,
        "question_text": question['text'],
        "answer": question['default'] or "중급"
    })

# 4. LLM 생성
response = requests.post(f"{BASE_URL}/llm/generate/", json={
    "session_id": session_id,
    "quality": "balanced"
})
result = response.json()
print(result['response'])
```

## 비용 최적화

- **Intent Parsing**: GPT-4o-mini ($0.15/1M tokens) - 빠르고 저렴
- **Context Questions**: GPT-4o-mini - 경량 모델로 충분
- **Final Generation**: 품질 요구사항에 따라 유연하게 선택
- **캐싱**: 동일/유사 입력에 대한 중복 호출 방지

## 개발 가이드

### 새로운 LLM 제공자 추가

`llm_providers/` 디렉토리에 새 파일을 만들고 `BaseLLMProvider`를 상속:

```python
from .base import BaseLLMProvider, LLMResponse

class MyProvider(BaseLLMProvider):
    def generate(self, prompt, model, temperature, **kwargs):
        # 구현
        pass
    
    def generate_json(self, prompt, schema, **kwargs):
        # 구현
        pass
```

### 테스트

```bash
# 단위 테스트 (구현 예정)
python manage.py test

# API 테스트
curl -X POST http://localhost:8000/api/intent/parse/ \
  -H "Content-Type: application/json" \
  -d '{"user_input": "테스트 입력"}'
```

## 문제 해결

### LLM API 키 오류
```
LLMProviderError: OpenAI 클라이언트가 초기화되지 않았습니다.
```
→ `.env` 파일에서 `OPENAI_API_KEY` 등 API 키가 설정되었는지 확인

### 마이그레이션 오류
```bash
python manage.py migrate --run-syncdb
```

### 포트 충돌
```bash
python manage.py runserver 8001
```

## 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다.

## 기여

버그 리포트, 기능 요청, Pull Request를 환영합니다!

## 참고 자료

- [plainplan.md](./plainplan.md) - 전체 설계 원리
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)

