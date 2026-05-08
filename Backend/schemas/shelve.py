from pydantic import BaseModel,ConfigDict
import uuid

class ShelveCreate(BaseModel):

    name : str
    terminal_id : str
    business_number : str 
    vender_code : str 

class ShelveUpdate(BaseModel):

    name : str | None = None
    terminal_id : str | None = None
    business_number : str | None = None 
    vender_code : str | None = None

class ShelveResponse(BaseModel):

    id: uuid.UUID
    store_id : uuid.UUID
    name : str
    terminal_id : str
    business_number : str
    vender_code : str

    model_config = ConfigDict(from_attributes = True)