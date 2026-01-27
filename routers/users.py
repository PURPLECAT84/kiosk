from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import UserCreate, UserResponse, UserLogin, Token
from security import get_password_hash, verify_password, create_access_token

"""=====================여기서 부터 해싱(암호화) 코드(JWT)============================"""


router = APIRouter(prefix = "/users", tags = ["users"])

@router.post("/signup", response_model = UserResponse, status_code = status. HTTP_201_CREATED, summary = "회원가입", description = "회원 정보 입력")
def create_user(user : UserCreate, db : Session = Depends(get_db)):
    stmt = select(User).where(User.email == user.email) #???
    existing_user = db.execute(stmt).scalars().first() #???

    if existing_user:
        raise HTTPException(status_code = status.HTTP_409_CONFLICT, detail = "이미 존재하는 이메일입니다")
    
    user_data = user.model_dump()
     # user.model_dump(): Pydantic 데이터를 딕셔너리로 변환

    hashed_data = get_password_hash(user_data["password"])
    user_data["password"] = hashed_data
    new_user = User(**user_data)
    #위에 세줄 로직 파악 중요
   
    # **: 딕셔너리 압축 풀기 (email=..., name=... 등을 자동으로 넣어줌)

    db.add(new_user) # 장바구니 담기
    db.commit() # 결제 (저장)
    db.refresh(new_user)# DB에서 생성된 ID, 가입일 등을 다시 가져옴

    return new_user

"""=====================여기서 부터 토큰 코드(JWT)============================"""

@router.post("/login",response_model = Token)
def token_access(user_login : UserLogin, db: Session = Depends(get_db)):
    stmt = select(User).where(User.email == user_login.email)
    user = db.execute(stmt).scalars().first()

    if not user or not verify_password(user_login.password, user.password):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, 
                            detail = "이메일 또는 비밀번호가 일치하지 않습니다", 
                            headers={"WWW-Authenticate": "Bearer"}) #???
    
    access_token = create_access_token(data = {"sub": user.email})

    return {"access_token" : access_token, "token_type" : "bearer"} #???