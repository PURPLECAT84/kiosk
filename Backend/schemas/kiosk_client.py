from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid
from typing import List, Optional
from schemas.order import OrderCreate

class KioskProductResponse(BaseModel):
    id: uuid.UUID
    category_id: int
    name: str
    price: int
    image: str
    stock: int
    is_active: bool
    sequence: int
    status: str # ACTIVE / SOLDOUT

    model_config = ConfigDict(from_attributes=True)

class KioskCategoryResponse(BaseModel):
    id: int
    name: str
    sequence: int
    products: List[KioskProductResponse]

    model_config = ConfigDict(from_attributes=True)

class KioskSyncResponse(BaseModel):
    store_name: str
    categories: List[KioskCategoryResponse]

    model_config = ConfigDict(from_attributes=True)

class MockPaymentRequest(BaseModel):
    store_id: uuid.UUID
    total_amount: int
    payment_method: str
    payment_provider: str = "MockProvider"
    order_no: Optional[str] = None # 휴대폰 번호 등
    items: List[dict] # [{"product_id": uuid, "quantity": int}] 형태로 전달

class MockPaymentResponse(BaseModel):
    success: bool
    order_no: str
    approval_code: str
    total_amount: int
    created_at: datetime
