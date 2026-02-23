from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator #EmailStr 을 사용하기 위해선 email-validator 설치 필요
from datetime import datetime
from typing import Optional
import uuid

class UserCreate(BaseModel):
   
    email : EmailStr
    password : str
    name : str
    phone : str
    address : str
    #authority: Optional[str] = "manager" #관리자가 생성하는 경우를 위해. models 의 기본값보다 우선한다. <- 인위적으로 넣으면 안되므로 삭제. 어차피 models 에 있음

class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    address: str | None = None

class UserPasswordUpdate(BaseModel):
    current_password: str = Field(...,description="현재 비밀번호")
    new_password : str = Field(..., min_length = 4, description="새 비밀번호")
    new_password_check: str = Field(...,min_length = 4, description="새 비밀번호 확인")

    @field_validator("new_password_check")
    def password_match(cls, v, values):
        if "new_password" in values.data and v != values.data["new_password"]:
            raise ValueError("새 비밀번호가 일치하지 않습니다")
            
        return v
    
class UserDelete(BaseModel):
    password : str


class UserResponse(BaseModel):
    
    id : uuid.UUID
    email : EmailStr
    name : str
    phone : str
    address : str
    authority : str
    joined_date : datetime

    model_config = ConfigDict(from_attributes = True) # SQLAlchemy 모델(DB 객체)을 Pydantic 모델로 변환 허용


class UserLogin(BaseModel):

    email : EmailStr
    password :str

class Token(BaseModel):

    access_token : str
    token_type : str

"""============여기부터 매장-매대-카테고리-상품 관련 스키마=============="""


class StoreCreate(BaseModel):

    name : str
    address : str
    type : str | None = None
    user_email : EmailStr



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
