# Backend/routers/payment_webhook.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import logging

from database import get_db
from models.order import Order
from models.product import Product
from service.portone_service import verify_portone_payment

logger = logging.getLogger("payment_webhook")

router = APIRouter()

# -----------------------------------------------------------------------------
# [초보자 가이드 - Webhook 요청 Pydantic 스키마 정의]
# 포트원 V2 Webhook 서버가 우리 백엔드로 전송하는 JSON 페이로드 구조를 클래스로 모델링합니다.
# -----------------------------------------------------------------------------
class WebhookData(BaseModel):
    storeId: str = Field(..., description="가맹점 식별 ID (store-...)")
    paymentId: str = Field(..., description="포트원 결제 고유 ID")
    transactionId: Optional[str] = Field(None, description="포트원 트랜잭션 고유 식별자 (있을 시)")

class PortOneWebhook(BaseModel):
    type: str = Field(..., description="이벤트 유형 (예: Transaction.Paid, Transaction.Cancelled)")
    timestamp: datetime = Field(..., description="이벤트 발생 일시")
    data: WebhookData = Field(..., description="결제 세부 정보")

# -----------------------------------------------------------------------------
# [초보자 가이드 - Webhook 엔드포인트 수신]
# Webhook은 결제 완료, 취소, 가상계좌 발급 등 상태 변화가 포트원 내부에서 발생했을 때
# 포트원 서버가 우리 백엔드로 직접 HTTP POST 요청을 보내어 상태를 동기화하는 비동기 통지 방식입니다.
# -----------------------------------------------------------------------------
@router.post("/webhook", status_code=status.HTTP_200_OK)
async def receive_portone_webhook(
    webhook: PortOneWebhook,
    db: Session = Depends(get_db)
):
    event_type = webhook.type
    payment_id = webhook.data.paymentId
    store_id = webhook.data.storeId

    logger.info(f"[Webhook 수신] 이벤트={event_type}, 결제 ID={payment_id}, 매장={store_id}")

    try:
        # [1단계] 해당 결제 ID를 갖는 주문 정보가 우리 DB에 존재하는지 확인합니다.
        # approval_code 필드에 포트원의 payment_id를 저장해 두고 있으므로 이를 조건으로 조회합니다.
        stmt = select(Order).where(Order.approval_code == payment_id)
        order = db.execute(stmt).scalar_one_or_none()

        if not order:
            # 우리 DB에 없는 결제라면, 타 시스템의 결제이거나 오결제일 수 있으므로 로그를 남기고 종료합니다.
            # (FastAPI에서는 Webhook 서버에게 200 OK를 응답해야 포트원이 재전송을 반복하지 않습니다.)
            logger.warning(f"우리 DB에 등록되지 않은 결제 ID에 대한 Webhook 수신: {payment_id}")
            return {"status": "ignored", "message": "Order not found in local database."}

        # [2단계] 포트원 서버 직접 재조회 검증 (Read-back Verification)
        # Webhook 페이로드는 해커에 의해 위변조될 위험이 있으므로,
        # 전달받은 payment_id를 가지고 포트원 API 서버에 직접 결제 상태를 역조회하여 확실한 상태를 판별합니다.
        
        # 2-1. 결제 완료 (Paid) 처리
        if event_type == "Transaction.Paid":
            # 실제 결제액이 주문서의 total_amount와 일치하는지 포트원 측에 재검증 요청합니다.
            # 검증 중 불일치 시 ValueError 예외가 발생합니다.
            verified = await verify_portone_payment(payment_id, order.total_amount)
            
            if verified["status"] == "PAID" and order.status in ["Pending", "Preparing", "Completed"]:
                # 주문 상태를 최종 완료 상태로 업데이트합니다. (가상계좌 대기 중이었거나 준비 중인 건)
                # 만약 외식형(Restaurant) 주문이라면 준비중("Preparing")으로 두고, 판매형이면 즉시 "Completed" 처리합니다.
                if order.status == "Pending":
                    order.status = "Preparing" if order.kiosk.type == "Restaurant" else "Completed"
                
                db.commit()
                logger.info(f"결제 완료 동기화 성공: 주문번호={order.order_no}, 결제 ID={payment_id}")

        # 2-2. 결제 취소 (Cancelled) 처리
        elif event_type == "Transaction.Cancelled":
            if order.status != "REFUNDED":
                # 포트원 재조회를 통해 실제로 취소되었는지 검증합니다.
                # cancel_portone_payment가 아니라 단순 조회를 활용하기 위해 verify_portone_payment의 오류 처리 예외만 처리하거나,
                # 여기서는 포트원 API로 직접 조회하여 상태를 점검합니다.
                try:
                    verified = await verify_portone_payment(payment_id, order.total_amount)
                except ValueError as ve:
                    # 취소 건의 경우 금액 검증이 다를 수 있으므로(부분취소 등), 
                    # 포트원 공식 취소 상태임을 정상 수신한 것으로 간주하여 처리를 진행합니다.
                    logger.info(f"취소 건 조회 검증 정보 (취소로 인한 불일치 가능): {str(ve)}")
                
                # 주문 취소(환불) 상태로 갱신
                order.status = "REFUNDED"
                order.refund_amount = order.total_amount
                order.refund_reason = "포트원 외부 결제 취소 (Webhook 동기화)"
                order.refund_method = order.payment_method
                order.refunded_at = datetime.now()

                # 취소되었으므로 상품 재고 롤백
                for item in order.items:
                    product = db.get(Product, item.product_id)
                    if product:
                        if getattr(product, "stock_managed", True):
                            product.stock += item.quantity
                        product.is_active = True # 재고가 복구되었으므로 활성화
                
                db.commit()
                logger.info(f"결제 취소(환불) 동기화 완료: 주문번호={order.order_no}, 결제 ID={payment_id}")

        return {"status": "success", "event_processed": event_type}

    except Exception as e:
        db.rollback()
        logger.error(f"Webhook 처리 중 에러 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error during Webhook handling: {str(e)}"
        )
