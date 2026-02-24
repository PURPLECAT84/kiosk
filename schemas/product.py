from pydantic import BaseModel,ConfigDict
from datetime import datetime
import uuid


class ProductCreate(BaseModel):

    category_id : int
    barcode : str | None = None
    name : str
    price : int
    buy_from : str | None = None
    image : str

class ProductUpdate(BaseModel):

    barcode : str | None = None
    name : str | None = None
    price : int | None = None
    buy_from : str | None = None
    image : str | None = None

class ProductResponse(BaseModel):

    id : uuid.UUID
    store_id : uuid.UUID
    shelve_id : uuid.UUID
    category_id : int
    barcode : str | None = None
    name : str
    price : int
    buy_from : str | None = None
    created_date :datetime
    image : str

    model_config = ConfigDict(from_attributes = True)