# Backend/service/portone_service.py
import httpx
import logging
from typing import Dict, Any, Optional
from core.security import PORTONE_API_SECRET, PORTONE_API_URL

# 포트원 연동 관련 로그를 기록하기 위한 로거 객체를 설정합니다.
logger = logging.getLogger("portone_service")

async def verify_portone_payment(payment_id: str, expected_amount: int) -> Dict[str, Any]:
    """
    [초보자 가이드 - 결제 검증(Verification)]
    사용자가 클라이언트(키오스크/웹)에서 결제를 완료하면, 해당 결제가 위변조되지 않았는지
    백엔드에서 포트원 API 서버에 직접 물어보고 결제금액과 상태가 유효한지 2차 검증을 수행합니다.
    
    :param payment_id: 포트원에서 발급한 결제 고유 식별자
    :param expected_amount: DB에 기록될 실제 주문 총금액
    :return: 검증 완료된 결제 정보 딕셔너리
    :raises ValueError: 결제 정보 불일치 혹은 유효하지 않은 결제 상태일 때 예외 발생
    """
    # 1. 테스트 모드 판별
    # API Secret이 없거나, 기본 테스트 비밀키인 경우, 혹은 결제 ID가 "test_"로 시작하는 경우 
    # 포트원 서버로 실요청을 보내지 않고 로컬 모의(Mock) 검증 결과로 자동 통과시킵니다.
    if not PORTONE_API_SECRET or PORTONE_API_SECRET == "test_portone_secret" or payment_id.startswith("test_"):
        logger.info(f"[Mock] 포트원 V2 결제 검증 성공 처리 (Mock): ID={payment_id}, 금액={expected_amount}원")
        
        # 가상계좌(READY) 상태 시뮬레이션용 결제 ID 처리
        status = "READY" if "ready" in payment_id.lower() else "PAID"
        
        return {
            "payment_id": payment_id,
            "status": status,
            "amount": expected_amount,
            "payment_method": "CARD",
            "payment_provider": "PORTONE",
            "approval_code": f"MOCK_APP_{payment_id[:6]}"
        }

    # 2. 포트원 V2 API 호출 헤더 구성
    # 포트원 V2는 별도의 인증 토큰 발급 프로세스 없이, Authorization 헤더에 "PortOne {API_SECRET}" 포맷으로 인증합니다.
    url = f"{PORTONE_API_URL}/payments/{payment_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"PortOne {PORTONE_API_SECRET}"
    }

    try:
        async with httpx.AsyncClient() as client:
            # 비동기 HTTP GET 요청을 포트원 서버로 보냅니다. (타임아웃 10초 적용)
            response = await client.get(url, headers=headers, timeout=10.0)
            
        if response.status_code != 200:
            logger.error(f"포트원 결제 단건 조회 실패: HTTP {response.status_code} - {response.text}")
            raise ValueError(f"포트원 결제 내역 조회에 실패했습니다. (HTTP {response.status_code})")
        
        payment_data = response.json()
        
        # 3. 결제 금액 및 상태 검증
        # 포트원 V2 API 응답 스키마 상, 총 결제 금액은 'amount.total'에 위치합니다.
        # 결제 상태는 'status' 필드에 위치합니다. (예: PAID, CANCELLED, READY, FAILED)
        actual_status = payment_data.get("status")
        amount_info = payment_data.get("amount", {})
        actual_amount = amount_info.get("total", 0)

        # 3-1. 가상계좌 입금 대기 상태(READY) 예외 허용 처리
        # 가상계좌(Virtual Account)의 경우 입금 전까지는 READY 상태이므로 결제 완료로 즉시 취급하지 않고 READY를 반환합니다.
        if actual_status not in ["PAID", "READY"]:
            raise ValueError(f"결제가 성공 상태가 아닙니다. (현재 상태: {actual_status})")

        # 3-2. 결제 금액 변조 대조 검증
        if actual_amount != expected_amount:
            logger.error(f"결제 금액 불일치 위변조 의심! 요청 금액: {expected_amount}원, 실제 결제액: {actual_amount}원")
            raise ValueError("결제 요청 금액과 포트원 실제 결제 승인 금액이 일치하지 않습니다.")

        # 결제 수단 및 대행사 파싱
        # V2 응답의 paymentMethod 및 paymentProvider 필드를 참고합니다.
        method = payment_data.get("method", {}).get("type", "CARD")
        provider = payment_data.get("method", {}).get("provider", "UNKNOWN")
        
        # 신용카드 등 승인 번호는 내장 객체에서 추출합니다.
        approval_code = payment_data.get("transaction", {}).get("approvalCode", f"PORTONE_{payment_id[:6]}")

        logger.info(f"포트원 V2 결제 검증 통과: ID={payment_id}, 상태={actual_status}, 금액={actual_amount}원")
        return {
            "payment_id": payment_id,
            "status": actual_status,
            "amount": actual_amount,
            "payment_method": method,
            "payment_provider": provider,
            "approval_code": approval_code
        }

    except Exception as e:
        logger.error(f"포트원 V2 결제 검증 연동 중 에러 발생: {str(e)}")
        raise ValueError(f"결제 검증 오류: {str(e)}")


async def cancel_portone_payment(payment_id: str, amount: int, reason: str) -> bool:
    """
    [초보자 가이드 - 결제 취소 (환불)]
    점주가 주문을 취소하거나, DB 적재 실패 등으로 결제를 자동 취소해야 할 때 포트원 API 서버에 취소 요청을 전송합니다.
    
    :param payment_id: 취소할 포트원 결제 고유 식별자
    :param amount: 취소할 금액
    :param reason: 취소 사유
    :return: 취소 성공 여부 (True / False)
    """
    # 1. 테스트 모드 판별
    if not PORTONE_API_SECRET or PORTONE_API_SECRET == "test_portone_secret" or payment_id.startswith("test_"):
        logger.info(f"[Mock] 포트원 V2 결제 취소 성공 처리 (Mock): ID={payment_id}, 취소금액={amount}원, 사유={reason}")
        return True

    # 2. 포트원 V2 API 취소 엔드포인트 호출
    url = f"{PORTONE_API_URL}/payments/{payment_id}/cancel"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"PortOne {PORTONE_API_SECRET}"
    }
    # V2 취소 명세에 따른 바디 데이터 구성
    payload = {
        "reason": reason,
        "amount": amount
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)

        if response.status_code == 200:
            logger.info(f"포트원 V2 결제 취소 요청 성공: ID={payment_id}, 취소금액={amount}원")
            return True
        else:
            logger.error(f"포트원 V2 결제 취소 실패: HTTP {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"포트원 V2 결제 취소 연동 중 예외 발생: {str(e)}")
        return False
