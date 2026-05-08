from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator, ValidationInfo #EmailStr 을 사용하기 위해선 email-validator 설치 필요
from datetime import datetime
import uuid
from models.user import UserRole, UserStatus

class UserCreate(BaseModel):
    email : EmailStr # 이메일
    password : str # 비밀번호
    name : str # 이름
    phone : str | None = None # 전화번호

class UserUpdate(BaseModel):
    name: str | None = None # 이름
    phone: str | None = None # 전화번호

class UserPasswordUpdate(BaseModel):
    current_password: str = Field(...,description="현재 비밀번호")
    new_password : str = Field(..., min_length = 4, description="새 비밀번호")
    new_password_check: str = Field(...,min_length = 4, description="새 비밀번호 확인")

    @field_validator("new_password_check")
    @classmethod
    def password_match(cls, v: str, info: ValidationInfo) -> str:
        # info.data 딕셔너리에 이전에 검증된 필드들이 담겨 있습니다.
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("새 비밀번호가 일치하지 않습니다")
        return v
    
class UserDelete(BaseModel):
    password : str # 계정 삭제를 위한 비밀번호 확인

class UserResponse(BaseModel):
    id : uuid.UUID # 회원 고유아이디
    email : EmailStr # 이메일
    name : str # 이름
    phone : str | None = None # 전화번호
    role : UserRole # 권한 (DEV, HEAD, MASTER, MANAGER, STAFF)
    status : UserStatus # 상태 (PENDING, ACTIVE, BANNED)
    store_id : uuid.UUID | None = None # 소속 매장아이디 (복수가능한 경우도 고려)
    created_at : datetime # 가입일, 서버시간 기준

    model_config = ConfigDict(from_attributes = True) # SQLAlchemy 모델(DB 객체)을 Pydantic 모델로 변환 허용


class UserLogin(BaseModel):
    email : EmailStr # 이메일
    password : str # 비밀번호

class Token(BaseModel):
    access_token : str # 발급된 엑세스 토큰
    token_type : str # 토큰 타입 (예: bearer)