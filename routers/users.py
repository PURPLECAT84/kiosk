from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from database import get_db
from models import User
from schemas import UserCreate, UserResponse, UserLogin, Token
from security import get_password_hash, verify_password, create_access_token, ALGORITHM, SECRET_KEY
from typing import List
import jwt
from jwt.exceptions import InvalidTokenError

"""=====================여기서 부터 해싱(암호화) 코드============================"""


router = APIRouter(prefix = "/users", tags = ["users"])


"""=====================여기서 부터 토큰 코드(JWT)============================"""

@router.post("/login",response_model = Token)
def token_access(form_data : OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    stmt = select(User).where(User.email == form_data.username)
    user = db.execute(stmt).scalars().first()

   
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, 
                            detail = "이메일 또는 비밀번호가 일치하지 않습니다", 
                            headers={"WWW-Authenticate": "Bearer"}) #???
    
    access_token = create_access_token(data = {"sub": user.email})

    return {"access_token" : access_token, "token_type" : "bearer"} #???

"""=====================여기서 부터 토큰 검증 및 조회============================"""

oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "/users/login")

def get_current_user(token : str = Depends(oauth2_scheme), db : Session = Depends(get_db)) ->User:

    credentials_exception = HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "로그인 정보를 확인할 수 없습니다",
                                          headers = {"WWW-Authenticate" : "Bearer"},)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms = [ALGORITHM]) # 토큰 해독 (Decode) # SECRET_KEY로 서명을 확인하고, 만료 시간(exp)도 자동으로 체크

        email : str | None = payload.get("sub")

        if email is None:
            raise credentials_exception
        
    except InvalidTokenError :
        credentials_exception

    stmt = select(User).where(User.email == email)
    user = db.execute(stmt).scalars().first()

    if user is None :
        raise credentials_exception
    
    return user

@router.get ("/me", response_model = UserResponse, summary = "회원검증")

def read_users_me(current_user : User = Depends(get_current_user)):
    
    return current_user

"""=====================여기서 부터 회원 가입 및 조회============================"""


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

@router.get("/",response_model=List[UserResponse], summary = "회원조회",description= "전체 회원 조회")
async def read_user(skip: int = 0, limit : int = 10, 
                     name : str | None = None, 
                     email : str | None = None,
                     current_user: User = Depends(get_current_user),
                     db : Session = Depends(get_db)):
    
    stmt = select(User) #일단 "모든 회원 리스트를 가져와라"

    if current_user.authority not in ["master", "dev"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail= "회원조회 권한이 없습니다")

    if name : 
      
        stmt = stmt.where(User.name.contains(name)) #[검색 로직] 만약(if) 사용자가 검색어(name)를 보냈다면

    if name : 
      
        stmt = stmt.where(User.email.contains(email)) #[검색 로직] 만약(if) 사용자가 검색어(name)를 보냈다면
    

    stmt = stmt.offset(skip).limit(limit) #페이징(자르기) 적용

    users = db.execute(stmt).scalars().all()#실행

    return users


