# 🎨 FRONTEND TASKS (React Web / Flutter App)

> **Role:** PM이 할당한 UI/UX 디자인 구현 및 백엔드 API와의 연동 작업을 담당합니다.

## 🚀 프론트엔드 UI/UX 가이드라인 (V2.1)

### 💻 파트너센터 (React Web)
1. **기술/테마:** React, Tailwind CSS, Lucide React 적용. 배경은 연한 그레이(`#F9FAFB`), 카드는 흰색. 메인 테마 퍼플(`#7C3AED`)은 중요 버튼과 활성화 메뉴에만 포인트로 사용.
2. **레이아웃:** Bento Grid 스타일, 부드러운 그림자(`shadow-sm`), 둥근 모서리(`rounded-2xl`). Shadcn/ui 스타일 차용.
3. **접근성/UX:** 시니어 점주 배려를 위해 기본 폰트 `text-lg` 적용, 대비 향상. 아이콘 옆 텍스트 명시. 호버 애니메이션(퍼플 강조) 적용.

### 📱 키오스크 클라이언트 (Flutter App)
1. **디자인 무드:** 연한 그레이 배경(`#F3F4F6`), 흰색 상품 카드(입체감). '결제 시작' 및 '최종 결제' 버튼에 메인 컬러 퍼플(`#7C3AED`) 강력 적용.
2. **접근성/UX:** 웹 대비 폰트 크기 1.5배 상향. 상품 가격은 굵은 서체 + 퍼플 색상.
3. **인터랙션/레이아웃:** Material 3 리플(Ripple) 효과 강화. 장바구니 애니메이션 적용. 화면 하단에 보라색 계열 장바구니/결제 영역 상시 고정 (`borderRadius: 20.0`).

## 📝 TODO List (V2.1 백로그)

- `[ ]` [Web] 파트너센터 대시보드 Bento Grid 레이아웃 뼈대 구축 및 테마 설정
- `[ ]` [Web] 외식형(Type B) / 상품판매형(Type A) 매장 타입 스위칭 토글 UI 구현
- `[ ]` [App] 하단 고정 장바구니 영역 UI 및 리플 애니메이션 뼈대 구축
- `[ ]` [App] ESC/POS 범용 프린터 통신 추상화 클래스(인터페이스) 설계
- `[x]` [App] (20260611-1) Store 모델 제거에 따른 Flutter 기기 연동 메커니즘에서 store_id 상태 및 가상결제 파라미터 완전 제거
- `[x]` [Web] (20260610-1) 매장 관리(StoreManagement.tsx, StoreDetail.tsx) 화면 파일 물리적 삭제 및 라우팅 제거
- `[x]` [Web] (20260610-1) 대시보드 홈(DashboardHome.tsx)에서 기존의 `/store/` 호출을 제거하고, 내 관리 기기 목록(`/kiosks/my`)을 Bento Grid 형태로 노출하도록 리팩토링 (404 index.html JSON '<' 파싱 에러 해결)
- `[x]` [Web] (20260610-1) 대시보드 홈 하단 기기 카드 클릭 시 활성 기기가 전환되며 새로고침하여 즉시 반영되는 스위칭 메커니즘 연동
- `[x]` [Web] (20260610-1) KioskManagement.tsx에서 DEV/HEAD 권한인 경우 매장이 없어도 상시 기기를 추가할 수 있게 하고, 목록에서 바로 삭제할 수 있도록 작업 열(삭제 버튼) 추가
- `[x]` [Web] (20260610-1) KioskDetail.tsx에서 매장 상세로 돌아가던 뒤로가기/삭제 경로를 모두 `/kiosks` 목록 화면으로 리다이렉트 처리
- `[x]` [Web] (20260610-1) KioskContext.tsx에서 불필요한 store_id 및 currentStoreId 속성 제거
- `[x]` [Web] (20260508-1) Vite Proxy(`vite.config.ts`) 적용 및 프론트엔드 API 호출 상대경로 리팩토링 완료
- `[x]` [Web] (20260508-1) React Router 기반 로그인 상태 확인 시 AuthContext 비동기 지연에 의한 튕김(Race Condition) 방어 처리 완료 (`isLoading` 동기 갱신)
- `[x]` [Web] (20260508-1) React Strict Mode에 의한 소셜 로그인 토큰 중복 발급 및 DB 에러 방지 처리 완료 (`useRef` 도입)
- `[x]` [Web] (20260508-2) 대시보드 헤더 레이아웃 개편 (로그아웃 우측 상단 이동, 내 정보 아이콘 추가, 로고 클릭 시 홈 이동)
- `[x]` [Web] (20260508-2) 내 정보(`ProfilePage`) 신설: 로그인 상태 뱃지, 개인정보 수정, 비밀번호 변경, 소셜 계정 분기처리
- `[x]` [Web] (20260508-2) 아이디 찾기(`FindIdPage`) 및 비밀번호 찾기(`FindPasswordPage`) 페이지 신설
- `[x]` [Web] (20260508-2) 비밀번호 복잡도 정규식 검사 (회원가입 + 비밀번호 변경)

---
*진행 방법:*
* `[ ]` : 대기 중
* `[/]` : 진행 중 (코딩 중)
* `[x]` : 완료
