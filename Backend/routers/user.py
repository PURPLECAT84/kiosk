# routers/user.py
import secrets
import string
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from typing import List

from database import get_db
from models.user import UserInfo, UserRole
from schemas.user import (UserCreate, UserResponse, Token, UserUpdate, 
                          UserPasswordUpdate, UserDelete,
                          FindIdRequest, FindIdResponse,
                          ResetPasswordRequest, ResetPasswordResponse,
                          UserManagementResponse)
from core.security import get_password_hash, verify_password, create_access_token
# 🔥 [핵심] 아까 만든 문지기를 여기서 불러옵니다!
from core.dependency import get_current_user 

router = APIRouter()

"""===================== 토큰 발급 (로그인) ============================"""
@router.post("/login", response_model=Token)
def token_access(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    stmt = select(UserInfo).where(UserInfo.email == form_data.username)
    user = db.execute(stmt).scalars().first()
   
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="이메일 또는 비밀번호가 일치하지 않습니다", 
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    access_token = create_access_token(data={"sub": user.email, "provider": "email"})
    return {"access_token": access_token, "token_type": "bearer"}

"""===================== 내 정보 조회 ============================"""
@router.get("/me", response_model=UserResponse, summary="회원검증")
def read_users_me(current_user: UserInfo = Depends(get_current_user)):
    return current_user

"""===================== 회원 가입 ============================"""
@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="회원가입")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    stmt = select(UserInfo).where(UserInfo.email == user.email)
    if db.execute(stmt).scalars().first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 존재하는 이메일입니다")
    
    user_data = user.model_dump()
    user_data["password"] = get_password_hash(user_data["password"])
    new_user = UserInfo(**user_data)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

"""===================== 회원 전체 조회 (어드민용 고도화) ============================"""
@router.get("/", response_model=List[UserManagementResponse], summary="회원조회")
async def read_user(
    skip: int = 0, limit: int = 100, 
    name: str | None = None, email: str | None = None,
    current_user: UserInfo = Depends(get_current_user), # 🔒 권한 검사
    db: Session = Depends(get_db)
):
    # 📝 [초보자를 위한 멘토링 주석]
    # 어드민 전용 회원 목록 조회입니다. 보안을 위해 MASTER, DEV, HEAD 권한의 관리자만 접근 가능합니다.
    if current_user.role not in [UserRole.MASTER, UserRole.DEV, UserRole.HEAD]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="회원조회 권한이 없습니다")

    # 1. 필터 조건에 따라 회원 리스트 조회
    stmt = select(UserInfo)
    if name: 
        stmt = stmt.where(UserInfo.name.contains(name))
    if email: 
        stmt = stmt.where(UserInfo.email.contains(email))
    
    stmt = stmt.offset(skip).limit(limit)
    users = db.execute(stmt).scalars().all()

    # 2. 조회된 유저들에 대해 매장명 요약 및 키오스크 수 통계 조립
    from models.store import Store
    from models.kiosk import Kiosk
    
    response_data = []
    for user in users:
        # 각 점주가 만든 매장 목록을 생성일자 순으로 조회합니다.
        store_stmt = select(Store).where(Store.user_id == user.id).order_by(Store.created_at.asc())
        stores = db.execute(store_stmt).scalars().all()
        
        # 매장 요약 정보 조립
        if not stores:
            store_names_summary = "매장 없음"
        elif len(stores) == 1:
            store_names_summary = stores[0].name
        else:
            # 복수 매장일 경우: 가장 처음 만든 매장명 외 00개 로 표기
            store_names_summary = f"{stores[0].name} 외 {len(stores) - 1}개"
            
        # 각 점주가 가진 모든 매장의 키오스크 상태 집계
        active_kiosks = 0
        inactive_kiosks = 0
        if stores:
            store_ids = [s.id for s in stores]
            kiosk_stmt = select(Kiosk).where(Kiosk.store_id.in_(store_ids))
            kiosks = db.execute(kiosk_stmt).scalars().all()
            for k in kiosks:
                if k.status == "OPERATING":
                    active_kiosks += 1
                else:
                    inactive_kiosks += 1
                    
        # 응답 객체 구성
        response_data.append(UserManagementResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            phone=user.phone,
            role=user.role,
            status=user.status,
            created_at=user.created_at,
            store_names_summary=store_names_summary,
            kiosks_summary={
                "active_count": active_kiosks,
                "inactive_count": inactive_kiosks
            }
        ))
        
    return response_data

