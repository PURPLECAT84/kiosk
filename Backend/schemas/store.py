from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid

class StoreCreate(BaseModel):
    name: str
    address: str
    type: str = "Store"
    owner_name: str | None = None

class StoreUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    type: str | None = None
    status: str | None = None
    owner_name: str | None = None

class StoreResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    address: str
    type: str
    owner_name: str | None
    status: str
    created_date: datetime
    kiosk_count: int = 0

    model_config = ConfigDict(from_attributes=True)