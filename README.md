# open-class

학원의 선생님, 학생, 수업, 시간표와 학생별 수업 일지를 관리하는 멀티테넌트 SaaS입니다. **Phase 1~4 기반 구성, 인증·권한, 기본 데이터 관리, 반복 시간표와 개별 수업 회차**를 구현했습니다. 다음 단계는 수업 일지입니다.

## 기술 구성

- Frontend: React, TypeScript, Vite, Tailwind CSS, Lucide
- Backend: FastAPI, Pydantic Settings, SQLAlchemy 2, Alembic
- Database: PostgreSQL 17 (`pg_trgm` 확장 준비)
- Architecture: REST API 기반 모듈형 모놀리스, `/api/v1` API prefix
- 기본 시간대: Asia/Seoul

## 실행

Docker Desktop을 실행한 뒤 저장소 루트에서:

```bash
docker compose up --build
```

- 프론트엔드: http://localhost:5173
- API 문서: http://localhost:8000/docs
- API 및 DB 상태: http://localhost:8000/api/v1/health

`.env.example`을 `.env`로 복사해 설정할 수 있습니다. Compose 시작 시 Alembic 마이그레이션이 자동 적용됩니다. 개발 계정은 임의로 자동 생성하지 않습니다. `.env`에 12자 이상의 `SEED_PASSWORD`를 지정한 뒤 아래 명령으로 만들어 주세요.

```bash
docker compose exec backend python -m app.seed
```

시드 계정 이메일은 `admin@open-class.example.com`, `teacher@open-class.example.com`, `student@open-class.example.com`, `platform@open-class.example.com`이며 모두 `SEED_PASSWORD` 값을 사용합니다. 개발 환경 전용 계정입니다.

로그인 API는 JWT를 HTTP-only, SameSite 쿠키로 전달하고, `/api/v1/auth/me`에서 서버가 현재 계정과 역할을 확인합니다. 학원 관리자 데이터 조회는 본인 학원 범위로 제한됩니다.

## 단계별 계획

1. 기반 구성: Compose, React/FastAPI, PostgreSQL, Alembic, 공통 API 연결
2. 인증 및 권한: 로그인/로그아웃, 역할 검증, 학원별 데이터 격리
3. 기본 데이터 관리: 학원, 선생님, 학생, 과목, 수업, 수강 등록
4. 시간표: 반복 규칙, 세션 생성, 주간 보기, 중복 검증 (완료)
5. 수업 일지: 수업·학생·선생님 단위 기록과 조회
6. 검색 및 대시보드: 조합 검색, 통계, 미작성 일지
7. 품질 완성: 권한/격리 검증, 문서와 운영 준비

상세 PRD, 설계, 결정 기록과 진행 태스크는 [Company OS](.company-os/README.md)의 `projects/open-class/` 및 `tasks/`에서 관리합니다.
