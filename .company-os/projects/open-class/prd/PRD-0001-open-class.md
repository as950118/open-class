# PRD-0001: open-class 학원 수업 및 학습 일지 관리 SaaS

## 목표

여러 학원이 테넌트별로 안전하게 선생님, 학생, 수업, 반복 시간표, 실제 수업 세션과 학생별 일지를 관리하도록 한다. 가장 중요한 제품 데이터는 수업이 끝날 때마다 쌓이는 학습 기록이다.

## 사용자와 권한

- `SUPER_ADMIN`: 플랫폼과 가입 학원 관리
- `ACADEMY_ADMIN`: 소속 학원의 전체 운영 및 데이터 관리
- `TEACHER`: 본인 일정, 담당 학생과 수업, 본인이 작성한 일지 관리
- `STUDENT`: 본인 시간표, 수업 이력과 일지 조회

모든 권한은 UI와 별도로 API에서 검증한다. 모든 학원 소속 데이터는 `academy_id` 기준으로 격리한다.

## 제품 범위

1. 인증·역할 기반 접근 제어
2. 학원/선생님/학생/과목/개설 수업/수강 등록 관리
3. 반복 시간표와 실제 세션 관리, 일정 충돌 검증
4. 세션 참석 학생 및 학생별 개별 학습 일지
5. 학생/선생님/수업/기간/과목/키워드 기준 기록 조회
6. 운영 대시보드 및 통합 검색

## 핵심 엔티티

Academy, User, Teacher, Student, Subject, Course, Enrollment, Schedule, LessonSession, LessonSessionStudent, LessonLog. 수업 세션과 반복 스케줄을 분리하고, 한 세션 안의 각 학생에 일지를 연결한다. LessonLog는 academy, session, teacher, student를 명시적으로 참조한다.

## 비기능 요구사항

- REST API `/api/v1`, request/response Pydantic 스키마 분리
- PostgreSQL, Alembic, 트랜잭션과 DB 제약 조건
- 비밀번호 안전 해시, 인증 필요 API와 역할 검사
- 모든 쿼리의 학원 경계 강제, SQLAlchemy 바인딩 파라미터 사용
- PostgreSQL `pg_trgm` 기반 초기 부분 검색, 검색 코드는 서비스 경계에 격리
- 한국어 UI, Asia/Seoul 날짜·시간 표기, 반응형 레이아웃
- Docker Compose 기반 로컬 개발 및 환경 변수 설정

## 단계/완료 조건

단계별 범위는 저장소 README의 로드맵을 따른다. Phase 1은 Compose에서 프론트엔드, API, PostgreSQL이 실행되고 프론트엔드에서 DB 연결 상태를 확인할 수 있으며, API 기본 문서와 Alembic 마이그레이션 경로가 준비되면 완료다. 이후 단계는 실제 API/DB 동작과 권한 검증을 포함해야 하며 정적 화면으로 대체하지 않는다.
