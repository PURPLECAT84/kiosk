from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional
import uuid

class UserCreate(BaseModel):
   
    email : EmailStr
    password : str
    name : str
    phone : str
    address : str
    authority: Optional[str] = "manager" #관리자가 생성하는 경우를 위해. models 의 기본값보다 우선한다

class UserUpdate(BaseModel):
    
    email : Optional[EmailStr] = None
    password : Optional[str] = None
    name : Optional[str] = None
    phone : Optional[str] = None
    address : Optional[str] = None

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

