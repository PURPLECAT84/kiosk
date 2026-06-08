from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid
from typing import List, Optional

from schemas.order_item import OrderItemCreate, OrderItemResponse

class OrderCreate(BaseModel):
    store_id: uuid.UUID # 필수: 어느 매장의 결제인가?
    total_amount: int
    payment_method: str
    payment_provider: str
    approval_code: str
    status: str | None = None
    order_no: Optional[str] = None # 고객이 입력한 전화번호 또는 커스텀 주문번호
    items: List[OrderItemCreate] # 필수: 뭘 샀는가? (콜라 2개 등)

class OrderResponse(BaseModel):
    id: int
    order_no: Optional[str] = None
    store_id: uuid.UUID
    total_amount: int
    payment_method: str
    payment_provider: str
    approval_code: str
    status: str | None = None
    created_date: datetime
    items: List[OrderItemResponse] # 영수증 상세 내역도 같이 보여주기
    refund_amount: Optional[int] = None
    refund_reason: Optional[str] = None
    refund_method: Optional[str] = None
    refunded_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OrderRefundRequest(BaseModel):
    refund_amount: int
    refund_reason: str
    refund_method: str

