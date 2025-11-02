# Prompt Mate: 범용 AI 인터페이스 시스템 설계 (원리 중심)

## 1. 핵심 설계 원리

### 1.1 문제의 본질
**사람들이 AI를 제대로 활용하지 못하는 이유:**
1. **의도-언어 변환 실패**: 머릿속 목표를 AI가 이해할 수 있는 구조화된 질문으로 전환하는 능력 부족
2. **컨텍스트 누락**: AI가 좋은 답을 하려면 필요한 정보가 무엇인지 모름
3. **피드백 루프 비효율**: 원하는 결과가 나올 때까지 시행착오를 반복하는 과정이 비체계적

### 1.2 Prompt Mate의 해결 원리
**"사용자와 AI 사이의 통역자 + 질문 설계자"**

```
[기존 패러다임]
사용자 → (불완전한 질문) → AI → (부정확한 답변) → 반복

[새로운 패러다임]
사용자 → (날것의 의도) → Prompt Mate → (최적화된 프롬프트) → AI → (정확한 답변)
                           ↓
                    (필요한 정보 역질문)
```

### 1.3 시스템의 3대 핵심 기능
1. **Intent Parsing**: 사용자의 날것 입력에서 진짜 의도 추출
2. **Context Elicitation**: 좋은 답변에 필요한 정보를 최소한의 질문으로 수집
3. **Prompt Synthesis**: 의도 + 컨텍스트를 AI가 최고 성능을 낼 수 있는 프롬프트로 합성

---

## 2. Intent Parsing Engine (의도 파싱 엔진)

### 2.1 의도의 구조적 분해
모든 사용자 입력은 다음 3가지 차원으로 분해 가능:

#### 차원 1: 인지적 목표 (Cognitive Goal)
- **알기** (Know): 정보 획득, 이해, 비교
- **하기** (Do): 문제 해결, 실행, 변환
- **만들기** (Create): 생성, 작성, 디자인
- **배우기** (Learn): 학습, 연습, 숙달

#### 차원 2: 구체성 수준 (Specificity Level)
- **추상적** (Abstract): "행복", "성공", "좋은 코드"
- **범주적** (Categorical): "파이썬", "마케팅", "다이어트"
- **구체적** (Specific): "Flask 에러 500", "인스타 광고 CTR 개선"

#### 차원 3: 완결성 (Completeness)
- **완전한 쿼리**: 필요한 정보가 모두 포함 (드물음)
- **부분적 쿼리**: 핵심 정보만 있고 세부사항 누락 (대부분)
- **모호한 쿼리**: 해석의 여지가 큼

### 2.2 파싱 알고리즘 원리

```python
def parse_intent(user_input):
    """
    3단계 파싱 프로세스
    """
    # Stage 1: 언어적 분석
    linguistic_features = {
        'question_words': ['무엇', '어떻게', '왜'],  # Know 신호
        'action_verbs': ['만들어', '해결', '고쳐'],  # Do/Create 신호
        'learning_markers': ['배우', '공부', '연습'], # Learn 신호
        'entities': extract_named_entities(user_input),
        'domain_keywords': match_domain_vocabulary(user_input)
    }

    # Stage 2: 의미적 추론 (경량 모델)
    semantic_intent = lightweight_llm_classify(
        user_input,
        candidates=[
            "사용자는 정보를 원한다",
            "사용자는 문제를 해결하려 한다",
            "사용자는 무언가를 만들려 한다",
            "사용자는 배우려 한다"
        ]
    )

    # Stage 3: 신뢰도 평가
    confidence = calculate_confidence(
        linguistic_features,
        semantic_intent
    )

    if confidence < THRESHOLD:
        return clarification_needed()

    return {
        'cognitive_goal': semantic_intent,
        'specificity': measure_specificity(user_input),
        'domain': identify_domain(entities, domain_keywords),
        'missing_info': infer_missing_context()
    }
```

### 2.3 핵심 설계 결정
- **2단계 모델 사용**: 1차 분류는 경량 모델 (속도), 애매한 경우만 고성능 모델
- **신뢰도 기반 분기**: 확신이 없으면 사용자에게 직접 물어보는 게 비용 효율적
- **도메인 지식 주입**: 코딩, 마케팅 등 주요 도메인의 고유 패턴을 사전 학습

---

## 3. Context Elicitation System (컨텍스트 도출 시스템)

### 3.1 정보 이론적 접근

