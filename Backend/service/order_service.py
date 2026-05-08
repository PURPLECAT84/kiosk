# services/order_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException
import httpx
import uuid
import base64
from datetime import datetime

from models.order import Order
from models.order_item import OrderItem
from models.product import Product
from schemas.order import OrderCreate
from core.security import TOSS_SECRET_KEY

async def create_order_transaction(db: Session, order_data: OrderCreate) -> Order:
    """
    [요리사] 결제 승인 및 DB 저장(영수증+장바구니) 트랜잭션을 한 번에 처리합니다.
    """
    # [1단계] 토스페이먼츠 결제 승인 (Mock)
    auth_string = f"{TOSS_SECRET_KEY}:"
    encode_auth = base64.b64encode(auth_string.encode()).decode()
    headers = {
        "Authorization" : f"Basic {encode_auth}",
        "Content-type" : "application/json"
    }
    toss_payload = {
        "paymentKey" : order_data.approval_code,
        "orderId" : str(uuid.uuid4()), 
        "amount" : order_data.total_amount
    }
    
    async with httpx.AsyncClient() as client:
        # 실제 연동 시 주석 해제하여 사용
        print("토스 결제 승인 완료")

    try:
        # [2단계] 영수증(Order) 뼈대 만들기
        new_order = Order(
            store_id=order_data.store_id,
            total_amount=order_data.total_amount,
            payment_method=order_data.payment_method,
            payment_provider=order_data.payment_provider,
            approval_code=order_data.approval_code,
        )
        db.add(new_order)
        # 🔥 commit() 대신 flush()를 씁니다!
        # 확정(commit) 짓기 전에 임시로 DB에 밀어 넣어서 주문번호(new_order.id)만 빠르게 받아옵니다.
        db.flush() 

        # [3단계] 장바구니 내용물(OrderItem) 달아주기 & 🔥 재고 검증/차감
        for item in order_data.items:
            product = db.get(Product, item.product_id)
            if not product: 
                raise HTTPException(status_code=404, detail=f"상품ID {item.product_id}를 찾을 수 없습니다")

            # 🔥 [요구사항 2] 사장님이 강제로 미판매 처리한 상품인가?
            if not product.is_active:
                raise HTTPException(status_code=400, detail=f"[{product.name}] 상품은 현재 판매가 중단되었습니다.")
            
            # 🔥 [요구사항 3] 유통기한이 지났는가? (Lazy Check)
            if product.expiration_date and product.expiration_date < datetime.now():
                product.is_active = False # 시간이 지났으므로 영구 미판매 처리!
                raise HTTPException(status_code=400, detail=f"[{product.name}] 상품은 판매 기한이 만료되었습니다.")
            
            # 🔥 재고가 충분한가?
            if product.stock < item.quantity:
                raise HTTPException(status_code=400, detail=f"[{product.name}] 재고가 부족합니다. (남은 수량: {product.stock}개)")

            # ✅ 모든 검사를 통과했다면 재고를 깎습니다!
            product.stock -= item.quantity
            
            # (옵션) 만약 재고가 0이 되었다면 자동으로 미판매 처리!
            if product.stock == 0:
                product.is_active = False

            # 장바구니에 담기
            order_item = OrderItem(
                order_id=new_order.id, 
                product_id=product.id,
                product_name=product.name,
                product_price=product.price,
                quantity=item.quantity
            )
            db.add(order_item)

        # 4단계: 영수증과 장바구니를 한 번에 도장 쾅! (에러 없으면 최종 확정)
        db.commit()
        db.refresh(new_order)
        return new_order

    except Exception as e:
        # 중간에 하나라도 에러가 나면, 영수증이든 장바구니든 다 취소(Rollback)합니다!
        db.rollback()
        raise e