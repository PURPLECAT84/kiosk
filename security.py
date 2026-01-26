from passlib.context import CryptContext

pwd_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto") #암호화 알고리즘

def get_password_hash(password : str) -> str :
    return pwd_context.hash(password)

def verify_password(original_password : str, hashed_password : str) -> bool:
    return pwd_context.verify(original_password, hashed_password)