# Railway 배포 체크리스트

## 배포 전 확인사항

### ✅ 코드 준비
- [x] Pinecone 클라이언트로 벡터 DB 변경 완료
- [x] requirements.txt에 모든 의존성 포함
- [x] Procfile 설정 완료
- [x] runtime.txt 설정 완료 (Python 3.9.18)
- [x] WhiteNoise 미들웨어 설정 완료
- [x] 정적 파일 설정 완료

### 📋 Railway 설정

#### 1. 프로젝트 생성
- [ ] Railway 계정 생성 ([https://railway.app](https://railway.app))
- [ ] "New Project" 클릭
- [ ] "Deploy from GitHub repo" 선택
- [ ] GitHub 저장소 연결 및 선택

#### 2. PostgreSQL 데이터베이스 추가
- [ ] Railway 프로젝트에서 "New" → "Database" → "Add PostgreSQL" 클릭
- [ ] PostgreSQL 인스턴스 생성 확인
- [ ] 자동으로 환경 변수가 설정되었는지 확인 (`PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGHOST`, `PGPORT`)

#### 3. Pinecone 계정 설정
- [ ] [Pinecone](https://www.pinecone.io) 가입
- [ ] API 키 생성
- [ ] 인덱스 이름 확인 (기본: `prompt-mate-memories`)

#### 4. 환경 변수 설정
Railway 대시보드 → "Variables" 탭에서 다음 변수들을 설정:

**필수 설정:**
- [ ] `SECRET_KEY` (Django 시크릿 키 생성 필요)
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS=your-app.railway.app,*.railway.app` (배포 후 실제 도메인으로 변경)

**LLM API Keys (최소 1개):**
- [ ] `OPENAI_API_KEY`
- [ ] `ANTHROPIC_API_KEY` (선택)
- [ ] `GOOGLE_API_KEY` (선택)
- [ ] `PERPLEXITY_API_KEY` (선택)

**Pinecone 설정:**
- [ ] `PINECONE_API_KEY`
- [ ] `PINECONE_INDEX_NAME=prompt-mate-memories` (선택, 기본값 사용 가능)

**LLM 설정:**
- [ ] `DEFAULT_LLM_PROVIDER=openai`
- [ ] `DEFAULT_MODEL_QUALITY=balanced`
- [ ] 기타 설정 (선택)

**CORS 설정 (프론트엔드가 별도 도메인인 경우):**
- [ ] `CORS_EXTRA_ORIGINS=https://your-frontend-domain.com`

## 배포 후 확인사항

### 배포 완료 확인
- [ ] Railway 배포 로그에서 에러 없음 확인
- [ ] 도메인 생성 및 접속 확인
- [ ] `/api/subscriptions/current/` 엔드포인트 정상 작동
- [ ] 데이터베이스 마이그레이션 완료 확인
- [ ] 구독 플랜 자동 생성 확인

### 기능 테스트
- [ ] 사용자 인증 (회원가입/로그인) 테스트
- [ ] LLM 생성 API 테스트
- [ ] RAG 기능 테스트 (Pinecone 연결 확인)
- [ ] 구독 플랜 조회 테스트

## SECRET_KEY 생성 방법

터미널에서 실행:
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

## 트러블슈팅

### 배포 실패 시
1. Railway 로그 확인: "Deployments" 탭
2. 환경 변수 확인: "Variables" 탭
3. 의존성 설치 실패 시 `requirements.txt` 확인

### 데이터베이스 마이그레이션 실패
```bash
railway run python manage.py migrate
```

### 구독 플랜이 없는 경우
```bash
railway run python manage.py create_subscription_plans
```

### Pinecone 연결 문제
1. `PINECONE_API_KEY` 환경 변수 확인
2. Pinecone 대시보드에서 API 키 활성화 확인
3. 로그에서 Pinecone 초기화 메시지 확인

