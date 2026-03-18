from fastapi import APIRouter, Depends,HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
import httpx
import uuid
import base64
from typing import List
from datetime import datetime, time

from database import get_db
from models.order import Order
from models.order_item import OrderItem
from models.product import Product
from core.security import TOSS_SECREET_KEY
from schemas.order import OrderCreate,OrderResponse
from schemas.order_item import OrderItemCreate,OrderItemResponse
from service.order_service import create_order_transaction

router = APIRouter()


@router.post("/", response_model=OrderResponse)
async def create_order(
        order_data: OrderCreate,
        db: Session = Depends(get_db)
):
    """
    [웨이터] 프론트엔드에서 결제 요청을 받아 요리사(Service)에게 전달합니다.
    """
    # 50줄이 넘던 코드가 단 2줄로 줄어들었습니다!
    new_order = await create_order_transaction(db, order_data)
    return new_order


@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    store_id : uuid.UUID,
    start_date : datetime | None = None,
    end_date : datetime | None = None,
    db : Session = Depends(get_db)
):
    stmt = select(Order).where(Order.store_id == store_id)

    if start_date:
        stmt = stmt.where(Order.created_date >=start_date)
    
    if end_date:
        # 프론트가 00:00:00으로 보낸 시간을 그날의 끝(23:59:59.999999)으로 꽉 채워줌
        end_date_max = datetime.combine(end_date.date(), time.max)
        stmt = stmt.where(Order.created_date <= end_date_max)
    
    
    stmt = stmt.order_by(desc(Order.created_date))

    orders = db.scalars(stmt).all()

    return orders


@router.delete("/{order_id}", response_model=OrderResponse)
async def delete_orders(
    order_id: int,
    db : Session = Depends(get_db)
):

    order = db.get(Order, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="해당 주문 내역을 찾을 수 없습니다.")
    
    if order.status == "REFUNDED":
        raise HTTPException(status_code=400, detail="이미 취소(환불) 처리된 주문입니다.")
    
    order.status = "REFUNDED"

    db.commit()
    db.refresh(order)

    return order