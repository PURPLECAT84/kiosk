# 포트원(PortOne) V2 결제창 연동 가이드 (Front-End & Kiosk Client)

본 문서는 MOKI 프로젝트의 키오스크 클라이언트 및 웹 프론트엔드에서 포트원 V2 SDK를 사용하여 오프라인/웹 결제창을 안전하게 호출하고, 백엔드와 연계하는 가장 보편적이고 안전한 가이드를 제공합니다.

---

## 1. 포트원 V2 브라우저 SDK 로드

가장 편리하고 보편적인 방법은 CDN을 통해 포트원 V2 SDK를 로드하는 것입니다.
HTML 파일의 `<head>` 태그 내에 아래의 스크립트를 추가합니다.

```html
<!-- 포트원 V2 전용 브라우저 SDK CDN -->
<script src="https://cdn.portone.io/v2/browser-sdk.js"></script>
```

만약 React/Vite 환경에서 모듈 방식으로 설치하여 사용하고 싶다면, npm 패키지를 이용할 수도 있습니다.
```bash
npm install @portone/browser-sdk
```

---

## 2. 결제창 호출 및 백엔드 연동 표준 코드 (React/JavaScript 예시)

사용자가 장바구니에서 [결제하기] 버튼을 누르면 아래의 2단계 프로세스가 실행됩니다.
1. **`PortOne.requestPayment()`**를 호출하여 카드/간편결제창을 띄우고 승인을 받습니다.
2. 결제 성공 시 포트원으로부터 전달받은 `paymentId`를 백엔드 **주문 생성 API (`POST /order/`)**에 주입하여 DB에 적재하고 검증을 완료합니다.

### 📝 React 결제 연동 컴포넌트 예시

```javascript
import React, { useState } from 'react';

// 포트원 V2 설정값
const PORTONE_STORE_ID = "store-7cb871e1-4629-4eee-a422-e4fd672636c9";
const PORTONE_CHANNEL_KEY = "YOUR_CHANNEL_KEY_HERE"; // 포트원 관리자 콘솔 -> 채널 관리에서 발급받은 채널 키

export function PaymentButton({ cartItems, totalAmount, kioskId, onPaymentSuccess, onPaymentFailure }) {
  const [isProcessing, setIsProcessing] = useState(false);

  const handlePayment = async () => {
    if (isProcessing) return;
    setIsProcessing(true);

    try {
      // 1. 고유 결제 식별 ID (paymentId) 생성
      // 결제 시도 시마다 고유해야 하므로 UUID 혹은 타임스탬프 결합형을 권장합니다.
      const paymentId = `pay_${Date.now()}_${Math.random().toString(36).substring(2, 10)}`;

      // 2. 포트원 결제창 호출
      // 글로벌 객체 'window.PortOne'을 사용합니다.
      const response = await window.PortOne.requestPayment({
        storeId: PORTONE_STORE_ID,
        channelKey: PORTONE_CHANNEL_KEY,
        paymentId: paymentId,
        orderName: cartItems.length > 1 
          ? `${cartItems[0].product_name} 외 ${cartItems.length - 1}건`
          : cartItems[0].product_name,
        totalAmount: totalAmount,
        currency: "CURRENCY_KRW",
        payMethod: "CARD", // 결제 수단 (CARD, EASY_PAY 등)
        // 모바일 환경에서의 리다이렉트 URL (웹뷰 대응 시 필요)
        redirectUrl: `${window.location.origin}/payment-callback`
      });

      // 3. 결제 창 닫힘 및 결과 분석
      // 포트원 V2 SDK는 에러가 없으면 무조건 결제 시도가 성공한 것입니다.
      // (만약 한도 초과, 잔액 부족 등으로 실패하면 response.code 에러가 담겨 옵니다.)
      if (response.code) {
        // 결제 실패 또는 취소
        throw new Error(`결제 실패: ${response.message}`);
      }

      // 4. 백엔드 주문 생성 및 결제 검증 API 호출
      // 결제창이 닫히고 나면, 즉시 백엔드에 결제 정보(paymentId)를 넘겨 이중 검증 및 영수증 적재를 마쳐야 합니다.
      const orderPayload = {
        kiosk_id: kioskId,
        total_amount: totalAmount,
        payment_method: "CARD",
        payment_provider: "PORTONE",
        approval_code: paymentId, // 🌟 백엔드 검증에 사용될 포트원의 paymentId를 전달합니다.
        items: cartItems.map(item => ({
          product_id: item.product_id,
          quantity: item.quantity
        }))
      };

      const backendResponse = await fetch('/order/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(orderPayload)
      });

      if (!backendResponse.ok) {
        const errorData = await backendResponse.json();
        throw new Error(errorData.detail || '주문 생성 및 결제 검증에 실패했습니다.');
      }

      const orderData = await backendResponse.json();
      
      // 최종 결제 및 주문 적재 완료 콜백 호출
      onPaymentSuccess(orderData);

    } catch (error) {
      console.error(error);
      onPaymentFailure(error.message);
      alert(error.message);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <button
      onClick={handlePayment}
      disabled={isProcessing || cartItems.length === 0}
      className="w-full bg-[#7C3AED] hover:bg-[#6D28D9] text-white py-4 rounded-2xl font-bold text-lg transition-all"
    >
      {isProcessing ? "결제 처리 중..." : `₩${totalAmount.toLocaleString()} 결제하기`}
    </button>
  );
}
```

---

## 3. Flutter (키오스크 클라이언트) 웹뷰 연동 방식

네이티브 Flutter 환경의 경우, `iamport_flutter` 패키지 또는 `webview_flutter`를 사용해 포트원 결제창을 처리하는 방법이 보편적입니다.
웹 뷰(Webview) 내부에서 위의 Javascript 코드가 실행되도록 감싸거나, 포트원 공식 Flutter 연동 라이브러리를 통해 결제 완료 콜백에서 `imp_uid` (V2의 `paymentId`에 대응)를 가로채어 백엔드 `POST /order/`로 REST 통신을 쏘는 구조를 구현하면 키오스크 기기에서도 완벽하게 동작합니다.
