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
- `[x]` [Web] (20260508-1) Vite Proxy(`vite.config.ts`) 적용 및 프론트엔드 API 호출 상대경로 리팩토링 완료
- `[x]` [Web] (20260508-1) React Router 기반 로그인 상태 확인 시 AuthContext 비동기 지연에 의한 튕김(Race Condition) 방어 처리 완료 (`isLoading` 동기 갱신)
- `[x]` [Web] (20260508-1) React Strict Mode에 의한 소셜 로그인 토큰 중복 발급 및 DB 에러 방지 처리 완료 (`useRef` 도입)

---
*진행 방법:*
* `[ ]` : 대기 중
* `[/]` : 진행 중 (코딩 중)
* `[x]` : 완료
