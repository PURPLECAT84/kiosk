# 📄 20260508-1 작업 결과 요약 보고서

## 1. 프로젝트 구조 전면 개편 (Monorepo화)
* **목적**: 기존 루트 폴더에 혼재되어 있던 백엔드/프론트엔드/관리용 파일들을 명확히 분리.
* **결과**: `Backend/`, `Partnercenter/`, `KioskScreen/`, `PM/` 등 4개의 독립된 역할별 디렉토리로 구조화 완료.
* **환경 동기화**: VS Code의 Multi-root Workspace (`kiosk.code-workspace`) 설정 및 Python 가상환경 인식용 `.vscode/settings.json` 구성 완료.

## 2. 파트너센터 프론트엔드 - 백엔드 통신 최적화 (Vite Proxy)
* **목적**: 하드코딩된 API 주소(`http://127.0.0.1:8000`)를 제거하여 배포 및 로컬 환경 변경에 유연하게 대응.
* **결과**: Vite의 `proxy` 설정(vite.config.ts)을 통해 `/users`, `/auth` 경로를 백엔드로 자동 라우팅. 프론트엔드의 `fetch` 함수들을 모두 상대 경로로 리팩토링.

## 3. 인증(Auth) 흐름 안정화 및 소셜 로그인 연동
* **회원가입/수동 로그인 QA**: Playwright 기반 자동화 스크립트를 작성하여 가입부터 로그아웃까지 전체 흐름 검증 성공 (결과물은 `PM/Scripts`로 이동).
* **소셜 로그인 콜백 페이지 구현**: `AuthCallbackPage.tsx`를 생성하여 Supabase에서 반환된 토큰을 백엔드 자체 JWT로 무사히 교환.
* **트러블슈팅 (Race Condition & Strict Mode)**:
  * 백엔드: DB의 `password` 컬럼 필수 제약조건을 우회하기 위해 소셜 계정은 `SOCIAL_LOGIN` 더미 암호를 넣도록 예외 처리.
  * 프론트엔드: 토큰 발급 후 `Dashboard` 진입 시 `user`가 갱신되기 전에 튕기는 레이스 컨디션을 막기 위해 `login()` 함수 호출 시 동기적으로 `isLoading=true` 부여.
  * 프론트엔드: React Strict Mode에 의한 `useEffect` 중복 실행(2번의 fetch)이 DB의 `IntegrityError`를 유발하고 페이지 강제 이동을 발생시키는 버그를 `useRef`를 도입하여 완벽히 차단.

## 4. 데이터 정리
* QA 및 트러블슈팅 과정에서 발생한 스크린샷 찌꺼기(`qa_error_*.png`) 삭제 완료.
* Playwright E2E 테스트 과정에서 생성된 31개의 테스트용 유저 계정(`testuser_*`)을 DB에서 말끔히 정리하여 초기화.

---
**다음 작업 방향**:
이후 PM 및 각 에이전트 가이드 문서를 바탕으로 대시보드 세부 기능 개발과 키오스크(Flutter) 개발 환경 세팅을 진행할 예정입니다.
