from fastapi import APIRouter, Depends,HTTPException, status
from sqlalchemy.orm import Session
import httpx
import uuid
import base64

from database import get_db
from models.order import Order
from models.order_item import OrderItem
from models.product import Product
from core.security import TOSS_SECREET_KEY
from schemas.order import OrderCreate,OrderResponse
from schemas.order_item import OrderItemCreate,OrderItemResponse

router = APIRouter()


@router.post("/", response_model=OrderResponse)
async def create_order(
        order_data : OrderCreate,
        db : Session = Depends(get_db)
 ):
    
    # [1단계] 토스페이먼츠 결제 승인(Confirm) 요청
    # 토스는 시크릿 키 뒤에 콜론(:)을 붙이고 Base64로 인코딩한 값을 요구

    auth_string = f"{TOSS_SECREET_KEY}:"
    encode_auth = base64.b64encode(auth_string.encode()).decode() #???

    headers = {
        "Authorization" : f"Basic {encode_auth}",
        "Content-type" : "application/json"}
    
    toss_payload = {
        "paymentKey" : order_data.approval_code,
        "orderId" : str(uuid.uuid4()), #임시주문번호 (토스요청)
        "amount" : order_data.total_amount
    }
    # httpx를 써서 토스 서버에 승인 요청
    async with httpx.AsyncClient() as client :
        # 🚨 테스트 시에는 아래 3줄을 주석 처리 하거나, 토스 연동이 완료된 프론트가 있어야 진짜 작동합니다.
        # response = await client.post("https://api.tosspayments.com/v1/payments/confirm", json=toss_payload, headers=headers)
        # if response.status_code != 200:
        #     raise HTTPException(status_code=400, detail="토스 결제 승인 실패: " + response.text)
        print("토스 결제 승인 완료")
        # (임시) 스웨거에서 바로 테스트하기 위해 토스 결제가 무조건 성공했다고 칩니다! 

#[2단계] 영수증 머리말(Order) DB에 저장하기

    new_order = Order(
        store_id = order_data.store_id,
        total_amount = order_data.total_amount,
        payment_method = order_data.payment_method,
        payment_provider = order_data.payment_provider,
        approval_code = order_data.approval_code,

    )    

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

# [3단계] 장바구니 내용물(OrderItem) DB에 저장하기

    for item in order_data.items:
        product = db.get(Product, item.product_id)
        if not product : 
            raise HTTPException(status_code=404, detail=f"상품ID{item.product_id}를 찾을 수 없습니다")

        order_item = OrderItem(
            order_id=new_order.id, # 방금 위에서 만든 영수증 번호
            product_id=product.id,
            product_name=product.name,
            product_price=product.price,
            quantity=item.quantity
        )
    db.add(order_item)
    db.commit()
    db.refresh(new_order)

    return new_order