**핵심 원리**: AI가 좋은 답변을 하는 데 필요한 정보의 엔트로피를 최소화하는 최소 질문 집합 찾기

```
H(Answer | User_Input) = High Entropy (불확실성 큼)
→ 어떤 정보 X를 물어보면 H(Answer | User_Input, X)가 가장 감소?
→ 그 정보를 우선 질문
```

### 3.2 컨텍스트의 위계 구조

#### Level 0: Universal Context (모든 의도에 필요)
- **숙련도** (Expertise): 초보 / 중급 / 전문가
  - 설명의 깊이, 전문 용어 사용 여부 결정
- **목적** (Purpose): 개인용 / 업무용 / 공유용
  - 형식성, 완성도 수준 결정
- **제약** (Constraints): 시간, 길이, 형식
  - 출력 스타일 결정

#### Level 1: Intent-Specific Context
각 인지적 목표마다 고유한 필수 정보:

**Know (알기)**
- 지식 수준: 이미 아는 것 / 배경 지식
- 깊이 요구: 개요 / 상세 / 전문적

**Do (하기)**
- 현재 상태: 무엇이 문제인가
- 시도한 것: 이미 해본 방법들
- 제약 조건: 사용 가능한 도구/환경

**Create (만들기)**
- 스타일: 톤, 형식, 레퍼런스
- 타겟: 누가 볼 것인가
- 분량: 길이, 복잡도

**Learn (배우기)**
- 현재 수준: 사전 지식
- 목표 수준: 어디까지 도달할 것인가
- 학습 방식: 이론 / 실습 / 혼합

#### Level 2: Domain-Specific Context
특정 도메인에서만 의미 있는 정보:

**코딩 도메인**
- 언어/프레임워크
- 개발 환경
- 에러 메시지 (문제 해결 시)

**글쓰기 도메인**
- 독자
- 매체 (블로그/공식문서/소셜미디어)
- 길이 제약

### 3.3 질문 생성 알고리즘

```python
def generate_questions(intent_analysis):
    """
    최소 질문으로 최대 정보 획득
    """
    questions = []

    # Step 1: Universal Context
    questions.extend(
        select_universal_questions(
            intent_analysis['cognitive_goal']
        )
    )

    # Step 2: Intent-Specific
    questions.extend(
        generate_intent_questions(
            intent_analysis['cognitive_goal'],
            intent_analysis['specificity']
        )
    )

    # Step 3: Domain-Specific
    if intent_analysis['domain']:
        questions.extend(
            generate_domain_questions(
                intent_analysis['domain'],
                intent_analysis['missing_info']
            )
        )

    # Step 4: 중요도 순 정렬 및 필터링
    ranked_questions = rank_by_information_gain(questions)

    # 최대 3-4개만 질문 (사용자 피로도 최소화)
    return ranked_questions[:MAX_QUESTIONS]
```

### 3.4 질문 최적화 원칙

**원칙 1: 선택지 우선**
- 자유 입력보다 선택지가 더 빠르고 구조화된 데이터 제공
- 선택지는 상호배타적이고 집합적으로 완전해야 함 (MECE 원칙)

**원칙 2: 점진적 구체화**
- 첫 질문은 넓게 (카테고리 분류)
- 답변에 따라 다음 질문이 동적으로 변화
- 불필요한 질문은 스킵

**원칙 3: 디폴트 값 제공**
- 모든 질문에 합리적인 기본값 설정
- 사용자가 답하지 않으면 기본값 사용 (friction 최소화)

---

## 4. Prompt Synthesis Engine (프롬프트 합성 엔진)

### 4.1 프롬프트의 구조 이론

좋은 프롬프트의 필수 구성 요소:

```
Prompt = Role + Task + Context + Constraints + Format
```

#### 4.1.1 Role (역할 정의)
```python
role_templates = {
    'Know': "당신은 {domain} 전문가입니다.",
    'Do': "당신은 {domain} 문제 해결 전문가입니다.",
    'Create': "당신은 {domain} 창작 전문가입니다.",
    'Learn': "당신은 {domain} 교육 전문가입니다."
}
```

#### 4.1.2 Task (작업 명세)
- 명확한 동사 사용 (설명하라, 생성하라, 분석하라)
- 의도에서 자동 추출

#### 4.1.3 Context (맥락 주입)
```python
context_structure = {
    'user_info': {
        'expertise_level': collected_answers['숙련도'],
        'purpose': collected_answers['목적']
    },
    'task_info': {
        'domain': intent_analysis['domain'],
        'specifics': collected_answers  # 도메인별 정보
    },
    'constraints': {
        'length': collected_answers['분량'],
        'style': collected_answers['스타일']
    }
}
```

