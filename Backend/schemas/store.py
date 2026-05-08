from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
import uuid

class StoreCreate(BaseModel):

    name : str
    address : str
    type : str | None = None



class StoreUpdate(BaseModel):

    name : str | None = None
    address : str | None = None
    type : str
    
class StoreResponse(BaseModel):

    id: uuid.UUID
    name : str
    address: str
    type : str
    created_date : datetime

    model_config = ConfigDict(from_attributes = True)