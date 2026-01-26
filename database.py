from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DB_URL = "postgresql://postgres.wmrnknlikvcohczmyvpb:PGHwIpn08gBh9gi8@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
# supabase 비번 : PGHwIpn08gBh9gi8

engine = create_engine(DB_URL, pool_pre_ping = True)
#pool_pre_ping = True : DB 와의 연결 전 매번 연결 상태 체크 실행

DB_session = sessionmaker(autocommit = False, autoflush = False, bind = engine)

"""
bind = engine <- 세션과 DB 주소가 있는 engine 연결
autocommit <-commit()이라고 말하기 전까지는 절대 DB에 영구 저장하지 마!, True 는 자동저장
autoflush <- 자동 명령 전송 끄기, 불필요한 DB 전송 및 액션 감소, 성능 향상
"""

class Base(DeclarativeBase):
    pass


def get_db():
    db = DB_session()
    try:
        yield db
    finally:
        db.close()