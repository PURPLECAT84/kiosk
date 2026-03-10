from pydantic import BaseModel,ConfigDict
from datetime import datetime
import uuid


class OrderItemCreate(BaseModel):
    product_id : uuid.UUID
    quantity : int

class OrderItemResponse(BaseModel):
    product_name : str
    product_price: int
    quantity : int

    model_config = ConfigDict(from_attributes=True)