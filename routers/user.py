# routers/user.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from typing import List

from database import get_db
from models.user import User
from schemas.user import UserCreate, UserResponse, Token, UserUpdate, UserPasswordUpdate, UserDelete
from core.security import get_password_hash, verify_password, create_access_token
# 🔥 [핵심] 아까 만든 문지기를 여기서 불러옵니다!
from core.dependency import get_current_user 

router = APIRouter()

"""===================== 토큰 발급 (로그인) ============================"""
@router.post("/login", response_model=Token)
def token_access(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    stmt = select(User).where(User.email == form_data.username)
    user = db.execute(stmt).scalars().first()
   
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="이메일 또는 비밀번호가 일치하지 않습니다", 
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

"""===================== 내 정보 조회 ============================"""
@router.get("/me", response_model=UserResponse, summary="회원검증")
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

"""===================== 회원 가입 ============================"""
@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="회원가입")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    stmt = select(User).where(User.email == user.email)
    if db.execute(stmt).scalars().first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 존재하는 이메일입니다")
    
    user_data = user.model_dump()
    user_data["password"] = get_password_hash(user_data["password"])
    new_user = User(**user_data)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

"""===================== 회원 전체 조회 ============================"""
@router.get("/", response_model=List[UserResponse], summary="회원조회")
async def read_user(
    skip: int = 0, limit: int = 10, 
    name: str | None = None, email: str | None = None,
    current_user: User = Depends(get_current_user), # 🔒 권한 검사
    db: Session = Depends(get_db)
):
    if current_user.authority not in ["master", "dev"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="회원조회 권한이 없습니다")

    stmt = select(User)
    if name: 
        stmt = stmt.where(User.name.contains(name))
    if email: 
        stmt = stmt.where(User.email.contains(email))
    
    stmt = stmt.offset(skip).limit(limit)
    return db.execute(stmt).scalars().all()

"""===================== 내 정보 수정 ============================"""
@router.patch("/me", response_model=UserResponse, summary="내 정보 수정")
async def update_user_profile(
    body: UserUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user) # 🔒 권한 검사
):
    if body.name: current_user.name = body.name
    if body.phone: current_user.phone = body.phone
    if body.address: current_user.address = body.address 

    db.commit()
    db.refresh(current_user)
    return current_user

"""===================== 비밀번호 수정 ============================"""
@router.patch("/me/password", summary="비밀번호 변경")
async def update_password(
    body: UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # 🔒 권한 검사
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
    current_user: User = Depends(get_current_user) # 🔒 권한 검사
):
    if not verify_password(confirm.password, current_user.password):
          raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="비밀번호가 일치하지 않습니다")
      
    db.delete(current_user)
    db.commit()
    return None