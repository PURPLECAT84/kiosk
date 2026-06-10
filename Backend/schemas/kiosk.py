from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid

class KioskCreate(BaseModel):
    name: str
    model_name: str | None = None
    type: str = "Store" # Store / Restaurant
    status: str = "WAITING" # OPERATING / WAITING
    user_id: uuid.UUID

class KioskUpdate(BaseModel):
    name: str | None = None
    model_name: str | None = None
    status: str | None = None
    payment_status: str | None = None
    next_payment_date: datetime | None = None

class KioskResponse(BaseModel):
    id: uuid.UUID
    code: str
    user_id: uuid.UUID
    store_name: str | None = None # Joins store name for frontend display
    name: str
    model_name: str | None
    type: str
    status: str
    payment_status: str
    next_payment_date: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class KioskAdminResponse(BaseModel):
    user_id: uuid.UUID
    name: str
    email: str
    phone: str | None = None
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class KioskAdminCreate(BaseModel):
    email: str
    role: str = "STAFF"

class KioskAdminUpdate(BaseModel):
    role: str
