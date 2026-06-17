from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import UserInfo
from core.dependency import get_current_user
from pydantic import BaseModel, Field, EmailStr
import uuid
import hashlib
from typing import Dict, Any

router = APIRouter(
    prefix="/auth",
    tags=["Identity Verification (본인인증)"]
)

# 인메모리 임시 대기열 (본인인증 발송 요청 임시 저장)
# 실제 포트원 연동 시에는 포트원 API 서버가 세션을 가지지만, 개발 샌드박스 검증을 위해 로컬 메모리를 활용합니다.
pending_verifications: Dict[str, Dict[str, Any]] = {}

class IdentitySendRequest(BaseModel):
    name: str = Field(..., description="고객 실명")
    phone: str = Field(..., description="휴대폰 번호 (예: 010-1234-5678 또는 01012345678)")
    operator: str = Field(..., description="통신사 (SKT, KT, LGU, SKT_MVNO, KT_MVNO, LGU_MVNO 등)")
    birth_date: str = Field(..., description="생년월일 8자리 (예: 19900101)")
    gender: str = Field(..., description="성별 (MALE / FEMALE)")

class IdentitySendResponse(BaseModel):
    success: bool
    verification_id: str
    message: str

class IdentityConfirmRequest(BaseModel):
    verification_id: str = Field(..., description="인증 요청 고유 ID")
    otp: str = Field(..., description="SMS로 수신된 6자리 인증번호")

class IdentityConfirmResponse(BaseModel):
    success: bool
    name: str
    phone: str
    message: str

@router.post("/identity-verification/send", response_model=IdentitySendResponse, summary="인라인 SMS 본인인증 요청 발송")
async def send_identity_verification(
    request: IdentitySendRequest,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    통신사 본인확인 SMS 인증문자를 발송합니다.
    샌드박스 모드에서는 성공 응답과 가상의 verification_id(UUID)를 반환하며, 6자리 인증번호 OTP 입력 대기 상태로 진입합니다.
    """
    try:
        # [모킹 동작]
        # 0. 회원가입 시 입력한 실명 및 전화번호 일치 검증
        # 📝 [초보자를 위한 멘토링 주석]
        # 타인의 명의로 불법 본인인증을 시도하는 것을 막기 위해,
        # 회원가입 시 등록된 이름/전화번호가 본인인증 시 입력한 값과 일치하는지 비교합니다.
        clean_user_phone = "".join(c for c in current_user.phone if c.isdigit())
        clean_req_phone = "".join(c for c in request.phone if c.isdigit())
        
        if current_user.name != request.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="가입된 회원명과 본인인증 이름이 일치하지 않습니다."
            )
            
        if clean_user_phone != clean_req_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="가입된 전화번호와 본인인증 전화번호가 일치하지 않습니다."
            )

        # 전화번호 포맷 정규화
        clean_phone = clean_req_phone
        if len(clean_phone) < 10 or len(clean_phone) > 11:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="올바르지 않은 휴대폰 번호 형식입니다."
            )
            
        # 생년월일 포맷 확인
        if len(request.birth_date) != 8 or not request.birth_date.isdigit():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="생년월일은 YYYYMMDD 형태의 8자리 숫자로 입력해야 합니다."
            )

        # 가상의 본인인증 거래ID(UUID) 생성
        verification_id = f"cert-{uuid.uuid4()}"
        
        # 인메모리에 본인인증 요청 내역 보관
        pending_verifications[verification_id] = {
            "name": request.name,
            "phone": f"{clean_phone[:3]}-{clean_phone[3:-4]}-{clean_phone[-4:]}",
            "operator": request.operator,
            "birth_date": request.birth_date,
            "gender": request.gender
        }
        
        return IdentitySendResponse(
            success=True,
            verification_id=verification_id,
            message="입력하신 번호로 본인확인 인증 문자가 발송되었습니다. (테스트 모드: 아무 번호나 6자리 입력하여 승인 가능)"
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"본인인증 발송 처리 중 오류 발생: {str(e)}"
        )

@router.post("/identity-verification/confirm", response_model=IdentityConfirmResponse, summary="인라인 SMS 본인인증 완료 처리")
async def confirm_identity_verification(
    request: IdentityConfirmRequest,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    점주가 입력한 6자리 OTP 인증번호를 검증하여 실명 본인인증을 완료합니다.
    테스트 모드에서는 6자리 숫자이기만 하면 통과 처리되어 계정이 정식 활성화됩니다.
    """
    verification_id = request.verification_id
    
    if verification_id not in pending_verifications:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="만료되었거나 존재하지 않는 본인인증 요청입니다. 인증번호를 다시 요청해주세요."
        )
        
    # OTP 검증 (6자리 숫자 여부 검증)
    if not request.otp.isdigit() or len(request.otp) != 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="인증번호는 6자리 숫자여야 합니다."
        )
        
    try:
        cert_data = pending_verifications.pop(verification_id)
        
        # 중복가입 방지 고유키(CI/DI) 생성 (실명+전화번호 기반 해시)
        hashed_ci = hashlib.sha256(f"MOCK_CI_{cert_data['name']}_{cert_data['phone']}".encode()).hexdigest()
        hashed_di = hashlib.sha256(f"MOCK_DI_{cert_data['name']}_{cert_data['phone']}".encode()).hexdigest()
        
        # 1. 이미 동일 명의(CI)로 등록된 타 계정이 존재하는지 조회
        from sqlalchemy import select
        duplicate_check = db.execute(
            select(UserInfo).where(UserInfo.ci == hashed_ci, UserInfo.id != current_user.id)
        ).scalars().first()
        
        if duplicate_check:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 해당 명의로 가입되어 인증된 다른 계정이 존재합니다."
            )
            
        # 2. 본인인증 정보 및 전화번호 실명 동기화 적재
        current_user.is_identity_verified = True
        current_user.ci = hashed_ci
        current_user.di = hashed_di
        current_user.name = cert_data["name"]
        current_user.phone = cert_data["phone"]
        
        db.commit()
        db.refresh(current_user)
        
        return IdentityConfirmResponse(
            success=True,
            name=current_user.name,
            phone=current_user.phone,
            message="통신사 실명 본인인증이 완료되었습니다. 기기 개통 및 관리가 활성화됩니다."
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"본인인증 승인 처리 중 오류 발생: {str(e)}"
        )
