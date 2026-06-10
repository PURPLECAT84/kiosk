from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid
from typing import Optional, List

class ProductCreate(BaseModel):
    category_id: int
    barcode: Optional[str] = None
    name: str
    price: int
    image: str
    stock: int = 0
    stock_managed: bool = True
    sequence: int = 0
    kiosk_id: Optional[uuid.UUID] = None

class ProductUpdate(BaseModel):
    category_id: Optional[int] = None
    barcode: Optional[str] = None
    name: Optional[str] = None
    price: Optional[int] = None
    image: Optional[str] = None
    stock: Optional[int] = None
    stock_managed: Optional[bool] = None
    sequence: Optional[int] = None
    is_active: Optional[bool] = None
    kiosk_id: Optional[uuid.UUID] = None

class ProductResponse(BaseModel):
    id: uuid.UUID
    kiosk_id: uuid.UUID
    shelve_id: uuid.UUID
    category_id: int
    barcode: Optional[str] = None
    name: str
    price: int
    created_date: datetime
    image: str
    stock: int
    stock_managed: bool
    is_active: bool
    sequence: int

    model_config = ConfigDict(from_attributes=True)

class ProductStatusUpdate(BaseModel):
    stock: Optional[int] = None
    is_active: Optional[bool] = None
    expiration_date: Optional[datetime] = None
    stock_managed: Optional[bool] = None

class BulkStatusUpdate(BaseModel):
    product_ids: List[uuid.UUID]
    is_active: bool

class BulkDelete(BaseModel):
    product_ids: List[uuid.UUID]