#### 4.1.4 Constraints (제약 조건)
- 출력 길이
- 금지 사항
- 필수 포함 사항

#### 4.1.5 Format (출력 형식)
```python
format_specs = {
    'tutorial': "단계별 번호를 붙여 설명하고, 각 단계마다 예시를 포함하세요.",
    'solution': "문제 원인 분석 → 해결 방법 → 예상 결과 순으로 작성하세요.",
    'creative': "3가지 버전을 제시하고, 각각의 특징을 설명하세요."
}
```

### 4.2 합성 알고리즘

```python
def synthesize_prompt(intent, context, user_input):
    """
    의도와 컨텍스트를 최적 프롬프트로 변환
    """
    # 1. 템플릿 선택
    base_template = select_template(
        intent['cognitive_goal'],
        intent['domain']
    )

    # 2. 동적 요소 주입
    prompt = base_template.format(
        role=generate_role(intent),
        task=generate_task(intent, user_input),
        context=structure_context(context),
        constraints=extract_constraints(context),
        format=select_format(intent['cognitive_goal'])
    )

    # 3. 프롬프트 최적화
    optimized_prompt = optimize_prompt(prompt)

    return optimized_prompt
```

### 4.3 프롬프트 최적화 원칙

**원칙 1: 토큰 효율성**
```python
def optimize_prompt(prompt):
    """
    불필요한 토큰 제거
    """
    # 제거 대상:
    # - 불필요한 경어 ("please", "kindly")
    # - 중복 표현 ("very very", "really really")
    # - 장황한 전치사구

    # 압축 기법:
    # - 구조화된 키-값 형식 사용
    # - 불필요한 문장 연결 제거
    # - 핵심 정보만 남김

    return compressed_prompt
```

**원칙 2: 명확성 우선**
- 애매한 표현 제거
- 구체적인 지시어 사용
- 예시 포함 (few-shot learning)

**원칙 3: 계층적 구조**
```
# 나쁜 프롬프트
장황하고 구조 없는 긴 문단...

# 좋은 프롬프트
[역할]
...

[작업]
1. ...
2. ...

[제약]
- ...
- ...
```

---

## 5. Adaptive Response System (적응적 응답 시스템)

### 5.1 피드백 해석 원리

사용자의 자연어 피드백을 프롬프트 파라미터 조정으로 변환:

```python
feedback_mappings = {
    # 난이도 조정
    '쉽게': {'expertise_level': -1},  # 한 단계 낮춤
    '전문적으로': {'expertise_level': +1},

    # 길이 조정
    '짧게': {'length': 0.5},  # 50%로
    '자세히': {'length': 2.0, 'depth': +1},

    # 스타일 조정
    '격식있게': {'formality': +1},
    '편하게': {'formality': -1},

    # 구조 조정
    '예시 추가': {'examples': +2},
    '이론만': {'examples': 0, 'depth': +1}
}
```

### 5.2 점진적 개선 알고리즘

```python
def refine_response(original_prompt, response, feedback):
    """
    피드백을 받아 프롬프트를 점진적으로 개선
    """
    # 1. 피드백 파싱
    adjustments = parse_feedback(feedback)

    # 2. 프롬프트 파라미터 조정
    modified_params = apply_adjustments(
        original_prompt.params,
        adjustments
    )

    # 3. 새 프롬프트 생성 (델타만)
    refinement_prompt = f"""
    원래 응답: {response}

    다음과 같이 수정하세요:
    {format_adjustments(adjustments)}

    수정된 부분만 출력하세요.
    """

    # 4. 비용 절약: 전체 재생성이 아닌 델타만 생성
    return generate_delta(refinement_prompt)
```

### 5.3 학습 기반 개선

```python
class SessionMemory:
    """
    세션 내에서 사용자 선호도 학습
    """
    def __init__(self):
        self.user_preferences = {}
        self.feedback_history = []

    def learn_from_feedback(self, feedback, accepted):
        """
        피드백 패턴 학습
        """
        if accepted:
            # 이 조정이 효과적이었음
            self.user_preferences.update(feedback_adjustments)

        # 다음 응답 생성 시 학습된 선호도 반영
```

---

## 6. Model Routing & Cost Optimization (모델 라우팅 및 비용 최적화)

### 6.1 작업 복잡도 기반 모델 선택

