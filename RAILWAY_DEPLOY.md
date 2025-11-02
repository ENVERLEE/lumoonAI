# Railway 배포 가이드

## 1. Railway 계정 생성 및 프로젝트 생성

1. [Railway](https://railway.app)에 가입
2. "New Project" 클릭
3. "Deploy from GitHub repo" 선택
4. GitHub 저장소 연결 및 선택

## 2. PostgreSQL 데이터베이스 추가

**중요**: 프로덕션 환경에서는 PostgreSQL을 사용하는 것을 권장합니다.

1. Railway 프로젝트 대시보드에서 "New" → "Database" → "Add PostgreSQL" 클릭
2. Railway가 자동으로 PostgreSQL 인스턴스를 생성하고 환경 변수를 설정합니다
3. `DATABASE_URL` 환경 변수가 자동으로 생성됩니다 (이 변수를 사용하여 연결)
4. PostgreSQL 서비스가 **같은 프로젝트**에 있어야 자동으로 환경 변수가 설정됩니다

**확인 방법:**
- Railway 대시보드 → 프로젝트 → "Variables" 탭
- `DATABASE_URL` 변수가 있는지 확인
- 형식: `postgresql://user:password@host:port/database`

## 3. Pinecone 계정 설정 (벡터 DB)

**필수**: RAG 기능을 사용하려면 Pinecone 계정이 필요합니다.

1. [Pinecone](https://www.pinecone.io)에 가입 (무료 티어 제공)
2. 대시보드에서 API 키 생성
3. 환경 변수에 `PINECONE_API_KEY` 설정 (4번 섹션 참고)

**참고**: Pinecone은 클라우드 기반 벡터 DB이므로 별도의 볼륨이나 파일 저장소가 필요 없습니다.

## 4. 환경 변수 설정

Railway 대시보드의 "Variables" 탭에서 다음 환경 변수들을 설정하세요:

### 필수 설정
```bash
SECRET_KEY=your-production-secret-key-here  # Django SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=your-app.railway.app,*.railway.app
```

### PostgreSQL 설정 (선택사항)
Railway에서 PostgreSQL을 추가하면 `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGHOST`, `PGPORT` 환경 변수가 자동으로 설정됩니다. 
수동 설정이 필요한 경우에만 아래 변수들을 사용하세요:

```bash
PGDATABASE=railway  # Railway 자동 생성
PGUSER=postgres     # Railway 자동 생성
PGPASSWORD=*****    # Railway 자동 생성
PGHOST=containers-us-west-xxx.railway.app  # Railway 자동 생성
PGPORT=5432         # Railway 자동 생성
```


### LLM API Keys (최소 1개 필수)
```bash
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GOOGLE_API_KEY=your-google-api-key
PERPLEXITY_API_KEY=your-perplexity-api-key
```

### LLM 설정
```bash
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL_QUALITY=balanced
MAX_CONTEXT_QUESTIONS=4
SEMANTIC_CACHE_THRESHOLD=0.85
TOKEN_BUDGET=1500
INTENT_PARSER_MODEL=gpt-4o-mini
CONTEXT_ELICITOR_MODEL=gpt-4o-mini
```

### CORS 설정 (프론트엔드 도메인 추가)
```bash
CORS_EXTRA_ORIGINS=https://your-frontend-domain.com
```

### Pinecone (벡터 DB) 설정 (RAG 기능용)
Pinecone 무료 계정 생성: [https://www.pinecone.io](https://www.pinecone.io)

1. Pinecone 대시보드에서 API 키 생성
2. 인덱스 생성 (자동 생성되지만, 수동 생성도 가능)
3. 환경 변수 설정:

```bash
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX_NAME=prompt-mate-memories  # 선택적, 기본값 사용 가능
```

**참고**: Pinecone은 무료 티어를 제공하며, 인덱스는 자동으로 생성됩니다.

## 5. SECRET_KEY 생성 방법

터미널에서 실행:
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

또는:
```bash
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 6. 배포 확인

1. Railway가 자동으로 GitHub 푸시를 감지하여 배포 시작
2. 배포 완료 후 "Settings" → "Generate Domain"으로 도메인 생성
3. 생성된 도메인으로 API 테스트

## 7. 배포 후 확인사항

- [ ] `/api/subscriptions/current/` 엔드포인트 정상 작동 확인
- [ ] 데이터베이스 마이그레이션 완료 확인
- [ ] 구독 플랜 자동 생성 확인
- [ ] 로그에서 에러 없음 확인

## 8. 트러블슈팅

### Pinecone 연결 문제
Pinecone 연결이 안 될 경우:
1. `PINECONE_API_KEY` 환경 변수가 올바르게 설정되었는지 확인
2. Pinecone 대시보드에서 API 키가 활성화되어 있는지 확인
3. Pinecone 인덱스 이름이 올바른지 확인 (기본값: `prompt-mate-memories`)
4. 로그에서 Pinecone 초기화 메시지 확인

**참고**: Pinecone이 없어도 앱은 정상 작동하며 RAG 기능만 비활성화됩니다.

### 데이터베이스 마이그레이션 실패
Railway 대시보드 → "Deployments" → 로그 확인
수동으로 마이그레이션 실행:
```bash
railway run python manage.py migrate
```

### 구독 플랜이 없는 에러
자동 생성되지만, 수동 실행:
```bash
railway run python manage.py create_subscription_plans
```

### PostgreSQL 연결 오류
**증상**: `connection to server at "localhost" failed`

**해결 방법:**
1. Railway 대시보드에서 PostgreSQL 서비스가 **같은 프로젝트**에 있는지 확인
2. PostgreSQL 서비스가 실행 중인지 확인 (일시 정지 상태일 수 있음)
3. "Variables" 탭에서 `DATABASE_URL` 환경 변수가 있는지 확인
4. PostgreSQL 서비스가 다른 프로젝트에 있다면:
   - PostgreSQL 서비스의 "Variables" 탭에서 연결 정보 복사
   - 앱 프로젝트의 "Variables" 탭에 `DATABASE_URL` 수동 설정
   - 또는 PostgreSQL 서비스를 같은 프로젝트로 이동

**DATABASE_URL 형식:**
```
postgresql://postgres:password@host:port/railway
```


## 9. 모니터링

Railway 대시보드에서:
- 로그 확인: "Deployments" 탭
- 메트릭 확인: "Metrics" 탭
- 환경 변수 확인: "Variables" 탭

