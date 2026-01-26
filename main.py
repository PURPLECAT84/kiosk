"""
[라이브러리 설명]

**"보안(Security)"**과 "인증(Auth)" 기능을 만들 때 없어서는 안 될 3대장

1. passlib[bcrypt] : 🔒 비밀번호 금고지기

역할: 비밀번호 해싱(Hashing) 라이브러리
비유: "문서 파쇄기 + 금고"


2. python-jose : 🆔 출입증 발급기
역할: JWT(JSON Web Token) 생성 및 관리 라이브러리
비유: "위조 방지 도장이 찍힌 사원증 발급 기계"

3. python-multipart : 📦 택배 상자 번역기
역할: Form Data 파싱(해석) 라이브러리
비유: "폼(Form) 언어 통역사"
OAuth2PasswordRequestForm을 사용하려면 이 라이브러리가 필수
"""


from fastapi import FastAPI
from database import engine, Base
from routers import users

Base.metadata.create_all(bind=engine)
#테이블 생성 (앱 시작할 때 DB에 테이블이 없으면 자동으로 만들어줌)

app = FastAPI() 

app.include_router(users.router)

@app.get("/")
def read_root():
    return{"message" : "Welcome to Kiosk Server"}

