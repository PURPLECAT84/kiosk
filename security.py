from passlib.context import CryptContext

from datetime import datetime, timedelta, timezone
import jwt

"""=====================여기서 부터 해싱(암호화) 코드============================"""

pwd_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto") #암호화 알고리즘

def get_password_hash(password : str) -> str :
    return pwd_context.hash(password)

def verify_password(original_password : str, hashed_password : str) -> bool:
    return pwd_context.verify(original_password, hashed_password)


"""=====================여기서 부터 토큰 코드(JWT)============================"""

SECRET_KEY = "User_Authority_Key"
ALGORITHM = "HS256" # 암호화 알고리즘
ACCESSABLE_TIME = 30

def create_access_token(data: dict):
    copied_data = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes = ACCESSABLE_TIME)

    copied_data.update({"expired": expire.timestamp()})

    encoded_jwt = jwt.encode(copied_data, SECRET_KEY, algorithm = ALGORITHM)

    return encoded_jwt