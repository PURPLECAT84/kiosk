# core/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
import jwt
from jwt.exceptions import InvalidTokenError

from database import get_db
from models.user import User
from core.security import SECRET_KEY, ALGORITHM

# 🔒 스웨거 자물쇠 생성 (로그인 주소 명시)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> User:
    """
    [보안 문지기] 토큰을 해독하여 정상적인 유저인지 확인하고 정보를 반환합니다.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="로그인 정보를 확인할 수 없습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 토큰 포장지 뜯기
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    # DB에서 유저 조회
    stmt = select(User).where(User.email == email)
    user = db.execute(stmt).scalars().first()

    if user is None:
        raise credentials_exception
    
    return user


