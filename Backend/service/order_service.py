# Backend/service/order_service.py
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException
import uuid
from datetime import datetime
import logging
import asyncio

from models.order import Order
from models.order_item import OrderItem
from models.product import Product
from schemas.order import OrderCreate
from service.portone_service import verify_portone_payment, cancel_portone_payment

logger = logging.getLogger("order_service")
alimtalk_logger = logging.getLogger("alimtalk_service")

async def send_order_complete_notification(phone: str, total_amount: int) -> bool:
    """
    [초보자 가이드 - 비동기 알림 전송]
    실제 운영 모드에서는 알리고 또는 포트원 알림톡 API를 호출합니다.
    테스트 환경에서는 백그라운드로 성공 로그만 남깁니다.
    """
    alimtalk_logger.info(f"카카오 알림톡 전송 완료 -> 수신번호: {phone}, 내용: [MOKI] 주문이 접수되었습니다. 결제금액: {total_amount}원")
    return True

async def create_order_transaction(db: Session, order_data: OrderCreate) -> Order:
    """
    [초보자 가이드 - 다중 주문 DB 적재 및 결제 통합 트랜잭션]
    결제 검증 -> DB 적재 & 재고 차감 -> DB 커밋의 3단계 파이프라인으로 구성되어 있습니다.
    도중에 한 단계라도 실패 시, DB 롤백 및 결제 자동 취소(보상 트랜잭션)를 실행하여 원자성을 완벽히 보장합니다.
    """
    verified_payment = None
    try:
        # [0단계] 키오스크 정보 조회
        from models.kiosk import Kiosk
        import random
        
        kiosk = db.get(Kiosk, order_data.kiosk_id)
        if not kiosk:
            raise HTTPException(status_code=404, detail="키오스크를 찾을 수 없습니다.")

        # [1단계] 포트원 V2 결제 검증 (결제액 변조 방지)
        # 클라이언트가 전달한 approval_code 필드를 포트원의 payment_id로 취급하여 이중 검증합니다.
        # 점주(MANAGER)가 소유한 가맹점 채널 식별값을 동적으로 넘깁니다.
        payment_id = order_data.approval_code
        store_id = getattr(kiosk.owner, "portone_store_id", None)
        channel_key = getattr(kiosk.owner, "portone_channel_key", None)
        
        verified_payment = await verify_portone_payment(
            payment_id=payment_id,
            expected_amount=order_data.total_amount,
            store_id=store_id,
            channel_key=channel_key
        )

        # [2단계] 주문번호(order_no) 결정 로직
        order_no = None
        if kiosk.type == "Restaurant" and order_data.order_no:
            # 외식형(Restaurant) 주문의 경우 입력받은 고객 연락처(010...)를 하이픈 제외 숫자로 적재
            digits = "".join(c for c in order_data.order_no if c.isdigit())
            if len(digits) >= 10:
                order_no = digits
                
        if not order_no:
            # 일반 판매형(Store) 또는 연락처 미입력 시: YYMMDD + 6자리 랜덤 숫자
            current_date = datetime.now().strftime("%y%m%d")
            random_digits = "".join(random.choice("0123456789") for _ in range(6))
            order_no = current_date + random_digits

        # [3단계] 영수증(Order) 뼈대 생성 및 flush() 호출
        # flush()를 호출하면 DB에 실제로 커밋하기 전, 임시 상태로 DB에 반영되어 generated primary key(Order.id)를 미리 받아올 수 있습니다.
        initial_status = "Preparing" if kiosk.type == "Restaurant" else "Completed"
        
        # 가상계좌(READY) 상태인 경우 주문 상태도 입금 대기("Pending") 상태로 지정합니다.
        if verified_payment["status"] == "READY":
            initial_status = "Pending"

        new_order = Order(
            order_no=order_no,
            kiosk_id=order_data.kiosk_id,
            total_amount=order_data.total_amount,
            # 검증 완료된 안전한 포트원 실제 결제 수단 및 대행사 정보를 사용합니다.
            payment_method=verified_payment["payment_method"],
            payment_provider=verified_payment["payment_provider"],
            approval_code=payment_id,
            status=initial_status,
        )
        db.add(new_order)
        db.flush() 

        # [4단계] 장바구니 품목 DB 적재 및 비관적 락(SELECT FOR UPDATE)을 통한 재고 검증/차감
        for item in order_data.items:
            # 동시성 재고 선점을 방지하기 위해 with_for_update()를 사용해 쓰기 락을 획득합니다.
            stmt = select(Product).where(Product.id == item.product_id).with_for_update()
            product = db.execute(stmt).scalar_one_or_none()
            
            if not product: 
                raise HTTPException(status_code=404, detail=f"상품ID {item.product_id}를 찾을 수 없습니다.")

            # 점주가 판매 중지 처리한 상품인지 검사
            if not product.is_active:
                raise HTTPException(status_code=400, detail=f"[{product.name}] 상품은 현재 판매가 중단되었습니다.")
            
            # 유통기한 경과 여부 체크
            if product.expiration_date and product.expiration_date < datetime.now():
                product.is_active = False # 시간이 지났으므로 영구 미판매 처리!
                raise HTTPException(status_code=400, detail=f"[{product.name}] 상품은 판매 기한이 만료되었습니다.")
            
            # 재고 수량 차감 검증
            if getattr(product, "stock_managed", True):
                if product.stock < item.quantity:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"[{product.name}] 재고가 부족합니다. (남은 수량: {product.stock}개)"
                    )

                # 재고 수량 차감 적용
                product.stock -= item.quantity
                
                # 재고가 소진된 경우 품절(비활성화) 처리
                if product.stock == 0:
                    product.is_active = False

            # 개별 장바구니 항목 생성 및 연결
            order_item = OrderItem(
                order_id=new_order.id, 
                product_id=product.id,
                product_name=product.name,
                product_price=product.price,
                quantity=item.quantity
            )
            db.add(order_item)

        # 5단계: 트랜잭션 최종 확정!
        db.commit()
        db.refresh(new_order)

        # 6단계: 알림톡 백그라운드 발송 (휴대폰 번호 주문 시에만)
        if new_order.order_no and new_order.order_no.startswith("010") and len(new_order.order_no) in [10, 11]:
            # 가상계좌 입금 대기 상태인 경우 입금 안내 알림톡을 발송하게 고도화할 수도 있습니다.
            asyncio.create_task(send_order_complete_notification(new_order.order_no, new_order.total_amount))

        return new_order

    except Exception as e:
        # [예외 단계] 트랜잭션 롤백 및 보상 트랜잭션(결제 자동 취소) 처리
        # DB 작업을 롤백하여 재고 복구 및 영수증 등록을 원복합니다.
        db.rollback()
        
        # 만약 포트원에서 실제 결제 승인이 완료(PAID)되었고, DB 트랜잭션 도중 예외가 터졌다면
        # 사용자에게 청구된 금액을 자동으로 환불(보상 트랜잭션)하여 금전적 피해를 원천 차단합니다.
        if verified_payment and verified_payment.get("status") == "PAID":
            payment_id = order_data.approval_code
            logger.warning(
                f"[보상 트랜잭션 실행] DB 적재 중 예외 발생하여 포트원 결제를 자동 취소합니다. "
                f"결제 ID: {payment_id}, 취소 대상 금액: {order_data.total_amount}원, 원인: {str(e)}"
            )
            # 포트원 API를 통해 점주의 PG 채널로 취소 요청을 발송합니다.
            cancel_success = await cancel_portone_payment(
                payment_id=payment_id,
                amount=order_data.total_amount,
                reason="주문 DB 적재 실패로 인한 자동 환불",
                store_id=store_id,
                channel_key=channel_key
            )
            if not cancel_success:
                logger.error(f"[보상 트랜잭션 실패] 결제 ID {payment_id} 환불 요청이 실패했습니다. 점주 수동 개입 필요!")

        # 예외를 다시 던져 FastAPI가 클라이언트에게 에러 코드를 전송하도록 처리합니다.
        raise e