```python
def select_model(task_complexity, quality_requirement):
    """
    작업의 복잡도와 품질 요구사항에 따라 모델 선택
    """
    complexity_score = calculate_complexity(
        factors=[
            'reasoning_depth',      # 추론 깊이
            'creativity_needed',    # 창의성 요구
            'precision_required',   # 정확도 요구
            'context_length'        # 컨텍스트 길이
        ]
    )

    if complexity_score < LOW_THRESHOLD:
        return 'gpt-4.1-nano'  # 빠르고 저렴
    elif complexity_score < HIGH_THRESHOLD:
        return 'gpt-4o-mini'    # 균형
    else:
        return 'gpt-4o'         # 최고 품질
```

### 6.2 캐싱 전략

```python
class SemanticCache:
    """
    의미론적 유사도 기반 캐싱
    """
    def __init__(self):
        self.cache = {}
        self.embeddings = {}

    def get(self, prompt):
        # 1. 정확히 동일한 프롬프트 체크
        if prompt in self.cache:
            return self.cache[prompt]

        # 2. 의미론적으로 유사한 프롬프트 탐색
        prompt_embedding = embed(prompt)
        for cached_prompt, cached_response in self.cache.items():
            similarity = cosine_similarity(
                prompt_embedding,
                self.embeddings[cached_prompt]
            )
            if similarity > SIMILARITY_THRESHOLD:
                # 캐시 히트: 약간 수정해서 반환
                return adapt_cached_response(
                    cached_response,
                    prompt
                )

        return None  # 캐시 미스
```

### 6.3 프롬프트 압축 이론

```python
def compress_prompt(prompt, target_reduction=0.25):
    """
    정보 손실 없이 토큰 수 감소
    """
    techniques = [
        remove_redundancy,      # 중복 제거
        use_abbreviations,      # 약어 사용
        structure_as_json,      # JSON 구조화
        remove_politeness,      # 불필요한 공손함 제거
        compress_examples       # 예시 압축
    ]

    compressed = prompt
    for technique in techniques:
        compressed = technique(compressed)
        if token_reduction(compressed) >= target_reduction:
            break

    return compressed
```

---

## 7. 시스템 아키텍처

### 7.1 계층 구조

```
┌─────────────────────────────────────┐
│        User Interface Layer          │  ← 사용자와의 접점
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Intent Processing Layer         │
│  ┌──────────────────────────────┐   │
│  │ Intent Parser                │   │
│  │ Context Elicitor             │   │
│  └──────────────────────────────┘   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│    Prompt Engineering Layer          │
│  ┌──────────────────────────────┐   │
│  │ Prompt Synthesizer           │   │
│  │ Template Manager             │   │
│  │ Optimization Engine          │   │
│  └──────────────────────────────┘   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Model Orchestration Layer       │
│  ┌──────────────────────────────┐   │
│  │ Model Router                 │   │
│  │ Cache Manager                │   │
│  │ Cost Optimizer               │   │
│  └──────────────────────────────┘   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        LLM Provider Layer            │
│   GPT-4o │ Claude │ Gemini          │
└─────────────────────────────────────┘
```

### 7.2 데이터 흐름

```
User Input
    ↓
[Intent Parser] → (cognitive_goal, domain, specificity)
    ↓
[Context Elicitor] → (questions)
    ↓
User Answers
    ↓
[Prompt Synthesizer] → (optimized_prompt)
    ↓
[Model Router] → (selected_model)
    ↓
[Cache Check] → HIT? return cached : generate new
    ↓
LLM API Call
    ↓
Response
    ↓
[Feedback Loop] → User satisfied? end : refine
```

---

## 8. API 설계 원칙

### 8.1 Stateful Session 관리

```python
class Session:
    """
    대화 세션 상태 관리
    """
    def __init__(self, session_id):
        self.id = session_id
        self.intent = None
        self.context = {}
        self.prompt_history = []
        self.response_history = []
        self.user_preferences = {}  # 학습된 선호도

    def update_state(self, new_info):
        """
        점진적 상태 업데이트
        """
        self.context.update(new_info)

    def get_effective_prompt(self):
        """
        현재까지 수집된 정보로 최적 프롬프트 생성
        """
        return synthesize_prompt(
            self.intent,
            self.context,
            self.prompt_history[0]  # 원래 입력
        )
```

### 8.2 멱등성과 재시도 안정성