"""===================== 내 정보 수정 ============================"""
@router.patch("/me", response_model=UserResponse, summary="내 정보 수정")
async def update_user_profile(
    body: UserUpdate, 
    db: Session = Depends(get_db), 
    current_user: UserInfo = Depends(get_current_user) # 🔒 권한 검사
):
    if body.name: current_user.name = body.name
    if body.phone: current_user.phone = body.phone

    db.commit()
    db.refresh(current_user)
    return current_user

"""===================== 비밀번호 수정 ============================"""
@router.patch("/me/password", summary="비밀번호 변경")
async def update_password(
    body: UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user) # 🔒 권한 검사
):
    if not verify_password(body.current_password, current_user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="현재 비밀번호가 일치하지 않습니다")
    if body.current_password == body.new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="새 비밀번호는 기존 비밀번호와 달라야 합니다")
    if body.new_password != body.new_password_check:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="새 비밀번호 확인과 일치하지 않습니다")
    
    current_user.password = get_password_hash(body.new_password)
    db.commit()
    db.refresh(current_user)
    return {"message": "비밀번호가 성공적으로 변경되었습니다."}

"""===================== 회원 탈퇴 ============================"""
@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT, summary="회원 탈퇴")
async def delete_user(
    confirm: UserDelete,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user) # 🔒 권한 검사
):
    if not verify_password(confirm.password, current_user.password):
          raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="비밀번호가 일치하지 않습니다")
      
    db.delete(current_user)
    db.commit()
    return None

"""===================== 아이디 찾기 ========================"""
@router.post("/find-id", response_model=FindIdResponse, summary="아이디(이메일) 찾기")
async def find_user_id(body: FindIdRequest, db: Session = Depends(get_db)):
    """
    이름과 전화번호가 DB에 등록된 정보와 일치하면, 
    이메일 앞 2자만 남기고 마스킹하여 반환합니다.
    예) pmountain@naver.com → pm*******@naver.com
    """
    stmt = select(UserInfo).where(UserInfo.name == body.name, UserInfo.phone == body.phone)
    user = db.execute(stmt).scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="입력하신 정보와 일치하는 계정이 없습니다."
        )
    
    # 이메일 마스킹 처리
    email = user.email
    local, domain = email.split("@")
    # 앞 2자리만 공개, 나머지는 * 처리
    visible = local[:2]
    masked = visible + ("*" * (len(local) - 2))
    masked_email = f"{masked}@{domain}"

    return FindIdResponse(masked_email=masked_email)


"""===================== 비밀번호 초기화 ========================"""
@router.post("/reset-password", response_model=ResetPasswordResponse, summary="비밀번호 초기화 (임시 비밀번호 발급)")
async def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    이메일, 이름, 전화번호 3가지가 모두 일치하면 랜덤 임시 비밀번호를 생성하여 
    DB를 업데이트하고 화면으로 반환합니다.
    (상용화 버전에서는 화면 노출 대신 해당 이메일로 발송하도록 업그레이드 예정)
    """
    stmt = select(UserInfo).where(
        UserInfo.email == body.email,
        UserInfo.name == body.name,
        UserInfo.phone == body.phone
    )
    user = db.execute(stmt).scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="입력하신 이메일, 이름, 전화번호 정보가 일치하지 않습니다."
        )

    # 소셜 로그인 전용 계정 예외 처리
    if user.password == "SOCIAL_LOGIN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="소셜 로그인(카카오/구글) 연동 계정은 비밀번호 재설정이 불가합니다."
        )
    
    # 임시 비밀번호 생성: 영문(대소) + 숫자 + 특수문자 조합, 12자리
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    temp_password = (
        secrets.choice(string.ascii_uppercase) +
        secrets.choice(string.ascii_lowercase) +
        secrets.choice(string.digits) +
        secrets.choice("!@#$%") +
        "".join(secrets.choice(alphabet) for _ in range(8))
    )
    # 순서 무작위 섞기
    temp_list = list(temp_password)
    secrets.SystemRandom().shuffle(temp_list)
    temp_password = "".join(temp_list)

    # DB 업데이트
    user.password = get_password_hash(temp_password)
    db.commit()
    
    return ResetPasswordResponse(
        temp_password=temp_password,
        message="임시 비밀번호가 발급되었습니다. 로그인 후 반드시 비밀번호를 변경해 주세요."
    )