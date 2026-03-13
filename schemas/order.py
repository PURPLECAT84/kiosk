from pydantic import BaseModel,ConfigDict
from datetime import datetime
import uuid
from typing import List

from schemas.order_item import OrderItemCreate, OrderItemResponse

class OrderCreate(BaseModel):

    store_id : uuid.UUID # 🔥 필수: 어느 매장의 결제인가?
    total_amount : int
    payment_method : str
    payment_provider : str
    approval_code : str
    status : str | None = None
    items : List[OrderItemCreate] # 🔥 필수: 뭘 샀는가? (콜라 2개 등)


class OrderResponse(BaseModel):

    id : int
    store_id : uuid.UUID
    total_amount : int
    payment_method : str
    payment_provider : str
    approval_code : str
    status : str | None = None
    created_date : datetime
    items : List[OrderItemResponse] # 영수증 상세 내역도 같이 보여주기

    model_config = ConfigDict(from_attributes = True)