```python
@retry(max_attempts=3, backoff=exponential)
def call_llm_api(prompt, model, session_id):
    """
    LLM API 호출 with 재시도 로직
    """
    # 같은 (prompt, model, session_id) 조합은
    # 항상 같은 결과 반환 (캐싱 활용)
    cache_key = hash(f"{prompt}:{model}:{session_id}")

    if cached := get_from_cache(cache_key):
        return cached

    response = llm_api.generate(prompt, model)

    save_to_cache(cache_key, response)
    return response
```

### 8.3 점진적 품질 향상

```python
class AdaptiveQuality:
    """
    사용자 만족도에 따른 품질 조정
    """
    def __init__(self):
        self.quality_level = 'balanced'

    def adjust_on_feedback(self, feedback_type):
        if feedback_type == 'needs_improvement':
            # 다음 응답은 더 고성능 모델 사용
            self.quality_level = 'high'
        elif feedback_type == 'satisfied':
            # 현재 수준 유지
            pass

    def select_model(self):
        return MODEL_MAPPING[self.quality_level]
```

---

## 9. 핵심 성공 지표 (KPI)

### 9.1 기술적 지표
- **Intent Classification Accuracy**: 의도 파악 정확도 > 90%
- **Average Questions per Session**: 평균 질문 수 < 4개
- **First Response Quality**: 첫 응답 만족도 > 80%
- **Token Efficiency**: 기존 직접 사용 대비 토큰 30% 절감

### 9.2 사용자 경험 지표
- **Time to First Result**: 결과까지 소요 시간 < 30초
- **Retry Rate**: 재시도 비율 < 20%
- **Session Completion Rate**: 중도 포기율 < 10%

### 9.3 비즈니스 지표
- **Cost per Session**: 세션당 비용 < $0.05
- **User Retention (D7)**: 7일 재방문율 > 40%
- **Conversion to Premium**: 무료→유료 전환율 > 5%

---

## 10. 시제품 개발 우선순위 (원리 중심)

### Phase 1: 핵심 엔진 구축
**목표**: 의도→프롬프트 변환 파이프라인 완성

1. **Intent Parser 구현**
   - 3차원 분석 (cognitive goal, specificity, completeness)
   - 경량 모델 기반 1차 분류
   - 신뢰도 측정 시스템

2. **Context Elicitation 로직**
   - 정보 이득 기반 질문 순위화
   - Universal + Intent-specific 질문 템플릿
   - 동적 질문 생성 (이전 답변에 따라 변화)

3. **Prompt Synthesis Engine**
   - 5요소 프롬프트 구조 (Role, Task, Context, Constraints, Format)
   - 템플릿 기반 + 동적 생성 하이브리드
   - 압축 알고리즘

### Phase 2: 최적화 레이어
**목표**: 비용 효율성과 성능 균형

1. **Model Router**
   - 복잡도 계산 알고리즘
   - 모델 선택 로직
   - 폴백 메커니즘

2. **Caching System**
   - 정확 매칭 캐시
   - 의미론적 유사도 캐시
   - TTL 관리

3. **Cost Tracker**
   - 실시간 비용 모니터링
   - 세션별 비용 추적
   - 예산 기반 자동 조정

### Phase 3: 적응 시스템
**목표**: 사용자 피드백 학습

1. **Feedback Interpreter**
   - 자연어 피드백 → 파라미터 조정 매핑
   - 델타 생성 (전체 재생성 방지)

2. **Session Memory**
   - 사용자 선호도 학습
   - 컨텍스트 누적
   - 다음 응답에 반영

---

## 11. 기술적 차별화 포인트

### vs. ChatGPT/Claude 직접 사용
1. **구조화된 정보 수집**: 무작정 질문하지 않고, 필요한 정보만 체계적으로 수집
2. **최적 프롬프트 자동 생성**: 사용자는 프롬프트 엔지니어링 불필요
3. **비용 효율적**: 작업별 최적 모델 선택으로 30%+ 비용 절감

### vs. 프롬프트 라이브러리/템플릿
1. **동적 적응**: 고정 템플릿이 아닌, 사용자 입력에 따라 실시간 커스터마이징
2. **컨텍스트 지능**: 필요한 정보만 최소한으로 질문
3. **학습 능력**: 세션 내 사용자 선호도 학습 및 반영

---

이 설계는 **"AI 사용의 인지적 부담을 시스템이 대신 짊어진다"**는 핵심 원리를 기반으로, 모든 구성 요소가 이론적으로 정당화되고 측정 가능하도록 구조화되었습니다.
