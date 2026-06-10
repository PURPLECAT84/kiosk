from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid
from typing import List, Optional

from schemas.order_item import OrderItemCreate, OrderItemResponse

class OrderCreate(BaseModel):
    kiosk_id: uuid.UUID
    total_amount: int
    payment_method: str
    payment_provider: str
    approval_code: str
    status: str | None = None
    order_no: Optional[str] = None
    items: List[OrderItemCreate]

class OrderResponse(BaseModel):
    id: int
    order_no: Optional[str] = None
    kiosk_id: uuid.UUID
    total_amount: int
    payment_method: str
    payment_provider: str
    approval_code: str
    status: str | None = None
    created_date: datetime
    items: List[OrderItemResponse]
    refund_amount: Optional[int] = None
    refund_reason: Optional[str] = None
    refund_method: Optional[str] = None
    refunded_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OrderRefundRequest(BaseModel):
    refund_amount: int
    refund_reason: str
    refund_method: str

