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
from routers import user, store, shelve, category, product,order, statistics

from fastapi.middleware.cors import CORSMiddleware

import models

Base.metadata.create_all(bind=engine)
#테이블 생성 (앱 시작할 때 DB에 테이블이 없으면 자동으로 만들어줌)


app = FastAPI(title="Kiosk Admin Center", description="키오스크 관리자 페이지", version="1.0.0") 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 주소에서 내 API에 접근하는 것을 허용 (실무에선 특정 도메인만 넣습니다)
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, DELETE 등 모든 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(store.router, prefix="/store", tags=["Stores"])
app.include_router(shelve.router, prefix="/shelves", tags=["Shelves"])
app.include_router(category.router, prefix="/categories", tags=["Categories"])
app.include_router(product.router, prefix="/products", tags=["Products"])
app.include_router(order.router, prefix="/order", tags=["orders"])
app.include_router(statistics.router, prefix="/dashboard", tags=["dashboard"])
#app.include_router(order_item.router, prefix="/order_item", tags=["order_items"])

@app.get("/")
def read_root():
    return{"message" : "Welcome to Kiosk Server"}

