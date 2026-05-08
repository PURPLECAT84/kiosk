from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv
import os

# .env 파일에서 환경 변수를 불러옵니다.
load_dotenv()

DB_URL = os.getenv("DB_URL")

# 1. DB Engine 생성 (DB와의 실제 통신을 담당하는 핵심 객체)
# pool_pre_ping=True: 연결 풀에서 커넥션을 가져오기 전에 "DB 살아있니?" (Ping) 확인. 
# -> 예기치 않게 DB 연결이 끊어졌을 때 발생하는 에러를 방지합니다.
engine = create_engine(DB_URL, pool_pre_ping=True)

# 2. DB Session Factory 생성 (개발자가 DB와 대화하기 위한 창구 생성기)
# - bind=engine: 실제 연결(엔진)을 지정.
# - autocommit=False: "commit()" 명시 전에는 절대 영구 저장하지 않음. (트랜잭션 롤백 대비 안전성)
# - autoflush=False: 매번 쿼리를 보낼 때마다 자동으로 동기화하지 않음. 불필요한 통신을 줄여 성능을 향상시킵니다.
DB_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Base 클래스 (SQLAlchemy 2.0 권장 방식)
# 모든 모델(테이블)은 이 Base 클래스를 상속받아 정의됩니다.
class Base(DeclarativeBase):
    pass

# 4. Dependency Injection용 함수
# API 요청이 들어올 때마다 세션을 하나씩 열어주고, 끝나면 안전하게 닫아줍니다. (with open() 구문과 유사한 역할)
def get_db():
    db = DB_session()
    try:
        yield db
    finally:
        db.close()