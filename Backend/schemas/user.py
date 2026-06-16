from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator, ValidationInfo #EmailStr 을 사용하기 위해선 email-validator 설치 필요
from datetime import datetime
from typing import List
import uuid
import re
from models.user import UserRole, UserStatus

def validate_password_complexity(v: str) -> str:
    if len(v) < 8 or not re.search(r'[A-Za-z]', v) or not re.search(r'\d', v) or not re.search(r'[^A-Za-z0-9\s]', v):
        raise ValueError("비밀번호는 특수문자, 영문, 숫자를 조합하여 입력해주세요.")
    return v

class UserCreate(BaseModel):
    email : EmailStr # 이메일
    password : str # 비밀번호
    name : str # 이름
    phone : str | None = None # 전화번호

    @field_validator("password")
    @classmethod
    def validate_create_password(cls, v: str) -> str:
        return validate_password_complexity(v)

class UserUpdate(BaseModel):
    name: str | None = None # 이름
    phone: str | None = None # 전화번호
    portone_store_id: str | None = None # 점주 개별 포트원 Store ID
    portone_channel_key: str | None = None # 점주 개별 포트원 Channel Key

class UserPasswordUpdate(BaseModel):
    current_password: str = Field(..., description="현재 비밀번호")
    new_password: str = Field(..., min_length=8, description="새 비밀번호")
    new_password_check: str = Field(..., min_length=8, description="새 비밀번호 확인")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        # 복잡도 검사는 new_password에서만 수행
        return validate_password_complexity(v)

    @field_validator("new_password_check")
    @classmethod
    def password_match(cls, v: str, info: ValidationInfo) -> str:
        # new_password가 복잡도 검증을 통과하지 못하면 info.data에 없을 수 있음
        # 이 경우 일치 여부만 확인하면 됨 (복잡도는 new_password에서 이미 처리됨)
        new_pw = info.data.get("new_password")
        if new_pw is not None and v != new_pw:
            raise ValueError("새 비밀번호가 일치하지 않습니다")
        return v
    
class UserDelete(BaseModel):
    password : str # 계정 삭제를 위한 비밀번호 확인

class BusinessInfoResponse(BaseModel):
    id: int
    user_id: uuid.UUID
    business_number: str
    business_name: str
    representative_name: str
    representative_phone: str | None = None
    store_name: str
    document_url: str | None = None
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes = True)

class BusinessInfoCreate(BaseModel):
    business_number: str = Field(..., description="사업자 번호")
    business_name: str = Field(..., description="사업자명")
    representative_name: str = Field(..., description="대표자 이름")
    representative_phone: str | None = Field(None, description="대표자 전화번호")
    store_name: str = Field(..., description="설치매장명")
    document_url: str | None = Field(None, description="사업자등록증 이미지 파일 경로")

    @field_validator("store_name")
    @classmethod
    def validate_store_name(cls, v: str) -> str:
        # 공백 제거
        cleaned = "".join(v.split())
        if not cleaned:
            raise ValueError("설치매장명은 공백일 수 없습니다.")
        return cleaned

class UserResponse(BaseModel):
    id : uuid.UUID # 회원 고유아이디
    email : EmailStr # 이메일
    name : str # 이름
    phone : str | None = None # 전화번호
    role : UserRole # 권한 (DEV, HEAD, MASTER, MANAGER, STAFF)
    status : UserStatus # 상태 (PENDING, ACTIVE, BANNED)
    store_id : uuid.UUID | None = None # 소속 매장아이디
    is_business_verified: bool = False # 사업자 확인여부
    is_identity_verified: bool = False # 본인 확인여부
    created_at : datetime # 가입일, 서버시간 기준
    login_provider: str | None = "email" # 이메일, 카카오, 구글 등 현재 로그인 수단
    businesses: List[BusinessInfoResponse] = [] # 등록된 사업자 목록
    portone_store_id: str | None = None # 점주 개별 포트원 Store ID
    portone_channel_key: str | None = None # 점주 개별 포트원 Channel Key

    model_config = ConfigDict(from_attributes = True) # SQLAlchemy 모델(DB 객체)을 Pydantic 모델로 변환 허용


class UserLogin(BaseModel):
    email : EmailStr # 이메일
    password : str # 비밀번호

class Token(BaseModel):
    access_token : str # 발급된 엑세스 토큰
    token_type : str # 토큰 타입 (예: bearer)

# ======================== 아이디 찾기 ========================
class FindIdRequest(BaseModel):
    name: str = Field(..., description="이름")
    phone: str = Field(..., description="전화번호")

class FindIdResponse(BaseModel):
    masked_email: str  # 마스킹된 이메일 (예: pm*****@naver.com)

# ======================== 비밀번호 재설정 ========================
class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="가입한 이메일")
    name: str = Field(..., description="이름")
    phone: str = Field(..., description="전화번호")

class ResetPasswordResponse(BaseModel):
    temp_password: str  # 화면에 노출할 임시 비밀번호
    message: str
# ======================== 사용자 관리 (어드민용) ========================
# 📝 [초보자를 위한 멘토링 주석]
# 점주들의 전체 현황(매장 정보, 키오스크 수)을 한눈에 볼 수 있도록 어드민 대시보드 전용 데이터 구조(Schema)를 추가 정의합니다.
class UserManagementKioskSummary(BaseModel):
    active_count: int = Field(..., description="활성화(OPERATING) 상태인 키오스크 수")
    inactive_count: int = Field(..., description="미활성화(WAITING 등) 상태인 키오스크 수")

class UserManagementResponse(BaseModel):
    id: uuid.UUID # 점주 고유아이디
    email: EmailStr # 이메일
    name: str # 이름
    phone: str | None = None # 전화번호
    role: UserRole # 권한
    status: UserStatus # 상태
    is_business_verified: bool = False # 사업자 확인여부
    is_identity_verified: bool = False # 본인 확인여부
    created_at: datetime # 가입일
    store_names_summary: str = Field(..., description="소유 매장명 요약 정보 (예: '모키반점 외 2개')")
    kiosks_summary: UserManagementKioskSummary = Field(..., description="운영 중인 키오스크 현황 (활성/미활성 개수)")
    businesses: List[BusinessInfoResponse] = [] # 등록된 사업자 목록
    portone_store_id: str | None = None # 점주 개별 포트원 Store ID
    portone_channel_key: str | None = None # 점주 개별 포트원 Channel Key

    model_config = ConfigDict(from_attributes = True)