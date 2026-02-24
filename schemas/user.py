from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator #EmailStr 을 사용하기 위해선 email-validator 설치 필요
from datetime import datetime
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