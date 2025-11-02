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
3. `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGHOST`, `PGPORT` 변수가 자동 생성됩니다

## 3. 영구 볼륨 추가 (FAISS 인덱스 파일 저장용)

**선택사항**: FAISS 인덱스 파일을 영구 저장하려면 볼륨을 추가할 수 있습니다.

1. Railway 프로젝트 대시보드에서 "New" → "Volume" 클릭
2. Volume 이름: `data` (또는 원하는 이름)
3. Mount Path: `/data` 설정
4. 생성 완료 (FAISS 인덱스 저장용)

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

### FAISS 인덱스 저장용 (선택사항)
FAISS 인덱스 파일을 영구 볼륨에 저장하려면:
```bash
RAILWAY_VOLUME_MOUNT_PATH=/data  # 영구 볼륨 마운트 경로
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
- Railway 대시보드에서 PostgreSQL 서비스가 실행 중인지 확인
- `PGHOST`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` 환경 변수 확인
- Railway가 자동으로 설정한 환경 변수 사용 권장

### FAISS 인덱스 저장 (선택사항)
- 영구 볼륨을 추가한 경우 `RAILWAY_VOLUME_MOUNT_PATH` 환경 변수 확인
- 볼륨이 제대로 마운트되었는지 확인

## 9. 모니터링

Railway 대시보드에서:
- 로그 확인: "Deployments" 탭
- 메트릭 확인: "Metrics" 탭
- 환경 변수 확인: "Variables" 탭

