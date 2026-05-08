# 📄 20260508-2 작업 결과 요약 보고서

## 작업 목표
개인정보 수정 화면 개발, 아이디/비밀번호 찾기 기능 구현, 보안 강화

---

## 1. UI 레이아웃 개편 (Dashboard)
- **좌측 상단 로고 영역**: 클릭 시 대시보드 메인(`/`)으로 이동하는 링크로 변경
- **우측 상단 헤더**: `[권한 뱃지] - [내 정보 아이콘(UserCircle)] - [로그아웃 아이콘]` 순으로 재배치
- **좌측 하단 로그아웃 버튼**: 제거 (우측 상단 아이콘으로 통합)

## 2. 내 정보(Profile) 페이지 신설 (`/profile`)
- **로그인 상태 뱃지**: JWT 내 `provider` 필드 기반으로 📧이메일 / 💬카카오 / 🌐구글 뱃지 동적 표시
- **개인정보 수정**: 이름, 전화번호 수정 후 `PATCH /users/me` API 연동
- **비밀번호 변경** (이메일 계정만 표시 - 옵션 A):
  - 현재 비밀번호 → 새 비밀번호 → 새 비밀번호 확인
  - 소셜 로그인 계정은 "비밀번호 변경 불가" 안내 카드 표시
- **소셜 계정**: 비밀번호 변경 폼 숨기고 안내 메시지 표시

## 3. 로그인 상태 추적 로직 (Backend)
- `schemas/user.py`: `UserResponse`에 `login_provider` 필드 추가
- `routers/user.py` 이메일 로그인 JWT: `provider: "email"` 포함
- `routers/social_login.py` 소셜 로그인 JWT: Supabase `app_metadata.provider` 값 포함
- `core/dependency.py`: 토큰 해독 시 `provider` 추출 후 유저 객체에 동적 주입

## 4. 비밀번호 복잡도 정책 적용
- **조건**: 영문 + 숫자 + 특수문자 조합, 8자 이상
- **적용 범위**: 회원가입(`SignupPage`), 비밀번호 변경(`ProfilePage`)
- **Frontend**: 정규식 1차 검증 → 안내 메시지 표시
- **Backend**: `schemas/user.py` `validate_password_complexity()` 함수로 2차 검증

## 5. 회원 권한 기본값 변경
- DB PostgreSQL `userrole` Enum에 `NONE` 값 추가
- `models/user.py` `UserInfo.role` 기본값: `STAFF` → `NONE`으로 변경
- 소셜 로그인 최초 가입 시도 기본값도 동일하게 `NONE` 적용

## 6. 아이디 찾기 기능 (`/find-id`)
- 이름 + 전화번호 입력 → DB 매칭
- 매칭 성공 시 이메일 앞 2자리만 노출하고 나머지 `*` 마스킹 반환
  - 예) `pmountain@naver.com` → `pm*******@naver.com`
- `POST /users/find-id` API 신설

## 7. 비밀번호 찾기 / 임시 비밀번호 발급 (`/find-password`)
- 이메일 + 이름 + 전화번호 **3중 매칭** 검증
- 성공 시 영문 대소 + 숫자 + 특수문자 조합 **12자리 임시 비밀번호 자동 생성**
- 임시 비밀번호를 **화면에 직접 표시** + 클립보드 복사 버튼 제공
- 소셜 계정(`SOCIAL_LOGIN`) 접근 시 자동 차단 처리
- `POST /users/reset-password` API 신설
- *(상용화 시 화면 노출 → 이메일 발송 방식으로 업그레이드 예정)*

## 8. 로그인 화면 개편 (`/login`)
- 로그인 버튼 하단에 `아이디 찾기 | 비밀번호 찾기` 링크 추가

---

## 데이터 정리
- 개발 중 생성된 더미 계정 5개(`dummy1~5@moki.com`) DB에서 삭제 완료
- 임시 디버깅 스크립트 삭제 완료

## 다음 작업 방향
- 대시보드 세부 기능 개발 (주문 내역, 상품 관리)
- 키오스크(Flutter) 개발 환경 세팅
