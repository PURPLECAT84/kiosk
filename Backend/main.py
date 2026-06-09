#version.1.0.0

"""
[라이브러리 설명]
**"보안(Security)"**과 "인증(Auth)" 기능을 만들 때 없어서는 안 될 3대장

1. passlib[bcrypt] : 🔒 비밀번호 금고지기
   - 역할: 비밀번호 해싱(Hashing) 라이브러리
   - 비유: "문서 파쇄기 + 금고"

2. python-jose : 🆔 출입증 발급기
   - 역할: JWT(JSON Web Token) 생성 및 관리 라이브러리
   - 비유: "위조 방지 도장이 찍힌 사원증 발급 기계"

3. python-multipart : 📦 택배 상자 번역기
   - 역할: Form Data 파싱(해석) 라이브러리
   - 비유: "폼(Form) 언어 통역사"
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import engine, Base
import models
from routers import user, store, kiosk, kiosk_client, shelve, category, product, order, statistics, social_login

# 1. DB 테이블 자동 생성
# 앱이 시작될 때 models에 정의된 스키마를 바탕으로 DB에 테이블이 없으면 자동으로 생성해줍니다.
# 주의: Alembic 같은 마이그레이션 툴을 쓸 때는 이 기능을 끄는 것이 좋습니다. (현재는 개발 편의를 위해 유지)
Base.metadata.create_all(bind=engine)

# 1-2. 초기 연동 더미 데이터 시딩 (Seeding)
# 완전 초보자들의 실시간 연동 테스트를 위해, 고정된 UUID의 매장과 키오스크 및 메뉴들을 자동으로 삽입합니다.
from database import DB_session
from core.seeder import seed_initial_data
db_session = DB_session()
try:
    seed_initial_data(db_session)
finally:
    db_session.close()

# 2. 정적 파일 디렉토리 보장
# 사용자가 업로드할 이미지가 저장될 기본 폴더를 만듭니다.
os.makedirs("static/images", exist_ok=True)

# 3. FastAPI 앱 인스턴스 생성
app = FastAPI(title="Kiosk Admin Center", description="키오스크 관리자 페이지 및 백엔드 API", version="1.0.0") 

# 4. CORS 미들웨어 설정
# 프론트엔드(React, Flutter 등)에서 백엔드 API를 호출할 수 있도록 허용하는 보안 정책입니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용으로 모두 오픈 (*). 실무에서는 ["http://localhost:5173", "https://mydomain.com"] 처럼 특정 도메인만 허용해야 합니다.
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE 등 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# 5. 정적 파일(Static Files) 서빙 세팅
# 5-1. 백엔드 자체 정적 파일 (예: 업로드된 이미지)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 5-2. 파트너센터 React 빌드 파일 서빙 (../Partnercenter/dist 폴더 기준)
partner_ui_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../Partnercenter/dist"))
if os.path.exists(partner_ui_dir):
    assets_path = os.path.join(partner_ui_dir, "assets")
    
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="partner_assets")

# 6. 라우터 연결 (API 엔드포인트 모듈화)
# app.include_router()를 통해 기능별로 분리된 파일들을 하나의 앱으로 합쳐줍니다.
app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(store.router, prefix="/store", tags=["Stores"])
app.include_router(kiosk.router, prefix="/kiosks", tags=["Kiosks"])
app.include_router(kiosk_client.router, prefix="/kiosk_client", tags=["Kiosk Client"])
app.include_router(shelve.router, prefix="/shelves", tags=["Shelves"])
app.include_router(category.router, prefix="/categories", tags=["Categories"])
app.include_router(product.router, prefix="/products", tags=["Products"])
app.include_router(order.router, prefix="/order", tags=["Orders"])
app.include_router(statistics.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(social_login.auth_router) # prefix와 tags는 라우터 내부에서 정의됨

# 7. 루트 경로 처리 (프론트엔드 HTML 반환)
@app.get("/")
def read_root():
    if os.path.exists(partner_ui_dir):
        index_path = os.path.join(partner_ui_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
    return {"message": "Welcome to MOKI Backend API. (Partner UI is not built or not found)"}



