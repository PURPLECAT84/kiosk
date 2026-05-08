from pydantic import BaseModel,ConfigDict
import uuid

class CategoryCreate(BaseModel):
    
    name : str
    shelve_id : uuid.UUID

class CategoryUpdate(BaseModel):

    name : str | None = None

class CategoryResponse(BaseModel):

    id : int
    name : str
    shelve_id : uuid.UUID
    store_id : uuid.UUID

    model_config = ConfigDict(from_attributes = True)