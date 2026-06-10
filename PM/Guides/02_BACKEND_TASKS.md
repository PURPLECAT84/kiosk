# ⚙️ BACKEND TASKS (FastAPI & Database)

> **Role:** PM이 할당한 백엔드 로직 설계, DB 스키마 생성 및 API 라우터 구현을 담당합니다.

## 🚀 백엔드 개발 기본 원칙 (Core Principles)

1. **패키지 및 환경 관리:** `pip` 대신 반드시 `uv`를 활용합니다. (의존성 추가, 실행 등 모두 `uv` 기반)
2. **최신 스펙 지향:** `SQLAlchemy 2.0`을 비롯한 모든 라이브러리는 최신 버전의 문법과 아키텍처를 기준으로 작성합니다.
3. **상세한 주석:** 초보자도 원리를 이해할 수 있도록 코드에 상세한 주석과 설명을 포함합니다.
4. **[특명] FASTAPI 학습가이드 제공:** 작성하는 모든 코드(라우터, 모델, 로직 등)에 기능의 목적, 주의점, 원리를 가독성 좋은 주석으로 기록하여, 코드 자체가 훌륭한 'FastAPI 학습 교과서'가 되도록 합니다. 기능 변경 시 주석도 반드시 업데이트합니다.

## 📝 TODO List (V2.1 백로그)

- `[ ]` 외식형(Type B) 다중 출력 트랜잭션 로직 설계 (알림톡 API vs 프린터 통신 분기)
- `[ ]` 네트워크 장애 대비 Local Storage 상태 동기화 API 구축
- [x] (20260610-1) Store(매장) 테이블 및 관련 라우터/스키마 영구 삭제
- [x] (20260610-1) Kiosk, Shelve, Category, Product, Order 모델을 kiosk_id에 직접 귀속되도록 다대일 관계 리팩토링
- [x] (20260610-1) `/order` 조회 API, `/kiosks/active-stores` API 등에서 store_id 의존성 제거 및 kiosk_id 및 user_id 매개변수 기반 고도화
- [x] (20260610-1) 초기 데이터 시딩 스크립트(seeder.py)에서 더미 점주(dummy1@moki.com)에 대한 BusinessInfo(매장명: 모키반점) 적재 및 사업자 최종 활성화(is_business_verified=True) 강제 설정
- [x] (20260610-1) 상품 모델에서 불필요한 거래처/원산지(buy_from) 필드 및 스키마 속성 완전 제거
- [x] (20260508-1) Vite Proxy 지원을 위한 소셜 로그인 Redirect URI 경로 변경 (`/auth/callback` -> `/callback`)
- [x] (20260508-1) 소셜 계정 최초 연동 시 `user_info` 테이블의 `password` 필드 Not Null 제약조건 예외처리 완료 (`SOCIAL_LOGIN` 더미 암호 삽입)
- [x] (20260508-2) JWT 토큰에 `provider` 클레임 추가 (이메일/카카오/구글 구분)
- [x] (20260508-2) `POST /users/find-id` API 신설 (이름+전화번호 매칭 → 마스킹 이메일 반환)
- [x] (20260508-2) `POST /users/reset-password` API 신설 (3중 매칭 → 임시 비밀번호 발급)
- [x] (20260508-2) 비밀번호 복잡도 검증 로직 추가 (`validate_password_complexity`)
- [x] (20260508-2) `UserRole.NONE` Enum 추가 및 신규 가입 기본 권한 변경

---

_진행 방법:_

- `[ ]` : 대기 중
- `[/]` : 진행 중 (코딩 중)
- `[x]` : 완료
