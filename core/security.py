# core/security.py
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
from datetime import datetime, timedelta, timezone
import jwt

# 토스페이먼츠 시크릿 키
TOSS_SECRET_KEY = os.getenv("TOSS_SECRET_KEY")

"""===================== 해싱(암호화) 코드 [최신 pwdlib 적용] ============================"""
# 최신 FastAPI 표준 암호화 방식입니다.
password_hash = PasswordHash((BcryptHasher(),))

def get_password_hash(password: str) -> str:
    return password_hash.hash(password)

def verify_password(original_password: str, hashed_password: str) -> bool:
    return password_hash.verify(original_password, hashed_password)


"""===================== 토큰 코드(JWT) ============================"""
SECRET_KEY = os.getenv("SECRET_KEY", "User_Authority_Key") 
ALGORITHM = os.getenv("ALGORITHM", "HS256") 
ACCESSABLE_TIME = int(os.getenv("ACCESSABLE_TIME", "30")) # 토큰 유효 시간(분)

def create_access_token(data: dict):
    copied_data = data.copy()
    
    # 만료 시간 계산
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESSABLE_TIME)
    
    # JWT 표준 'exp' 적용
    copied_data.update({"exp": expire.timestamp()})
    
    # 토큰 암호화(인코딩)
    encoded_jwt = jwt.encode(copied_data, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt



