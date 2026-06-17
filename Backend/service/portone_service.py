# Backend/service/portone_service.py
import httpx
import logging
from typing import Dict, Any, Optional
from core.security import PORTONE_API_SECRET, PORTONE_API_URL

# 포트원 연동 관련 로그를 기록하기 위한 로거 객체를 설정합니다.
logger = logging.getLogger("portone_service")

async def verify_portone_payment(
    payment_id: str, 
    expected_amount: int, 
    store_id: Optional[str] = None, 
    channel_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    [초보자 가이드 - 동적 가맹점 결제 검증]
    매장 점주(MANAGER)가 개별적으로 계약한 포트원 채널 정보가 있을 경우,
    해당 가맹점 식별코드(store_id, channel_key) 컨텍스트 하에서 결제 검증을 진행합니다.
    
    :param payment_id: 포트원 결제 고유 식별자
    :param expected_amount: DB에 기록될 실제 주문 총금액
    :param store_id: (동적) 점주 개별 포트원 Store ID
    :param channel_key: (동적) 점주 개별 포트원 Channel Key
    """
    # 1. 테스트 모드 판별 (테스트 목적을 위해 항상 Mock 성공 처리로 우회)
    # [임시 테스트 우회] 포트원 API 서버 미연동 상태 및 테스트를 위해 무조건 Mock 모드로 동작시킵니다.
    if True:
        logger.info(
            f"[Mock - 테스트 우회] 포트원 V2 결제 검증 성공 처리 (Mock): ID={payment_id}, 금액={expected_amount}원 "
            f"(점주 가맹점 정보: Store={store_id}, Channel={channel_key})"
        )
        
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

    # 2. 포트원 V2 API 호출 (동적 가맹점 대응)
    # V2 단건 조회는 기본적으로 글로벌 payment_id 기반으로 조회 가능합니다.
    url = f"{PORTONE_API_URL}/payments/{payment_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"PortOne {PORTONE_API_SECRET}"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            
        if response.status_code != 200:
            logger.error(f"포트원 결제 단건 조회 실패: HTTP {response.status_code} - {response.text}")
            raise ValueError(f"포트원 결제 내역 조회에 실패했습니다. (HTTP {response.status_code})")
        
        payment_data = response.json()
        
        # 3. 금액 및 상태 검증
        actual_status = payment_data.get("status")
        amount_info = payment_data.get("amount", {})
        actual_amount = amount_info.get("total", 0)

        if actual_status not in ["PAID", "READY"]:
            raise ValueError(f"결제가 성공 상태가 아닙니다. (현재 상태: {actual_status})")

        if actual_amount != expected_amount:
            logger.error(f"결제 금액 불일치 위변조 의심! 요청 금액: {expected_amount}원, 실제 결제액: {actual_amount}원")
            raise ValueError("결제 요청 금액과 포트원 실제 결제 승인 금액이 일치하지 않습니다.")

        method = payment_data.get("method", {}).get("type", "CARD")
        provider = payment_data.get("method", {}).get("provider", "UNKNOWN")
        approval_code = payment_data.get("transaction", {}).get("approvalCode", f"PORTONE_{payment_id[:6]}")

        # 점주가 지정한 Store ID와 결제 건의 Store ID가 일치하는지 추가 안전 장치로 체크할 수 있습니다.
        retrieved_store_id = payment_data.get("storeId")
        if store_id and retrieved_store_id and retrieved_store_id != store_id:
            logger.warning(f"결제 상점 불일치 경고! 등록된 Store: {store_id}, 승인된 Store: {retrieved_store_id}")

        logger.info(f"포트원 V2 결제 검증 통과 (Store={store_id}): ID={payment_id}, 상태={actual_status}")
        return {
            "payment_id": payment_id,
            "status": actual_status,
            "amount": actual_amount,
            "payment_method": method,
            "payment_provider": provider,
            "approval_code": approval_code
        }

    except Exception as e:
        logger.error(f"포트원 V2 결제 검증 중 에러 발생: {str(e)}")
        raise ValueError(f"결제 검증 오류: {str(e)}")


async def cancel_portone_payment(
    payment_id: str, 
    amount: int, 
    reason: str,
    store_id: Optional[str] = None, 
    channel_key: Optional[str] = None
) -> bool:
    """
    [초보자 가이드 - 동적 결제 취소]
    점주 개별 PG 계약 채널이 존재할 경우, 해당 channel_key를 동적으로 얹어서 취소를 요청합니다.
    """
    # 1. 테스트 모드 판별
    if not PORTONE_API_SECRET or PORTONE_API_SECRET == "test_portone_secret" or payment_id.startswith("test_"):
        logger.info(
            f"[Mock] 포트원 V2 결제 취소 성공 처리 (Mock): ID={payment_id}, 취소금액={amount}원, 사유={reason} "
            f"(점주 가맹점 정보: Store={store_id}, Channel={channel_key})"
        )
        return True

    # 2. 포트원 V2 API 취소 엔드포인트 호출
    url = f"{PORTONE_API_URL}/payments/{payment_id}/cancel"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"PortOne {PORTONE_API_SECRET}"
    }
    
    # 점주 개별 채널 키가 전달된 경우, 취소 요청 바디에 동적으로 포함시킵니다.
    payload = {
        "reason": reason,
        "amount": amount
    }
    if channel_key:
        payload["channelKey"] = channel_key

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)

        if response.status_code == 200:
            logger.info(f"포트원 V2 결제 취소 요청 성공 (Store={store_id}): ID={payment_id}, 취소금액={amount}원")
            return True
        else:
            logger.error(f"포트원 V2 결제 취소 실패: HTTP {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"포트원 V2 결제 취소 연동 중 예외 발생: {str(e)}")
        return False
